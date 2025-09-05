import os, re, csv, sqlite3, io
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, send_file

DB_PATH = os.environ.get("DB_PATH", "/data/app.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB max upload

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

HTML = """
<!doctype html>
<title>CSV Import (Serverless-style)</title>
<link rel="stylesheet" href="https://unpkg.com/milligram@1.4.1/dist/milligram.min.css">
<div class="container" style="max-width: 900px; margin-top: 30px">
  <h2>CSV Import Demo</h2>
  <p>Upload a CSV with columns: <code>name,email,age</code> (UTF-8).</p>
  <form action="/upload" method="post" enctype="multipart/form-data">
    <input type="file" name="file" accept=".csv">
    <button type="submit" class="button-primary">Upload & Import</button>
    <a class="button" href="/sample">Download sample CSV</a>
    <a class="button" href="/export">Export DB</a>
  </form>

  {% if summary %}
  <hr>
  <h4>Result</h4>
  <p>Inserted: <b>{{summary.ok}}</b> &nbsp; | &nbsp; Errors: <b>{{summary.err}}</b></p>
  {% if errors %}
  <details open><summary>View errors ({{summary.err}})</summary>
    <ul>
      {% for e in errors %}<li>Row {{e.row}}: {{e.msg}}</li>{% endfor %}
    </ul>
  </details>
  {% endif %}
  {% endif %}

  <hr>
  <h4>Latest records (top 50)</h4>
  <table>
    <thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Age</th><th>Created</th></tr></thead>
    <tbody>
      {% for r in rows %}
      <tr>
        <td>{{r[0]}}</td><td>{{r[1]}}</td><td>{{r[2]}}</td><td>{{r[3]}}</td><td>{{r[4]}}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
"""

def db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        age INTEGER NOT NULL,
        created_at TEXT NOT NULL
    )""")
    return con

@app.get("/")
def home():
    with db() as con:
        rows = con.execute("SELECT id,name,email,age,created_at FROM customers ORDER BY id DESC LIMIT 50").fetchall()
    return render_template_string(HTML, rows=rows, summary=None, errors=None)

@app.get("/sample")
def sample():
    csv_bytes = b"name,email,age\nAlice,alice@example.com,30\nBob,bob@example.org,25\n"
    return send_file(io.BytesIO(csv_bytes), mimetype="text/csv", as_attachment=True, download_name="sample_customers.csv")

@app.get("/export")
def export():
    with db() as con:
        rows = con.execute("SELECT name,email,age,created_at FROM customers ORDER BY id").fetchall()
    sio = io.StringIO()
    w = csv.writer(sio)
    w.writerow(["name","email","age","created_at"])
    for r in rows:
        w.writerow(r)
    return send_file(io.BytesIO(sio.getvalue().encode("utf-8")), mimetype="text/csv",
                     as_attachment=True, download_name="customers_export.csv")

@app.post("/upload")
def upload():
    if "file" not in request.files:
        return "No file part", 400
    f = request.files["file"]
    if not f.filename or not f.filename.lower().endswith(".csv"):
        return "Please upload a .csv file", 400

    errors = []
    ok = 0
    # Read CSV safely as text
    wrapper = io.TextIOWrapper(f.stream, encoding="utf-8", newline="")
    reader = csv.DictReader(wrapper)

    required = {"name", "email", "age"}
    if not required.issubset(set([c.strip().lower() for c in reader.fieldnames or []])):
        return "Header must include: name,email,age", 400

    with db() as con:
        for i, row in enumerate(reader, start=2):  # start=2 because row 1 is header
            name = (row.get("name") or "").strip()
            email = (row.get("email") or "").strip().lower()
            age_s = (row.get("age") or "").strip()

            # Validations
            if len(name) < 2:
                errors.append({"row": i, "msg": "name must be at least 2 characters"})
                continue
            if not EMAIL_RE.match(email):
                errors.append({"row": i, "msg": "invalid email"})
                continue
            try:
                age = int(age_s)
                if age < 1 or age > 120:
                    raise ValueError
            except Exception:
                errors.append({"row": i, "msg": "age must be an integer 1–120"})
                continue

            try:
                con.execute("INSERT INTO customers(name,email,age,created_at) VALUES(?,?,?,?)",
                            (name, email, age, datetime.utcnow().isoformat(timespec="seconds")+"Z"))
                ok += 1
            except sqlite3.IntegrityError:
                errors.append({"row": i, "msg": "duplicate email (already imported)"})
                continue

        con.commit()

    with db() as con:
        rows = con.execute("SELECT id,name,email,age,created_at FROM customers ORDER BY id DESC LIMIT 50").fetchall()

    return render_template_string(HTML, rows=rows,
                                  summary={"ok": ok, "err": len(errors)},
                                  errors=errors)

@app.get("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
