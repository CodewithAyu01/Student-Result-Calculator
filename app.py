import os
from flask import Flask, render_template, request, redirect, session, make_response
from supabase import create_client
from dotenv import load_dotenv
from weasyprint import HTML

# =========================
# ENV SETUP
# =========================
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# FLASK APP
# =========================
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback-secret")

# =========================
# ADMIN
# =========================
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Ayushi123")

# =========================
# HOME LOGIN (MANUAL)
# =========================
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        data = supabase.table("users") \
            .select("*") \
            .eq("username", username) \
            .eq("password", password) \
            .execute()

        if data.data:
            session['user'] = username
            return redirect('/dashboard')
        else:
            error = "Invalid Username or Password"

    return render_template("login.html", error=error)

# =========================
# SIGNUP
# =========================
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        supabase.table("users").insert({
            "username": username,
            "password": password
        }).execute()

        return redirect('/')

    return render_template("signup.html")

# =========================
# GOOGLE LOGIN
# =========================
@app.route('/login/google')
def login_google():
    res = supabase.auth.sign_in_with_oauth({
        "provider": "google",
        "options": {
            "redirect_to": "http://127.0.0.1:5000/oauth/callback"
        }
    })
    return redirect(res.url)

# =========================
# GITHUB LOGIN
# =========================
@app.route('/login/github')
def login_github():
    res = supabase.auth.sign_in_with_oauth({
        "provider": "github",
        "options": {
            "redirect_to": "http://127.0.0.1:5000/oauth/callback"
        }
    })
    return redirect(res.url)

# =========================
# OAUTH CALLBACK
# =========================
@app.route('/oauth/callback')
def oauth_callback():
    user = supabase.auth.get_user()

    if user and user.user:
        session['user'] = user.user.email
        return redirect('/dashboard')

    return redirect('/')

# =========================
# DASHBOARD
# =========================
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect('/')

    if request.method == 'POST':
        subject = request.form['subject']
        obtained = int(request.form['obtained'])
        total = int(request.form['total'])

        percentage = (obtained / total) * 100

        if percentage >= 90:
            grade = "A+"
        elif percentage >= 75:
            grade = "A"
        elif percentage >= 60:
            grade = "B"
        elif percentage >= 40:
            grade = "C"
        else:
            grade = "Fail"

        supabase.table("results").insert({
            "username": session['user'],
            "subject": subject,
            "obtained": obtained,
            "total": total,
            "percentage": round(percentage, 2),
            "grade": grade
        }).execute()

    data = supabase.table("results") \
        .select("*") \
        .eq("username", session['user']) \
        .execute()

    return render_template("dashboard.html",
                           username=session['user'],
                           results=data.data)

# =========================
# PDF EXPORT
# =========================
@app.route('/export-pdf')
def export_pdf():
    if 'user' not in session:
        return redirect('/')

    data = supabase.table("results") \
        .select("*") \
        .eq("username", session['user']) \
        .execute()

    rows = ""
    total = 0

    for item in data.data:
        total += item['percentage']
        rows += f"""
        <tr>
            <td>{item['subject']}</td>
            <td>{item['obtained']}/{item['total']}</td>
            <td>{item['percentage']}%</td>
            <td>{item['grade']}</td>
        </tr>
        """

    avg = round(total / len(data.data), 2) if data.data else 0

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial; padding: 30px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ background: #6c63ff; color: white; padding: 10px; }}
            td {{ border: 1px solid #ddd; padding: 10px; text-align: center; }}
        </style>
    </head>
    <body>
        <h2>Student Result Report</h2>
        <p><b>User:</b> {session['user']}</p>

        <table>
            <tr>
                <th>Subject</th>
                <th>Marks</th>
                <th>Percentage</th>
                <th>Grade</th>
            </tr>
            {rows}
        </table>

        <h3>Average: {avg}%</h3>
    </body>
    </html>
    """

    pdf = HTML(string=html).write_pdf()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={session["user"]}.pdf'

    return response

# =========================
# LOGOUT
# =========================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# =========================
if __name__ == '__main__':
    app.run(debug=True)