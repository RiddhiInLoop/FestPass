import mysql.connector
from mysql.connector import Error
from PIL import Image, ImageDraw, ImageFont
import qrcode
import barcode
from barcode.writer import ImageWriter
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
import io
import uuid
import os
import logging
from typing import Optional, Tuple, Dict, Any, List
from dotenv import load_dotenv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

# --- CONFIGURATION (Environment Variables) ---
load_dotenv()

# Setup Logging
logger = logging.getLogger("FestPass")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("festpass.log")
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

DB_CONFIG: Dict[str, Any] = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 3306)),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""), 
    "database": os.environ.get("DB_NAME", "festpass_db")
}

EMAIL_SENDER: str = os.environ.get("EMAIL_SENDER", "")
EMAIL_PASSWORD: str = os.environ.get("EMAIL_PASSWORD", "")
ADMIN_PASSWORD: str = os.environ.get("ADMIN_PASSWORD", "admin123")

THEMES: Dict[str, Dict[str, str]] = {
    "Tech":     {"header": "#0D1B2A", "accent": "#00B4D8"},
    "Cultural": {"header": "#6A0572", "accent": "#FFB703"},
    "Sports":   {"header": "#1B4332", "accent": "#F4A261"},
    "VIP":      {"header": "#1A1A2E", "accent": "#FFD700"},
}

# --- DATABASE OPERATIONS ---

def get_db_connection(include_db: bool = True) -> Optional[mysql.connector.connection.MySQLConnection]:
    """Establishes and returns a MySQL database connection based on DB_CONFIG."""
    try:
        if include_db:
            return mysql.connector.connect(**DB_CONFIG)
        else:
            conf = DB_CONFIG.copy()
            conf.pop("database", None)
            return mysql.connector.connect(**conf)
    except Error as e:
        logger.error(f"Error connecting to MySQL: {e}")
        return None

