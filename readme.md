# CSV Import Demo (Flask + SQLite)

This is a lightweight **CSV Import Web App** built with **Flask** and **SQLite**.  
It allows uploading a CSV file with customer data (`name,email,age`), validates and inserts it into a database, and provides options to **view records**, **download a sample CSV**, and **export database records**.

---

## ✨ Features
- Upload CSV with columns: `name,email,age`
- Validations:
  - Name: at least 2 characters
  - Email: valid format, unique
  - Age: integer between 1–120
- Duplicate email detection
- Export database to CSV
- Download a sample CSV template
- Lightweight SQLite storage
- Ready-to-run with Docker

---

## 🚀 Running Locally

### Prerequisites
- Python 3.9+  
- `pip` for dependency installation  

### Setup
git clone https://github.com/your-username/csv-import-demo.git
cd csv-import-demo

# (Optional) create virtual environment
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
The app will start at:
👉 http://localhost:8080

### 🐳 Run with Docker

# Build the image:

docker build -t csv-import-demo .


# Run the container:

docker run -d -p 8080:8080 -v $(pwd)/data:/data csv-import-demo


# Now open:
👉 http://localhost:8080

Database will be stored in the ./data folder.

### 📂 Project Structure
.
├── app.py              # Main Flask app
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker build instructions
└── README.md           # Documentation

#🔑 API Endpoints
Method	Endpoint	Description
GET	/	Homepage with upload form & recent records
POST	/upload	Upload and import CSV file
GET	/sample	Download a sample CSV file
GET	/export	Export database as CSV
GET	/health	Health check (returns OK)
## 📊 Sample CSV
name,email,age
Alice,alice@example.com,30
Bob,bob@example.org,25

## ⚡ Example Workflow

Visit / and upload a CSV file.

App validates and imports rows.

View latest 50 records in the browser.

Export full database with /export.

## 🛠️ Development Notes

Database path defaults to /data/app.db. Override with:

export DB_PATH=/custom/path/app.db


Max upload size: 5 MB

Emails must be unique. Duplicate rows will be reported as errors.