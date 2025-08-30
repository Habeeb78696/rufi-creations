from flask import (
    Flask, request, render_template, render_template_string,
    jsonify, session, redirect, url_for, flash
)
from functools import wraps
from flask import session, redirect, url_for

import sqlite3, os, requests, random, time, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# ---------------------------
# App Config
# ---------------------------
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # TODO: replace with a secure random value in production

# Hardcoded admin creds (as requested)
ADMIN_USER = 'UT@2025'
ADMIN_PASS = 'Rufi@2025'

# Telegram (provided)
TELEGRAM_BOT_TOKEN = "8225553048:AAGxvPyYOGQG11GzaAqhSlK2U268aGl3_9A"
CHAT_ID = "7887307343"


# Email follow-up (provided)
EMAIL_SENDER = 'rufi.creation@gmail.com'
EMAIL_PASSWORD = 'lmmt bgyf mlxk pnuu'

DB_PATH = 'database.db'

# ---------------------------
# Helpers
# ---------------------------
def db_conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("admin_login"))  # ✅ matches your function name
        return f(*args, **kwargs)
    return decorated_function

def init_db():
    con = db_conn()
    cur = con.cursor()
    # Leads table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT NOT NULL,
            message TEXT,
            whatsapp INTEGER DEFAULT 0,
            urgency TEXT,
            service TEXT,
            submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Single-row settings table (id=1)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            modal_image TEXT,
            banner1 TEXT,
            banner2 TEXT,
            banner3 TEXT,
            banner4 TEXT,
            banner5 TEXT
        )
    """)
    # Ensure the single row exists
    cur.execute("SELECT id FROM settings WHERE id=1")
    if cur.fetchone() is None:
        cur.execute("""
            INSERT INTO settings (id, modal_image, banner1, banner2, banner3, banner4, banner5)
            VALUES (1, NULL, NULL, NULL, NULL, NULL, NULL)
        """)
    con.commit()
    con.close()

def send_telegram_message(text: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("Telegram send error:", e)

def send_followup_email(to_email, user_name):
    subject = f"We’ve received your request, {user_name}!"
    body = f"""
Hi {user_name},

✅ I just received your details — thank you for reaching out to *Rufi Creations*! 🖌️

Our team will get in touch with you shortly to assist with your request.

Meanwhile, feel free to explore more of our work or chat with us directly:

🌐 Instagram: https://www.instagram.com/rufi_creations/
🌐 Facebook:  https://www.facebook.com/profile.php?id=100088707296322
💬 WhatsApp: https://wa.me/919606888425?text=I%20want%20to%20know%20the%20details

We’re excited to help bring your ideas to life!

Warm regards,
The Rufi Creations Team
"""
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
        print("✅ Follow-up email sent to", to_email)
    except Exception as e:
        print("❌ Email send error:", e)

def get_settings():
    con = db_conn()
    cur = con.cursor()
    cur.execute("SELECT * FROM settings WHERE id=1")
    row = cur.fetchone()
    con.close()
    return row

# ---------------------------
# Public Routes
# ---------------------------
@app.route('/')
def index():
    # Pass settings to the homepage so your template can use dynamic images
    settings = get_settings()
    return render_template("index.html",
                           form_submitted=session.get('form_submitted', False),
                           settings=settings)

@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json() or {}
    print("Received data:", data)

    name = (data.get('name') or '').strip()
    phone = (data.get('phone') or '').strip()
    email = (data.get('email') or '').strip()
    message = (data.get('message') or '').strip()
    whatsapp = data.get('whatsapp', False)
    urgency = (data.get('urgency') or '').strip()
    service = (data.get('service') or '').strip()

    if not name or not phone:
        return jsonify(status='error', error='Missing required fields'), 400

    # Compose Telegram message (same logic you had)
    if urgency and service:
        telegram_message = (
            f"🤖 *New Chatbot Lead*\n\n"
            f"👤 Name: {name}\n"
            f"📧 Email: {email if email else 'N/A'}\n"
            f"📞 Phone: {phone}\n"
            f"⚡ Urgency: {urgency}\n"
            f"🛠️ Service: {service}"
        )
    else:
        telegram_message = (
            f"📝 *New Lead*\n\n"
            f"👤 Name: {name}\n"
            f"📧 Email: {email if email else 'N/A'}\n"
            f"📞 Phone: {phone}\n"
            f"💬 Message: {message if message else 'N/A'}\n"
            f"📱 WhatsApp: {'Yes' if whatsapp else 'No'}"
        )

    # Save to DB
    con = db_conn()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO leads (name, email, phone, message, whatsapp, urgency, service)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, email, phone, message, 1 if whatsapp else 0, urgency, service))
    con.commit()
    con.close()

    # Send Telegram
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": telegram_message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            session['form_submitted'] = True
            if email:
                send_followup_email(email, name)
            return jsonify(status='success')
        else:
            print("Telegram API Error:", response.status_code, response.text)
            return jsonify(status='error', error='Telegram API failed'), 500
    except Exception as e:
        print("Exception:", e)
        return jsonify(status='error', error='Internal Server Error'), 500

# ---------------------------
# Admin Auth + OTP
# ---------------------------
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    
    # Step 1: username + password
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == ADMIN_USER and password == ADMIN_PASS:
            # Generate 5-digit OTP and send to Telegram
            otp = random.randint(10000, 99999)
            session['pending_user'] = username
            session['otp'] = str(otp)
            session['otp_exp'] = int(time.time()) + 120  # valid for 2 minutes

            send_telegram_message(f"🔐 *Rufi Admin OTP*\n\nYour OTP is: *{otp}*\n(Valid for 2 minutes)")
            return redirect(url_for('admin_otp'))
        else:
            flash('Invalid username or password', 'danger')

    # Simple login page
    return render_template_string("""
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Admin Login</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
</head>
<body class="bg-light">
<div class="container py-5">
  <div class="row justify-content-center">
    <div class="col-md-4">
      <div class="card shadow-sm">
        <div class="card-body">
          <h4 class="mb-3 text-center">Admin Login</h4>
          {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for cat, msg in messages %}
              <div class="alert alert-{{cat}}">{{msg}}</div>
            {% endfor %}
          {% endif %}
          {% endwith %}
          <form method="post">
            <div class="mb-3">
              <label class="form-label">Username</label>
              <input name="username" class="form-control" placeholder="User Name" required>
            </div>
            <div class="mb-3">
              <label class="form-label">Password</label>
              <input name="password" type="password" class="form-control" placeholder="Password" required>
            </div>
            <button class="btn btn-primary w-100">Continue</button>
          </form>
        </div>
      </div>
      <p class="text-center text-muted mt-3">&copy; Rufi Creations</p>
    </div>
  </div>
