import os
from flask import Flask, render_template, request, redirect, session, make_response, jsonify
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
# HOME / LOGIN
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
        supabase.table("users").insert({
            "username": request.form['username'],
            "password": request.form['password']
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
def calculate_grade(percentage):
    if percentage >= 90:
        return "A+"
    if percentage >= 75:
        return "A"
    if percentage >= 60:
        return "B"
    if percentage >= 40:
        return "C"
    return "Fail"


def summarize_results(results):
    if not results:
        return {
            "subjects": 0,
            "average": 0,
            "grade": "N/A",
            "total_obtained": 0,
            "total_marks": 0,
            "best": None,
            "weakest": None,
            "passed": 0,
            "needs_attention": 0,
            "target_gap": 75,
            "next_target": 75,
            "message": "Add marks for at least one subject to unlock a full performance summary."
        }

    total_percentage = sum(float(item.get("percentage", 0) or 0) for item in results)
    total_obtained = sum(int(item.get("obtained", 0) or 0) for item in results)
    total_marks = sum(int(item.get("total", 0) or 0) for item in results)
    average = round(total_percentage / len(results), 2)
    best = max(results, key=lambda item: float(item.get("percentage", 0) or 0))
    weakest = min(results, key=lambda item: float(item.get("percentage", 0) or 0))
    passed = sum(1 for item in results if float(item.get("percentage", 0) or 0) >= 40)
    needs_attention = sum(1 for item in results if float(item.get("percentage", 0) or 0) < 60)
    next_target = 90 if average >= 75 else 75 if average >= 60 else 60

    return {
        "subjects": len(results),
        "average": average,
        "grade": calculate_grade(average),
        "total_obtained": total_obtained,
        "total_marks": total_marks,
        "best": best,
        "weakest": weakest,
        "passed": passed,
        "needs_attention": needs_attention,
        "target_gap": max(0, round(next_target - average, 2)),
        "next_target": next_target,
        "message": f"Overall average is {average}% with grade {calculate_grade(average)}."
    }


def build_improvement_plan(summary, details):
    if summary["subjects"] == 0:
        return (
            "First add marks for each subject. After that I can compare subjects, find the weak area, "
            "and create a clear percentage improvement plan."
        )

    weakest = summary["weakest"]
    best = summary["best"]
    target = details.get("targetPercentage") or summary.get("next_target", 75)

    try:
        target = float(target)
    except (TypeError, ValueError):
        target = summary.get("next_target", 75)

    gap = max(0, round(target - summary["average"], 2))
    hours = details.get("studyHours") or "2"

    if gap == 0:
        target_line = "You are already at or above the target. Focus on consistency and full-mark practice."
    else:
        target_line = f"To reach {target:g}%, improve the average by about {gap} percentage points."

    return (
        f"{target_line} Start with {weakest['subject']}, because it is the lowest at {weakest['percentage']}%. "
        f"Keep {best['subject']} strong at {best['percentage']}% by revising it twice a week. "
        f"Use a daily {hours}-hour plan: 50 percent weak-subject practice, 30 percent revision, "
        "and 20 percent test questions. After every test, write down mistakes and repeat those topics first."
    )


def build_assistant_reply(text, results, details):
    summary = summarize_results(results)
    text = (text or "").lower()
    name = details.get("name") or session.get("user", "student")
    student_class = details.get("studentClass") or details.get("class") or "not provided"
    goal = details.get("goal") or "improve percentage"
    focus = details.get("examFocus") or "upcoming exams"

    if summary["subjects"] == 0:
        return (
            f"I have the details for {name}. Class: {student_class}. Goal: {goal}. "
            "No subject marks are saved yet, so please add results and I will explain the full performance."
        )

    best = summary["best"]
    weakest = summary["weakest"]
    improvement_plan = build_improvement_plan(summary, details)

    if any(word in text for word in ["improve", "increase", "percentage", "plan", "study"]):
        return improvement_plan

    if any(word in text for word in ["weak", "low", "worst"]):
        return (
            f"The weakest subject is {weakest['subject']} with {weakest['percentage']}%. "
            f"Give it the first study slot of the day. {improvement_plan}"
        )

    if any(word in text for word in ["best", "strong", "highest"]):
        return (
            f"The strongest subject is {best['subject']} with {best['percentage']}%. "
            "Protect that score with regular revision while you lift the weaker subject."
        )

    if any(word in text for word in ["marks", "result", "summary", "details", "about", "student", "everything", "tell"]):
        return (
            f"Student summary for {name}. Class: {student_class}. Focus: {focus}. Goal: {goal}. "
            f"There are {summary['subjects']} subjects saved. Total marks are "
            f"{summary['total_obtained']} out of {summary['total_marks']}. "
            f"Average is {summary['average']}% with grade {summary['grade']}. "
            f"Best subject is {best['subject']} at {best['percentage']}%. "
            f"Weakest subject is {weakest['subject']} at {weakest['percentage']}%. "
            f"{improvement_plan}"
        )

    return (
        f"Hi {name}. I can tell your full result summary, strongest subject, weakest subject, "
        "or a plan to increase percentage. Try asking: how can I improve my percentage?"
    )


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect('/')

    if request.method == 'POST':
        subject = request.form['subject']
        obtained = int(request.form['obtained'])
        total = int(request.form['total'])

        if total <= 0:
            return redirect('/dashboard')

        percentage = (obtained / total) * 100
        grade = calculate_grade(percentage)

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

    summary = summarize_results(data.data)

    return render_template("dashboard.html",
                           username=session['user'],
                           results=data.data,
                           summary=summary)

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
    <body>
        <h2>Student Result Report</h2>
        <p>User: {session['user']}</p>
        <table border="1">
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
# AI ASSISTANT API
# =========================
@app.route('/assistant', methods=['POST'])
def assistant():
    if 'user' not in session:
        return jsonify({"reply": "Please log in first so I can read the student result data."}), 401

    payload = request.get_json(silent=True) or {}
    text = payload.get("text", "")
    details = payload.get("details", {}) or {}

    data = supabase.table("results") \
        .select("*") \
        .eq("username", session['user']) \
        .execute()

    reply = build_assistant_reply(text, data.data, details)

    return jsonify({"reply": reply})

# =========================
# LEADERBOARD  ← FIXED: moved before if __name__ block
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
            user_stats[username] = {'total': 0, 'count': 0}

        user_stats[username]['total'] += item['percentage']
        user_stats[username]['count'] += 1

    leaderboard_data = []

    for username, stats in user_stats.items():
        avg = round(stats['total'] / stats['count'], 2)
        leaderboard_data.append({
            'username': username,
            'average': avg,
            'subjects': stats['count'],
            'is_current': username == session['user']
        })

    # Sort by highest average first
    leaderboard_data.sort(key=lambda x: x['average'], reverse=True)

    # Add ranks
    for i, entry in enumerate(leaderboard_data):
        entry['rank'] = i + 1

    return render_template('leaderboard.html', leaderboard=leaderboard_data)

# =========================
# RUN APP
# =========================
if __name__ == '__main__':
    app.run(debug=True, host='localhost')
