# FestPass Studio

FestPass Studio is an advanced deskop application designed for generating, validating, and managing digital entry passes for various events, seminars, and hackathons. It seamlessly creates beautifully designed tickets complete with QR codes and Code128 Barcodes, and sends them directly via email. It also comes with an integrated OpenCV and PyZbar based entry gate scanner for ticket validation.

## ✨ Features
- **Smart Pass Generation:** Auto-generates styled tickets with QR codes and barcodes.
- **Validation:** Input sanitization for emails and name lengths before generation.
- **Email Delivery:** Send passes automatically via configured SMTP.
- **Admin Dashboard:** Access a unified dashboard of all generated passes and export to CSV.
- **Analytics:** View visual reports on scan metrics and tickets grouped per event.
- **Robust Scanner:** Use the live entry gate scanner with PyZbar to process attendees quickly natively.
- **Bulk Upload:** Utilize the `bulk_generate.py` CLI utility to generate and email passes directly from a CSV file.

## 🏗 System Architecture
```text
[ Tkinter Frontend ]
      |-- (event_frontend.py) -> Contains Generator, Admin Treeview, and Matplotlib Stats
      |-- (scanner_ui.py)     -> OpenCV Camera Feed + PyZbar Decoder
      |
      v
[ Backend Logic ]
      |-- (event_backend.py)  -> Generates pass images, sends emails, connects to DB
      |-- (bulk_generate.py)  -> Processes CSV logic
      |-- (validators.py)     -> Regex input validation
      |
      v
[ MySQL Database ]
      |-> festpass_db
         |-> tickets table
```

## 🛠️ Setup Instructions

### Prerequisites
- **Python 3.10+**
- **MySQL Server** installed and running on `localhost`.

### 1. Configure the Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```
*(Windows might require additional C++ dev tools if pyzbar fails. Usually pip handles it. Refer to pyzbar documentation if issues arise).*

### 3. Setup Database & Credentials
1. Make sure MySQL is running.
2. Rename `.env.example` to `.env` and fill in your details:
   ```ini
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=festpass_db
   
   EMAIL_SENDER=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   ```
*(The schema is automatically initialized the first time you run the backend or app).*

### 4. Running the Complete App
- To run the visual dashboard:
  ```bash
  python event_frontend.py
  ```
- To run the Entry Gate Scanner:
  ```bash
  python scanner_ui.py
  ```
- To use Bulk Generation:
  ```bash
  python bulk_generate.py data.csv --email
  ```

## 🧪 Testing
The backend is fully covered by pytest. Run unit tests using:
```bash
pytest test_backend.py
```

## 👥 Contributors
Developed for internal technical events and college fests. 
