import csv
import argparse
import sys
import os
import event_backend
import validators
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def bulk_generate(csv_file: str, send_emails: bool = False):
    """
    Reads a CSV file and generates event passes in bulk.
    CSV Columns expected: name, dept, event, seat, email, theme
    """
    if not os.path.exists(csv_file):
        logging.error(f"CSV file not found: {csv_file}")
        sys.exit(1)

    generated_count = 0
    error_count = 0

    with open(csv_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2): # Row 1 is header
            name = row.get('name', '').strip()
            dept = row.get('dept', '').strip()
            event = row.get('event', '').strip()
            seat = row.get('seat', '').strip()
            email = row.get('email', '').strip()
            roll_no = row.get('roll_no', '').strip()
            theme = row.get('theme', 'Tech').strip()

            if not all([name, dept, event, seat, roll_no, email]):
                logging.warning(f"Row {row_num}: Missing required fields. Skipping.")
                error_count += 1
                continue
            
            if not validators.is_valid_name(name):
                logging.warning(f"Row {row_num}: Invalid name '{name}'. Skipping.")
                error_count += 1
                continue
                
            if not validators.is_valid_seat(seat):
                logging.warning(f"Row {row_num}: Invalid seat '{seat}'. Skipping.")
                error_count += 1
                continue

            if not validators.is_valid_email(email):
                logging.warning(f"Row {row_num}: Invalid email '{email}'. Skipping.")
                error_count += 1
                continue
                
            if not validators.is_valid_roll_no(roll_no):
                logging.warning(f"Row {row_num}: Invalid roll_no '{roll_no}'. Skipping.")
                error_count += 1
                continue
                
            if event_backend.is_duplicate(email, event) or event_backend.is_roll_duplicate(roll_no, event):
                logging.warning(f"Row {row_num}: Duplicate ticket for {email} or {roll_no}. Skipping.")
                error_count += 1
                continue

            try:
                img, ticket_id = event_backend.generate_pass_image(
                    name=name, dept=dept, event=event, seat=seat, 
                    email=email, roll_no=roll_no, theme_name=theme, email_verified=True, photo_path=None
                )
                
                pdf_path = f"Pass_{ticket_id}_{name.replace(' ', '_')}.pdf"
                event_backend.export_to_pdf(img, pdf_path)
                logging.info(f"Generated pass for {name} -> {pdf_path}")
                generated_count += 1

                if send_emails and email:
                    success, msg = event_backend.send_pass_email(email, name, ticket_id, img)
                    if success:
                        logging.info(f"  -> Email sent to {email}")
                    else:
                        logging.error(f"  -> Failed to send email to {email}: {msg}")

            except Exception as e:
                logging.error(f"Row {row_num}: Failed to generate pass: {e}")
                error_count += 1

    logging.info(f"Bulk generation complete. Generated: {generated_count}, Errors: {error_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bulk generate FestPasses from a CSV file.")
    parser.add_argument("csv_file", help="Path to the CSV file")
    parser.add_argument("--email", action="store_true", help="Send emails to generated passes if email is provided")
    args = parser.parse_args()

    bulk_generate(args.csv_file, args.email)
