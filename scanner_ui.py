import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import threading
import event_backend
from pyzbar import pyzbar

class ScannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🎥 QR Scanner – Entry Gate")
        self.geometry("400x300")
        self.configure(bg="#2d2d2d")
        
        self.setup_ui()
        
    def setup_ui(self):
        lbl_title = tk.Label(self, text="🎟️ Entry Gate Scanner", bg="#2d2d2d", fg="white", font=("Arial", 16, "bold"), pady=20)
        lbl_title.pack(fill=tk.X)
        
        self.btn_scan = tk.Button(self, text="📷 Start Scanner", bg="#4CAF50", fg="white", font=("Arial", 14, "bold"), pady=15, command=self.start_scanner_thread)
        self.btn_scan.pack(pady=20, padx=50, fill=tk.X)
        
        self.lbl_result = tk.Label(self, text="Ready to scan", bg="#2d2d2d", fg="lightgray", font=("Arial", 14, "bold"), pady=20)
        self.lbl_result.pack(fill=tk.X)

    def start_scanner_thread(self):
        self.btn_scan.config(state=tk.DISABLED, text="📷 Scanning...")
        self.lbl_result.config(text="Aim QR Code at Camera...", fg="yellow")
        threading.Thread(target=self.scan_qr_camera, daemon=True).start()

    def scan_qr_camera(self):
        cap = cv2.VideoCapture(0)
        
        ticket_id = None
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            decoded_objects = pyzbar.decode(frame)
            
            for obj in decoded_objects:
                # Draw bounding box
                points = obj.polygon
                if len(points) == 4:
                    pts = [(point.x, point.y) for point in points]
                    for i in range(4):
                        cv2.line(frame, pts[i], pts[(i+1)%4], (0, 255, 0), 3) # Green box
                        
                ticket_id = obj.data.decode('utf-8')
                break # Process the first found QR code
            
            # Show the camera feed
            cv2.imshow("Scanner (Press 'q' to cancel)", frame)
            
            if ticket_id:
                # Add slight delay so user sees the green box before window closes
                cv2.waitKey(500)
                break
                
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        cap.release()
        cv2.destroyAllWindows()
        
        # Ensure UI updates are on the main thread
        self.after(0, self.process_scan_result, ticket_id)

    def process_scan_result(self, ticket_id):
        self.btn_scan.config(state=tk.NORMAL, text="📷 Start Scanner")
        
        if ticket_id:
            result = event_backend.scan_ticket(ticket_id)
            
            if "Allowed" in result:
                color = "#4CAF50" # Green
            elif "Used" in result:
                color = "#FF9800" # Orange
            else:
                color = "#F44336" # Red
                
            self.lbl_result.config(text=result, fg=color)
        else:
            self.lbl_result.config(text="Scan Cancelled.", fg="orange")

if __name__ == "__main__":
    app = ScannerApp()
    app.mainloop()