</div>
</body>
</html>
    """)

@app.route('/admin/otp', methods=['GET', 'POST'])

def admin_otp():
    # Step 2: OTP input & verify
    if 'pending_user' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        code = (request.form.get('otp') or '').strip()
        otp = session.get('otp')
        otp_exp = session.get('otp_exp', 0)
        now = int(time.time())

        if not otp or now > otp_exp:
            flash('OTP expired. Please login again.', 'danger')
            return redirect(url_for('admin_login'))

        if code == otp:
            # Success -> log in admin
            session.pop('otp', None)
            session.pop('otp_exp', None)
            session['admin'] = session.pop('pending_user')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid OTP, try again.', 'danger')

    return render_template_string("""
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Enter OTP</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
</head>
<body class="bg-light">
<div class="container py-5">
  <div class="row justify-content-center">
    <div class="col-md-4">
      <div class="card shadow-sm">
        <div class="card-body">
          <h4 class="mb-3 text-center">Enter OTP</h4>
          {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for cat, msg in messages %}
              <div class="alert alert-{{cat}}">{{msg}}</div>
            {% endfor %}
          {% endif %}
          {% endwith %}
          <form method="post">
            <div class="mb-3">
              <label class="form-label">5-digit OTP</label>
              <input name="otp" class="form-control" placeholder="12345" required maxlength="5">
            </div>
            <button class="btn btn-success w-100">Verify</button>
          </form>
          <p class="text-muted small mt-3">OTP sent to your Telegram.</p>
        </div>
      </div>
      <p class="text-center text-muted mt-3">&copy; Rufi Creations</p>
    </div>
  </div>
