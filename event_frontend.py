import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import event_backend
import validators
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random

class EventPassApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🎟️ FestPass Studio")
        self.geometry("1400x800")
        self.configure(bg="#f4f4f4")
        
        self.current_pass_image = None
        self.current_ticket_id = None
        self.photo_path = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Top Bar
        top_lbl = tk.Label(self, text="🎟️ FEST PASS STUDIO", bg="#003366", fg="white", font=("Arial", 20, "bold"), pady=15)
        top_lbl.pack(fill=tk.X)
        
        # Notebook for Tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Tab Frames
        self.tab_generator = tk.Frame(self.notebook, bg="#f4f4f4")
        self.tab_admin = tk.Frame(self.notebook, bg="#f4f4f4")
        
        self.notebook.add(self.tab_generator, text="🎟️ Generator")
        self.notebook.add(self.tab_admin, text="📊 Admin Panel")
        
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        self.admin_authenticated = False
        
        self.setup_generator_tab()
        self.setup_admin_tab()
        
    def setup_generator_tab(self):
        main_frame = tk.Frame(self.tab_generator, bg="#f4f4f4")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left Panel - Input
        left_panel = tk.LabelFrame(main_frame, text="Enter Details", bg="#f4f4f4", font=("Arial", 12, "bold"), padx=20, pady=20)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        
        # Grid settings for left panel
        for i in range(8):
            left_panel.grid_rowconfigure(i, pad=15)
            
        font_lbl = ("Arial", 11)
        font_entry = ("Arial", 11)
        
        tk.Label(left_panel, text="Full Name:", bg="#f4f4f4", font=font_lbl).grid(row=0, column=0, sticky="w")
        self.ent_name = ttk.Entry(left_panel, width=30, font=font_entry)
        self.ent_name.grid(row=0, column=1, sticky="w")

        tk.Label(left_panel, text="Department:", bg="#f4f4f4", font=font_lbl).grid(row=1, column=0, sticky="w")
        self.ent_dept = ttk.Entry(left_panel, width=30, font=font_entry)
        self.ent_dept.grid(row=1, column=1, sticky="w")

        tk.Label(left_panel, text="Event Name:", bg="#f4f4f4", font=font_lbl).grid(row=2, column=0, sticky="w")
        self.ent_event = ttk.Entry(left_panel, width=30, font=font_entry)
        self.ent_event.grid(row=2, column=1, sticky="w")

        tk.Label(left_panel, text="Seat Number:", bg="#f4f4f4", font=font_lbl).grid(row=3, column=0, sticky="w")
        self.ent_seat = ttk.Entry(left_panel, width=30, font=font_entry)
        self.ent_seat.grid(row=3, column=1, sticky="w")

        tk.Label(left_panel, text="Roll Number:", bg="#f4f4f4", font=font_lbl).grid(row=4, column=0, sticky="w")
        self.ent_roll_no = ttk.Entry(left_panel, width=30, font=font_entry)
        self.ent_roll_no.grid(row=4, column=1, sticky="w")

        tk.Label(left_panel, text="Email (College):", bg="#f4f4f4", font=font_lbl).grid(row=5, column=0, sticky="w")
        self.ent_email = ttk.Entry(left_panel, width=30, font=font_entry)
        self.ent_email.grid(row=5, column=1, sticky="w")
        
        tk.Label(left_panel, text="Theme:", bg="#f4f4f4", font=font_lbl).grid(row=6, column=0, sticky="w")
        self.theme_var = tk.StringVar(value="Tech")
        self.opt_theme = ttk.OptionMenu(left_panel, self.theme_var, "Tech", *event_backend.THEMES.keys())
        self.opt_theme.grid(row=6, column=1, sticky="w")
        
        self.btn_photo = tk.Button(left_panel, text="📸 Upload Photo", bg="#e0e0e0", command=self.upload_photo, font=font_lbl)
        self.btn_photo.grid(row=7, column=0, columnspan=2, sticky="ew")
        self.lbl_photo_status = tk.Label(left_panel, text="No photo selected", bg="#f4f4f4", fg="gray", font=("Arial", 9))
        self.lbl_photo_status.grid(row=8, column=0, columnspan=2)

        self.btn_generate = tk.Button(left_panel, text="🚀 GENERATE PASS", bg="#4CAF50", fg="white", font=("Arial", 14, "bold"), pady=10, command=self.generate_pass)
        self.btn_generate.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(20, 5))
        
        self.lbl_status = tk.Label(left_panel, text="", bg="#f4f4f4", fg="blue", font=("Arial", 10))
        self.lbl_status.grid(row=10, column=0, columnspan=2)

        # Right Panel - Live Preview
        right_panel = tk.LabelFrame(main_frame, text="Live Preview", bg="#f4f4f4", font=("Arial", 12, "bold"), padx=20, pady=20)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.lbl_preview = tk.Label(right_panel, text="Generate a pass to see preview here", bg="white", width=80, height=22, relief="solid")
        self.lbl_preview.pack(expand=True)
        
        # Bottom Button Bar
        btn_bar = tk.Frame(right_panel, bg="#f4f4f4")
        btn_bar.pack(fill=tk.X, pady=(20, 0))
        
        self.btn_save_png = tk.Button(btn_bar, text="💾 Save as PNG", bg="#2196F3", fg="white", font=font_lbl, state=tk.DISABLED, command=self.save_png)
        self.btn_save_png.pack(side=tk.LEFT, padx=5)

        self.btn_save_pdf = tk.Button(btn_bar, text="📄 Export as PDF", bg="#FF9800", fg="white", font=font_lbl, state=tk.DISABLED, command=self.save_pdf)
        self.btn_save_pdf.pack(side=tk.LEFT, padx=5)

        self.btn_email = tk.Button(btn_bar, text="✉️ Send Email", bg="#9C27B0", fg="white", font=font_lbl, state=tk.DISABLED, command=self.send_email)
        self.btn_email.pack(side=tk.LEFT, padx=5)

        self.btn_clear = tk.Button(btn_bar, text="🗑️ Clear All", bg="#F44336", fg="white", font=font_lbl, command=self.clear_all)
        self.btn_clear.pack(side=tk.RIGHT, padx=5)

    def setup_admin_tab(self):
        self.admin_paned = tk.PanedWindow(self.tab_admin, orient=tk.VERTICAL)
        self.admin_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        top_frame = tk.Frame(self.admin_paned, bg="#f4f4f4")
        self.admin_paned.add(top_frame, height=400)
        
        top_bar = tk.Frame(top_frame, bg="#f4f4f4")
        top_bar.pack(fill=tk.X)
        
        btn_refresh = tk.Button(top_bar, text="🔄 Refresh Table", bg="#2196F3", fg="white", font=("Arial", 11), command=lambda: [self.load_admin_data(), self.load_stats_data()])
        btn_refresh.pack(side=tk.LEFT, padx=5)
        
        btn_export = tk.Button(top_bar, text="📥 Export CSV", bg="#4CAF50", fg="white", font=("Arial", 11), command=self.export_csv)
        btn_export.pack(side=tk.LEFT, padx=5)
        
        columns = ("id", "ticket_id", "name", "dept", "event", "seat", "email", "scanned", "created_at", "scanned_at")
        
        self.tree = ttk.Treeview(top_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(top_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Bottom Frame for Stats
        self.stats_frame = tk.Frame(self.admin_paned, bg="#f4f4f4")
        self.admin_paned.add(self.stats_frame, height=300)
        self.fig = plt.Figure(figsize=(10, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.stats_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def on_tab_changed(self, event):
        selected_tab = self.notebook.select()
        if selected_tab == self.tab_admin._w:
            if not self.admin_authenticated:
                pwd = simpledialog.askstring("Admin Login", "Enter Admin Password:", show='*')
                if pwd != event_backend.ADMIN_PASSWORD:
                    messagebox.showerror("Access Denied", "Incorrect password.")
                    self.notebook.select(self.tab_generator._w)
                    return
                else:
                    self.admin_authenticated = True
                    
            self.load_admin_data()
            self.load_stats_data()

    def load_admin_data(self):
        # Clear existing data
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        tickets = event_backend.get_all_tickets()
        for t in tickets:
            scanned_str = "Yes" if t['scanned'] else "No"
            self.tree.insert("", tk.END, values=(
                t['id'], t['ticket_id'], t['name'], t['dept'], t['event'], 
                t['seat'], t['email'], scanned_str, t['created_at'], t['scanned_at'] or "N/A"
            ))

    def export_csv(self):
        tickets = event_backend.get_all_tickets()
        if not tickets:
            messagebox.showinfo("Info", "No data to export.")
            return
            
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV file", "*.csv")])
        if path:
            try:
                with open(path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=tickets[0].keys())
                    writer.writeheader()
                    writer.writerows(tickets)
                messagebox.showinfo("Success", f"Data exported to {path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export CSV: {e}")

    def load_stats_data(self):
        self.fig.clf() # Clear previous figure
        
        stats = event_backend.get_ticket_stats()
        if stats['scanned'] == 0 and stats['pending'] == 0:
            return # No data
            
        ax1 = self.fig.add_subplot(121)
        labels = ['Scanned', 'Pending']
        sizes = [stats['scanned'], stats['pending']]
        colors = ['#4CAF50', '#FF9800']
        ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax1.axis('equal')
        ax1.set_title("Ticket Scans")

        ax2 = self.fig.add_subplot(122)
        events = list(stats['events'].keys())
        counts = list(stats['events'].values())
        ax2.bar(events, counts, color='#2196F3')
        ax2.set_title("Passes per Event")
        ax2.set_ylabel("Count")
        ax2.tick_params(axis='x', rotation=45)
        
        self.fig.tight_layout()
        self.canvas.draw()

    # --- GENERATOR LOGIC ---

    def upload_photo(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if path:
            self.photo_path = path
            self.lbl_photo_status.config(text="Photo selected ✔️", fg="green")

    def generate_pass(self):
        name = self.ent_name.get().strip()
        dept = self.ent_dept.get().strip()
        event = self.ent_event.get().strip()
        seat = self.ent_seat.get().strip()
        email = self.ent_email.get().strip()
        roll_no = self.ent_roll_no.get().strip()
        theme = self.theme_var.get()
        
        # Validation checks
        if not all([name, dept, event, seat, roll_no, email]):
            messagebox.showerror("Validation Error", "Please fill all required fields.")
            return
            
        if not validators.is_valid_name(name):
            messagebox.showerror("Validation Error", "Name is invalid or too long.")
            return
            
        if not validators.is_valid_seat(seat):
            messagebox.showerror("Validation Error", "Seat must be alphanumeric and 1-10 characters.")
            return
            
        if not validators.is_valid_roll_no(roll_no):
            messagebox.showerror("Validation Error", "Roll number is invalid.")
            return

        if not validators.is_valid_email(email):
            messagebox.showerror("Validation Error", "Must use a valid @despu.edu.in email.")
            return
            
        # Duplicate checks
        if event_backend.is_duplicate(email, event):
            messagebox.showerror("Duplicate Ticket", f"A ticket for {event} has already been generated with this email.")
            return
            
        if event_backend.is_roll_duplicate(roll_no, event):
            messagebox.showerror("Duplicate Ticket", f"A ticket for {event} has already been generated with this roll number.")
            return
            
        # OTP Validation
        self.lbl_status.config(text="Sending OTP... Please wait.")
        self.update()
        
        otp = str(random.randint(100000, 999999))
        success, msg = event_backend.send_otp_email(email, otp)
        
        if not success:
            messagebox.showerror("OTP Error", f"Failed to send OTP to {email}.\nDetail: {msg}")
            self.lbl_status.config(text="")
            return
            
        self.lbl_status.config(text="Awaiting OTP...")
        self.update()
        
        user_otp = simpledialog.askstring("OTP Verification", f"An OTP has been sent to {email}.\nPlease enter it below to generate your pass:")
        
        if not user_otp or user_otp.strip() != otp:
             messagebox.showerror("OTP Failed", "Invalid OTP or OTP entry cancelled. Ticket not generated.")
             self.lbl_status.config(text="")
             return
             
        try:
            self.lbl_status.config(text="Generating Pass...")
            self.update()
            
            img, t_id = event_backend.generate_pass_image(
                name=name, dept=dept, event=event, seat=seat, 
                email=email, roll_no=roll_no, theme_name=theme, email_verified=True, photo_path=self.photo_path
            )
            self.current_pass_image = img
            self.current_ticket_id = t_id
            
            self.lbl_status.config(text=f"Last Generated ID: {t_id}")
            
            # Update Preview (580x355)
            preview_img = img.resize((580, 355), Image.Resampling.LANCZOS)
            self.preview_photo = ImageTk.PhotoImage(preview_img)
            self.lbl_preview.config(image=self.preview_photo, text="", width=580, height=355)
            
            # Enable Buttons
            self.btn_save_png.config(state=tk.NORMAL)
            self.btn_save_pdf.config(state=tk.NORMAL)
            self.btn_email.config(state=tk.NORMAL if email else tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate pass:\n{e}")

    def save_png(self):
        if not self.current_pass_image:
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", initialfile=f"Pass_{self.current_ticket_id}.png", filetypes=[("PNG file", "*.png")])
        if path:
            self.current_pass_image.save(path)
            messagebox.showinfo("Success", f"Saved to {path}")

    def save_pdf(self):
        if not self.current_pass_image:
            return
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"Pass_{self.current_ticket_id}.pdf", filetypes=[("PDF file", "*.pdf")])
        if path:
            try:
                event_backend.export_to_pdf(self.current_pass_image, path)
                messagebox.showinfo("Success", f"Exported PDF to {path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export PDF:\n{e}")

    def send_email(self):
        if not self.current_pass_image:
            return
        email = self.ent_email.get().strip()
        name = self.ent_name.get().strip()
        if not email:
            messagebox.showwarning("Warning", "No email provided.")
            return
            
        self.lbl_status.config(text="Sending email... Please wait.")
        self.update()
        
        success, msg = event_backend.send_pass_email(email, name, self.current_ticket_id, self.current_pass_image)
        if success:
            messagebox.showinfo("Email Sent", "The pass has been sent via email.")
            self.lbl_status.config(text=f"Email sent successfully to {email}")
        else:
            messagebox.showerror("Email Error", msg)
            self.lbl_status.config(text="Email delivery failed.")

    def clear_all(self):
        self.ent_name.delete(0, tk.END)
        self.ent_dept.delete(0, tk.END)
        self.ent_event.delete(0, tk.END)
        self.ent_seat.delete(0, tk.END)
        self.ent_email.delete(0, tk.END)
        if hasattr(self, 'ent_roll_no'):
            self.ent_roll_no.delete(0, tk.END)
        self.photo_path = None
        self.lbl_photo_status.config(text="No photo selected", fg="gray")
        self.theme_var.set("Tech")
        
        self.current_pass_image = None
        self.current_ticket_id = None
        self.lbl_status.config(text="")
        
        self.lbl_preview.config(image='', text="Generate a pass to see preview here", width=80, height=22)
        
        self.btn_save_png.config(state=tk.DISABLED)
        self.btn_save_pdf.config(state=tk.DISABLED)
        self.btn_email.config(state=tk.DISABLED)

if __name__ == "__main__":
    app = EventPassApp()
    app.mainloop()