def init_db() -> None:
    """Initializes the database schema and creates necessary tables and columns."""
    conn = get_db_connection(include_db=False)
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
            conn.commit()
        except Error as e:
            logger.error(f"Error creating DB: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    conn = get_db_connection(include_db=True)
    if conn:
        try:
            cursor = conn.cursor()
            # Create main table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tickets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    ticket_id VARCHAR(8) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    dept VARCHAR(255) NOT NULL,
                    event VARCHAR(255) NOT NULL,
                    seat VARCHAR(255) NOT NULL,
                    email VARCHAR(255),
                    scanned TINYINT(1) DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Use try-except to handle ALTER TABLE for existing DBs safely
            try:
                cursor.execute("ALTER TABLE tickets ADD COLUMN scanned_at DATETIME DEFAULT NULL")
            except Error:
                pass
                
            try:
                cursor.execute("ALTER TABLE tickets ADD COLUMN roll_no VARCHAR(50)")
            except Error:
                pass
                
            try:
                cursor.execute("ALTER TABLE tickets ADD COLUMN email_verified TINYINT(1) DEFAULT 0")
            except Error:
                pass

            # Truncate and apply UNIQUE constraint for roll_no and event
            try:
                # We need to wipe existing to apply the strict unique constraint per user request
                cursor.execute("TRUNCATE TABLE tickets")
                cursor.execute("ALTER TABLE tickets ADD CONSTRAINT unique_roll_event UNIQUE(roll_no, event)")
            except Error as e:
                logger.warning(f"Note on unique constraint (it may already exist): {e}")

            try:
                cursor.execute("CREATE INDEX idx_event ON tickets (event)")
            except Error:
                pass
            try:
                cursor.execute("CREATE INDEX idx_scanned ON tickets (scanned)")
            except Error:
                pass

            conn.commit()
            logger.info("Database initialized successfully.")
        except Error as e:
            logger.error(f"Error creating table: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

def save_ticket(ticket_id: str, name: str, dept: str, event: str, seat: str, email: str, roll_no: str, email_verified: bool = False) -> None:
    """Saves a newly generated ticket to the database."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            sql = "INSERT INTO tickets (ticket_id, name, dept, event, seat, email, roll_no, email_verified) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            val = (ticket_id, name, dept, event, seat, email, roll_no, 1 if email_verified else 0)
            cursor.execute(sql, val)
            conn.commit()
            logger.info(f"Ticket {ticket_id} saved for {name}.")
        except Error as e:
            logger.error(f"Error saving ticket: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

def is_duplicate(email: str, event: str) -> bool:
    """Checks if the email has already generated a ticket for the event."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM tickets WHERE email = %s AND event = %s LIMIT 1", (email, event))
            return cursor.fetchone() is not None
        except Error as e:
            logger.error(f"Error checking duplicate email: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    return False

def is_roll_duplicate(roll_no: str, event: str) -> bool:
    """Checks if the roll number has already generated a ticket for the event."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM tickets WHERE roll_no = %s AND event = %s LIMIT 1", (roll_no, event))
            return cursor.fetchone() is not None
        except Error as e:
            logger.error(f"Error checking duplicate roll no: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    return False

def scan_ticket(ticket_id: str) -> str:
    """Scans a ticket by checking its status and updating it if valid."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM tickets WHERE ticket_id = %s", (ticket_id,))
            record = cursor.fetchone()
            if not record:
                return "❌ Invalid Ticket"
            
            if record['scanned'] == 1:
                return "❌ Already Used"
            else:
                cursor.execute("UPDATE tickets SET scanned = 1, scanned_at = CURRENT_TIMESTAMP WHERE ticket_id = %s", (ticket_id,))
                conn.commit()
                logger.info(f"Ticket {ticket_id} scanned successfully.")
                return "✅ Entry Allowed"
        except Error as e:
            logger.error(f"Error scanning ticket: {e}")
            return "❌ Error checking ticket"
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    return "❌ Database Error"

def get_all_tickets() -> List[Dict[str, Any]]:
    """Retrieves all tickets for the admin panel."""
    conn = get_db_connection()
    tickets = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM tickets ORDER BY created_at DESC")
            tickets = cursor.fetchall()
            # Handle unread bytes returned by some mysql configurations
            for ticket in tickets:
               if ticket['scanned_at']:
                   ticket['scanned_at'] = str(ticket['scanned_at'])
               ticket['created_at'] = str(ticket['created_at'])
        except Error as e:
            logger.error(f"Error fetching tickets: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    return tickets

def get_ticket_stats() -> Dict[str, Any]:
    """Retrieves statistics for the dashboard charts."""
    conn = get_db_connection()
    stats = {"scanned": 0, "pending": 0, "events": {}}
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Scanned vs Pending
            cursor.execute("SELECT scanned, COUNT(*) as count FROM tickets GROUP BY scanned")
            for row in cursor.fetchall():
                if row['scanned'] == 1:
                    stats['scanned'] = row['count']
                else:
                    stats['pending'] = row['count']
                    
            # Per event
            cursor.execute("SELECT event, COUNT(*) as count FROM tickets GROUP BY event")
            for row in cursor.fetchall():
                stats['events'][row['event']] = row['count']

        except Error as e:
            logger.error(f"Error fetching stats: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    return stats

# --- PASS GENERATION ---

def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Loads Arial font or default font if Arial is not found."""
    try:
        if bold:
            return ImageFont.truetype("arialbd.ttf", size)
        return ImageFont.truetype("arial.ttf", size)
    except IOError:
        return ImageFont.load_default()

def generate_pass_image(name: str, dept: str, event: str, seat: str, email: str, roll_no: str, theme_name: str, email_verified: bool = False, photo_path: Optional[str] = None) -> Tuple[Image.Image, str]:
    """Generates the pass image with QR, Barcode and details."""
    ticket_id = str(uuid.uuid4()).split('-')[0].upper()
    theme = THEMES.get(theme_name, THEMES["Tech"])
    header_color = theme["header"]
    accent_color = theme["accent"]

    width, height = 900, 550
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # Thick Border
    border_width = 10
    draw.rectangle([0, 0, width, height], outline=header_color, width=border_width)

    # Header Bar
    header_height = 80
    draw.rectangle([border_width, border_width, width-border_width, header_height], fill=header_color)

    # Header Text
    font_title = get_font(40, bold=True)
    draw.text((30, 20), "FEST PASS", fill="white", font=font_title)
    
    font_event = get_font(30, bold=True)
    # Right align event name
    event_bbox = draw.textbbox((0, 0), event.upper(), font=font_event)
    event_w = event_bbox[2] - event_bbox[0]
    draw.text((width - event_w - 30, 25), event.upper(), fill=accent_color, font=font_event)

    # Photo (Optional)
    if photo_path:
        try:
            photo = Image.open(photo_path)
            photo = photo.resize((140, 160))
            if photo.mode != 'RGB':
                photo = photo.convert('RGB')
            img.paste(photo, (40, 180))
            # Photo border
            draw.rectangle([40, 180, 180, 340], outline=header_color, width=3)
        except Exception as e:
            logger.error(f"Could not load photo: {e}")

    # Labels and Values
    labels = ["NAME", "DEPARTMENT", "SEAT NO.", "TICKET ID"]
    values = [name.upper(), dept.upper(), str(seat).upper(), ticket_id]
    
    start_x = 220
    start_y = 130
    y_gap = 60

    font_label = get_font(18, bold=True)
    font_value = get_font(24, bold=False)
    font_id = get_font(28, bold=True)

    for i in range(4):
        y = start_y + (i * y_gap)
        draw.text((start_x, y), labels[i], fill=header_color, font=font_label)
        val_font = font_id if i == 3 else font_value
        val_color = header_color if i == 3 else "black"
        draw.text((start_x, y + 25), values[i], fill=val_color, font=val_font)

    # QR Code
    try:
        qr = qrcode.QRCode(box_size=4, border=2)
        qr.add_data(ticket_id)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color=header_color, back_color="white").resize((140, 140))
        img.paste(qr_img, (width - 140 - 40, 180))
    except Exception as e:
        logger.error(f"Error generating QR: {e}")

    # Barcode
    try:
        rv = io.BytesIO()
        Code128 = barcode.get_barcode_class('code128')
        bar = Code128(ticket_id, writer=ImageWriter())
        bar.write(rv)
        rv.seek(0)
        bar_img = Image.open(rv).resize((450, 80))
        img.paste(bar_img, (int((width - 450) / 2), 430))
    except Exception as e:
        logger.error(f"Error generating Barcode: {e}")

    # Save to Database
    save_ticket(ticket_id, name, dept, event, seat, email, roll_no, email_verified)
    
    return img, ticket_id

# --- EMAIL DELIVERY ---

def send_otp_email(to_email: str, otp: str) -> Tuple[bool, str]:
    """Sends a 6-digit OTP email."""
    if not to_email or not EMAIL_SENDER or not EMAIL_PASSWORD:
        return False, "Email configuration missing."
        
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = to_email
        msg['Subject'] = "FestPass OTP Verification"

        body = f"Your OTP for FestPass generation is: {otp}\n\nPlease do not share this with anyone."
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info(f"OTP Email successfully sent to {to_email}")
        return True, "OTP Email sent successfully."
    except Exception as e:
        logger.error(f"OTP Email failed: {e}")
        return False, f"Email failed: {e}"

def send_pass_email(to_email: str, name: str, ticket_id: str, pass_image: Image.Image) -> Tuple[bool, str]:
    """Sends an email with the pass image attached."""
    if not to_email or not EMAIL_SENDER or not EMAIL_PASSWORD:
        return False, "Email configuration missing."
        
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = to_email
        msg['Subject'] = f"Your FestPass – [{ticket_id}]"

        body = f"Hello {name},\n\nYour FestPass (Ticket ID: {ticket_id}) has been generated successfully.\nPlease find the pass attached as an image.\n\nEnjoy the event!"
        msg.attach(MIMEText(body, 'plain'))

        # Convert PIL Image to bytes
        img_byte_arr = io.BytesIO()
        pass_image.save(img_byte_arr, format='PNG')
        img_byte_arr_bytes = img_byte_arr.getvalue()

        image_attachment = MIMEImage(img_byte_arr_bytes, name=f"FestPass_{ticket_id}.png")
        msg.attach(image_attachment)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info(f"Email successfully sent to {to_email} for ticket {ticket_id}")
        return True, "Email sent successfully."
    except Exception as e:
        logger.error(f"Email failed: {e}")
        return False, f"Email failed: {e}"

# --- PDF EXPORT ---

def get_pdf_bytes(pass_image: Image.Image) -> bytes:
    """Converts a PIL Image to a PDF returning the byte stream."""
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    a4_width, a4_height = A4
    
    # 75% scale of 900x550
    target_width = 900 * 0.75
    target_height = 550 * 0.75
    
    x = (a4_width - target_width) / 2
    y = (a4_height - target_height) / 2
    
    # Convert PIL Image to ReportLab ImageReader
    img_byte_arr = io.BytesIO()
    pass_image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    img_reader = ImageReader(img_byte_arr)
    
    c.drawImage(img_reader, x, y, width=target_width, height=target_height)
    c.showPage()
    c.save()
    
    pdf_bytes = pdf_buffer.getvalue()
    return pdf_bytes

def export_to_pdf(pass_image: Image.Image, save_path: str) -> None:
    """Exports a pass image to a PDF file at the specified path."""
    pdf_bytes = get_pdf_bytes(pass_image)
    with open(save_path, 'wb') as f:
        f.write(pdf_bytes)

# Initialize DB on import
init_db()
