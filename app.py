import os
from flask import Flask, render_template, request, redirect, session
from supabase import create_client

# =========================
# SUPABASE CONNECTION
# =========================
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

supabase = create_client(url, key)

# =========================
# FLASK APP               ← YOU DELETED THIS SECTION
# =========================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret")

# =========================
# LOGIN PAGE
# =========================
@app.route('/', methods=['GET', 'POST'])
def login():

    error = None

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        # CHECK USER FROM SUPABASE

        data = supabase.table("users").select("*").eq(
            "username",
            username
        ).eq(
            "password",
            password
        ).execute()

        if data.data:

            session['user'] = username

            return redirect('/dashboard')

        else:
            error = 'Invalid Username or Password'

    return render_template('login.html', error=error)

# =========================
# SIGNUP PAGE
# =========================

@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        # SAVE USER IN DATABASE

        supabase.table("users").insert({
            "username": username,
            "password": password
        }).execute()

        return redirect('/')

    return render_template('signup.html')

# =========================
# DASHBOARD
# =========================

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():

    if 'user' not in session:
        return redirect('/')

    # SAVE RESULT

    if request.method == 'POST':

        subject = request.form['subject']
        obtained = int(request.form['obtained'])
        total = int(request.form['total'])

        percentage = (obtained / total) * 100

        # GRADE CALCULATION

        if percentage >= 90:
            grade = 'A+'

        elif percentage >= 75:
            grade = 'A'

        elif percentage >= 60:
            grade = 'B'

        elif percentage >= 40:
            grade = 'C'

        else:
            grade = 'Fail'

        # SAVE RESULT TO SUPABASE

        supabase.table("results").insert({
            "username": session['user'],
            "subject": subject,
            "obtained": obtained,
            "total": total,
            "percentage": round(percentage, 2),
            "grade": grade
        }).execute()

    # FETCH USER RESULTS

    data = supabase.table("results").select("*").eq(
        "username",
        session['user']
    ).execute()

    user_results = data.data

    return render_template(
        'dashboard.html',
        username=session['user'],
        results=user_results
    )

# =========================
# CONTACT FORM
# =========================

@app.route('/contact', methods=['POST'])
def contact():

    name = request.form['name']
    email = request.form['email']
    message = request.form['message']

    # SAVE CONTACT MESSAGE

    supabase.table("contacts").insert({
        "name": name,
        "email": email,
        "message": message
    }).execute()

    return redirect('/dashboard')

# =========================
# LOGOUT
# =========================

@app.route('/logout')
def logout():

    session.pop('user', None)

    return redirect('/')

# =========================
# RUN APP
# =========================

if __name__ == '__main__':
    app.run(debug=False)