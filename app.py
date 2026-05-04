import os
from flask import Flask, render_template, request, redirect, session, make_response
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
# FLASK APP
# =========================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret")

# =========================
# ADMIN CREDENTIALS
# =========================
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Ayushi123")

# =========================
# LOGIN PAGE
# =========================
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        data = supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
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
        supabase.table("users").insert({"username": username, "password": password}).execute()
        return redirect('/')
    return render_template('signup.html')

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
            grade = 'A+'
        elif percentage >= 75:
            grade = 'A'
        elif percentage >= 60:
            grade = 'B'
        elif percentage >= 40:
            grade = 'C'
        else:
            grade = 'Fail'
        supabase.table("results").insert({
            "username": session['user'],
            "subject": subject,
            "obtained": obtained,
            "total": total,
            "percentage": round(percentage, 2),
            "grade": grade
        }).execute()
    data = supabase.table("results").select("*").eq("username", session['user']).execute()
    user_results = data.data
    return render_template('dashboard.html', username=session['user'], results=user_results)

# =========================
# PDF EXPORT
# =========================
@app.route('/export-pdf')
def export_pdf():
    if 'user' not in session:
        return redirect('/')
    data = supabase.table("results").select("*").eq("username", session['user']).execute()
    user_results = data.data
    rows = ""
    total_percentage = 0
    for item in user_results:
        total_percentage += item['percentage']
        rows += f"""
        <tr>
            <td>{item['subject']}</td>
            <td>{item['obtained']}/{item['total']}</td>
            <td>{item['percentage']}%</td>
            <td>{item['grade']}</td>
        </tr>
        """
    avg = round(total_percentage / len(user_results), 2) if user_results else 0
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial; padding: 30px; }}
            h1 {{ color: #6c63ff; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th {{ background: #6c63ff; color: white; padding: 10px; }}
            td {{ padding: 10px; border: 1px solid #ddd; text-align: center; }}
            tr:nth-child(even) {{ background: #f9f9f9; }}
            .summary {{ margin-top: 20px; font-size: 1.1rem; }}
        </style>
    </head>
    <body>
        <h1>Student Result Report</h1>
        <p><strong>Student:</strong> {session['user']}</p>
        <p><strong>Total Subjects:</strong> {len(user_results)}</p>
        <table>
            <tr>
                <th>Subject</th>
                <th>Marks</th>
                <th>Percentage</th>
                <th>Grade</th>
            </tr>
            {rows}
        </table>
        <div class="summary">
            <p><strong>Average Percentage:</strong> {avg}%</p>
        </div>
    </body>
    </html>
    """
    from weasyprint import HTML
    pdf = HTML(string=html).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={session["user"]}_results.pdf'
    return response

# =========================
# CONTACT FORM
# =========================
@app.route('/contact', methods=['POST'])
def contact():
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']
    supabase.table("contacts").insert({"name": name, "email": email, "message": message}).execute()
    return redirect('/dashboard')

# =========================
# LOGOUT
# =========================
@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('admin', None)
    return redirect('/')

# =========================
# LEADERBOARD
# =========================
@app.route('/leaderboard')
def leaderboard():
    if 'user' not in session:
        return redirect('/')
    data = supabase.table("results").select("*").execute()
    all_results = data.data
    user_stats = {}
    for item in all_results:
        username = item['username']
        if username not in user_stats:
            user_stats[username] = {'total': 0, 'count': 0, 'grades': []}
        user_stats[username]['total'] += item['percentage']
        user_stats[username]['count'] += 1
        user_stats[username]['grades'].append(item['grade'])
    leaderboard = []
    for username, stats in user_stats.items():
        avg = round(stats['total'] / stats['count'], 2)
        leaderboard.append({
            'username': username,
            'average': avg,
            'subjects': stats['count'],
            'is_current': username == session['user']
        })
    leaderboard.sort(key=lambda x: x['average'], reverse=True)
    for i, entry in enumerate(leaderboard):
        entry['rank'] = i + 1
    return render_template('leaderboard.html', leaderboard=leaderboard, username=session['user'])

# =========================
# ADMIN LOGIN
# =========================
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    error = None
    if 'admin' in session:
        return redirect('/admin/dashboard')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = username
            return redirect('/admin/dashboard')
        else:
            error = 'Invalid Admin Credentials'
    return render_template('admin_login.html', error=error)

# =========================
# ADMIN DASHBOARD
# =========================
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/admin')
    users = supabase.table("users").select("*").execute().data
    results = supabase.table("results").select("*").execute().data
    contacts = supabase.table("contacts").select("*").execute().data
    total_students = len(users)
    total_results = len(results)
    user_stats = {}
    for item in results:
        username = item['username']
        if username not in user_stats:
            user_stats[username] = {'total': 0, 'count': 0}
        user_stats[username]['total'] += item['percentage']
        user_stats[username]['count'] += 1
    student_summaries = []
    for username, stats in user_stats.items():
        avg = round(stats['total'] / stats['count'], 2)
        student_summaries.append({
            'username': username,
            'subjects': stats['count'],
            'average': avg
        })
    student_summaries.sort(key=lambda x: x['average'], reverse=True)
    return render_template('admin_dashboard.html',
        users=users,
        results=results,
        contacts=contacts,
        total_students=total_students,
        total_results=total_results,
        student_summaries=student_summaries
    )

# =========================
# ADMIN DELETE RESULT
# =========================
@app.route('/admin/delete-result/<int:result_id>')
def delete_result(result_id):
    if 'admin' not in session:
        return redirect('/admin')
    supabase.table("results").delete().eq("id", result_id).execute()
    return redirect('/admin/dashboard')

# =========================
# ADMIN DELETE USER
# =========================
@app.route('/admin/delete-user/<username>')
def delete_user(username):
    if 'admin' not in session:
        return redirect('/admin')
    supabase.table("users").delete().eq("username", username).execute()
    supabase.table("results").delete().eq("username", username).execute()
    return redirect('/admin/dashboard')

# =========================
# RUN APP
# =========================
if __name__ == '__main__':
    app.run(debug=False)