</div>
</body>
</html>
    """)

@app.route('/logout')

def logout():
    session.clear()
    return redirect(url_for('admin_login'))

def admin_required():
    if not session.get('admin'):
        return False
    return True

# ---------------------------
# Dashboard + Settings
# ---------------------------
@app.route('/dashboard')
def dashboard():
    if not admin_required():
        return redirect(url_for('admin_login'))

    # Fetch leads and settings
    con = db_conn()
    cur = con.cursor()
    cur.execute("SELECT * FROM leads ORDER BY submitted_at DESC")
    leads = cur.fetchall()
    cur.execute("SELECT * FROM settings WHERE id=1")
    settings = cur.fetchone()
    con.close()

    # Simple dashboard (Bootstrap)
    return render_template_string("""
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Rufi Admin Dashboard</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
  <style>
    .img-prev{max-height:120px; object-fit:cover; border:1px solid #eee; border-radius:6px;}
    .table-wrap{overflow:auto;}
  </style>
</head>
<body>
<nav class="navbar navbar-dark bg-dark">
  <div class="container-fluid">
    <span class="navbar-brand">Rufi Admin</span>
    <div>
      <a class="btn btn-sm btn-outline-light" href="{{ url_for('logout') }}">Logout</a>
    </div>
  </div>
</nav>

<div class="container py-4">
  <div class="row g-4">
    <div class="col-12">
      <div class="card shadow-sm">
        <div class="card-body">
          <h5 class="card-title mb-3">Site Images (Modal & Banners)</h5>
          <form method="post" action="{{ url_for('update_settings') }}">
            <div class="row g-3">
              <div class="col-md-6">
                <label class="form-label">Modal Image URL</label>
                <input name="modal_image" class="form-control" value="{{ settings['modal_image'] or '' }}" placeholder="https://...">
                {% if settings['modal_image'] %}
                  <img src="{{ settings['modal_image'] }}" class="img-prev mt-2">
                {% endif %}
              </div>
              {% for i in range(1,6) %}
              <div class="col-md-6">
                <label class="form-label">Banner {{ i }} URL</label>
                <input name="banner{{ i }}" class="form-control" value="{{ settings['banner' ~ i] or '' }}" placeholder="https://...">
                {% if settings['banner' ~ i] %}
                  <img src="{{ settings['banner' ~ i] }}" class="img-prev mt-2">
                {% endif %}
              </div>
              {% endfor %}
            </div>
            <button class="btn btn-primary mt-3">Save Images</button>
          </form>
        </div>
      </div>
    </div>

    <div class="col-12">
      <div class="card shadow-sm">
        <div class="card-body">
          <h5 class="card-title">Leads</h5>
          <div class="table-wrap">
            <table class="table table-striped table-hover align-middle">
              <thead class="table-dark">
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Phone</th>
                  <th>WhatsApp</th>
                  <th>Urgency</th>
                  <th>Service</th>
                  <th>Message</th>
                  <th>Submitted</th>
                </tr>
              </thead>
              <tbody>
                {% for r in leads %}
                <tr>
                  <td>{{ r['id'] }}</td>
                  <td>{{ r['name'] }}</td>
                  <td>{{ r['email'] or '' }}</td>
                  <td>{{ r['phone'] }}</td>
                  <td>{{ 'Yes' if r['whatsapp'] else 'No' }}</td>
                  <td>{{ r['urgency'] or '' }}</td>
                  <td>{{ r['service'] or '' }}</td>
                  <td style="max-width:320px; white-space:pre-wrap">{{ r['message'] or '' }}</td>
                  <td>{{ r['submitted_at'] }}</td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
          <a class="btn btn-outline-secondary" href="{{ url_for('export_csv') }}">Export CSV</a>
        </div>
      </div>
    </div>
  </div>
</div>
</body>
</html>

    """, leads=leads, settings=settings)

@app.route('/update-settings', methods=['POST'])

def update_settings():
    if not admin_required():
        return redirect(url_for('admin_login'))

    modal_image = (request.form.get('modal_image') or '').strip() or None
    banners = []
    for i in range(1, 6):
        b = (request.form.get(f'banner{i}') or '').strip() or None
        banners.append(b)

    con = db_conn()
    cur = con.cursor()
    cur.execute("""
        UPDATE settings
           SET modal_image=?,
               banner1=?, banner2=?, banner3=?, banner4=?, banner5=?
         WHERE id=1
    """, (modal_image, *banners))
    con.commit()
    con.close()
    flash('Settings updated!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/export.csv')

def export_csv():
    if not admin_required():
        return redirect(url_for('admin_login'))

    con = db_conn()
    cur = con.cursor()
    cur.execute("SELECT id, name, email, phone, message, whatsapp, urgency, service, submitted_at FROM leads ORDER BY submitted_at DESC")
    rows = cur.fetchall()
    con.close()

    # Build CSV
    lines = ["id,name,email,phone,message,whatsapp,urgency,service,submitted_at"]
    for r in rows:
        # Basic CSV escaping for commas/quotes/newlines
        def esc(v):
            if v is None:
                v = ""
            v = str(v)
            if any(c in v for c in [',', '"', '\n']):
                v = '"' + v.replace('"', '""') + '"'
            return v
        lines.append(",".join([
            esc(r['id']), esc(r['name']), esc(r['email']), esc(r['phone']),
            esc(r['message']), esc('Yes' if r['whatsapp'] else 'No'),
            esc(r['urgency']), esc(r['service']), esc(r['submitted_at'])
        ]))
    csv_data = "\n".join(lines)
    return app.response_class(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"}
    )

# ---------------------------
# Init + Run
# ---------------------------
import os

if __name__ == '__main__':
    # Initialize database
    init_db()

    # Ensure templates folder exists
    os.makedirs('templates', exist_ok=True)

    # Use environment PORT if set (for Render/Heroku), else default to 8000
    port = int(os.environ.get("PORT", 8000))
    
    app.run(debug=True, host="0.0.0.0", port=port)
