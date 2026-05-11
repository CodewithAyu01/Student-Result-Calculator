import os
import re
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


def is_admin_logged_in():
    return session.get("admin") is True


def fetch_table_rows(table_name):
    try:
        return supabase.table(table_name).select("*").execute().data or []
    except Exception:
        return []

# =========================
# HOME / LOGIN
# =========================
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.@-]{3,50}$")


def validate_username(username):
    username = (username or "").strip()
    if not username:
        return username, "Username is required."
    if not USERNAME_PATTERN.match(username):
        return username, "Use 3-50 letters, numbers, dots, underscores, @, or hyphens."
    return username, None


def validate_password(password):
    password = password or ""
    if not password:
        return "Password is required."
    if len(password) < 6:
        return "Password must be at least 6 characters."
    return None


@app.route('/', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        username, username_error = validate_username(request.form.get('username'))
        password = request.form.get('password', '')
        password_error = validate_password(password)

        if username_error or password_error:
            error = username_error or password_error
            return render_template("login.html", error=error, username=username)

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


@app.route('/admin', methods=['GET', 'POST'])
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if is_admin_logged_in():
        return redirect('/admin/dashboard')

    error = None

    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect('/admin/dashboard')

        error = "Invalid admin username or password."

    return render_template("admin_login.html", error=error)


@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if not is_admin_logged_in():
        return redirect('/admin/login')

    users = fetch_table_rows("users")
    results = fetch_table_rows("results")
    contacts = fetch_table_rows("contacts")

    user_stats = {}
    for item in results:
        username = item.get("username", "Unknown")
        if username not in user_stats:
            user_stats[username] = {"username": username, "total": 0, "subjects": 0}

        user_stats[username]["total"] += float(item.get("percentage", 0) or 0)
        user_stats[username]["subjects"] += 1

    student_summaries = []
    for stats in user_stats.values():
        average = round(stats["total"] / stats["subjects"], 2) if stats["subjects"] else 0
        student_summaries.append({
            "username": stats["username"],
            "subjects": stats["subjects"],
            "average": average,
            "grade": calculate_grade(average)
        })

    student_summaries.sort(key=lambda item: item["average"], reverse=True)

    return render_template(
        "admin_dashboard.html",
        total_students=len(users),
        total_results=len(results),
        contacts=contacts,
        results=results,
        student_summaries=student_summaries
    )


@app.route('/admin/delete-result/<result_id>', methods=['POST'])
def admin_delete_result(result_id):
    if not is_admin_logged_in():
        return redirect('/admin/login')

    supabase.table("results").delete().eq("id", result_id).execute()
    return redirect('/admin/dashboard')


@app.route('/admin/delete-user/<username>', methods=['POST'])
def admin_delete_user(username):
    if not is_admin_logged_in():
        return redirect('/admin/login')

    supabase.table("results").delete().eq("username", username).execute()
    supabase.table("users").delete().eq("username", username).execute()
    return redirect('/admin/dashboard')

# =========================


# =========================
# GOOGLE LOGIN
# =========================
@app.route('/login/google')
def login_google():
    res = supabase.auth.sign_in_with_oauth({
        "provider": "google",
        "options": {
           "redirect_to": "https://student-result-calculator-g7r0.onrender.com/oauth/callback"
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
            "redirect_to": "https://student-result-calculator-g7r0.onrender.com/oauth/callback"
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

    form_error = None

    if request.method == 'POST':
        subject = (request.form.get('subject') or "").strip()
        obtained_value = request.form.get('obtained', '')
        total_value = request.form.get('total', '')

        try:
            obtained = int(obtained_value)
            total = int(total_value)
        except (TypeError, ValueError):
            form_error = "Marks must be valid whole numbers."
        else:
            if not subject:
                form_error = "Subject name is required."
            elif len(subject) > 50:
                form_error = "Subject name must be 50 characters or fewer."
            elif total <= 0:
                form_error = "Total marks must be greater than zero."
            elif obtained < 0:
                form_error = "Obtained marks cannot be negative."
            elif obtained > total:
                form_error = "Obtained marks cannot be greater than total marks."
            else:
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

                return redirect('/dashboard')

    data = supabase.table("results") \
        .select("*") \
        .eq("username", session['user']) \
        .execute()

    summary = summarize_results(data.data)

    return render_template("dashboard.html",
                           username=session['user'],
                           results=data.data,
                           summary=summary,
                           form_error=form_error)


@app.route('/delete-result/<result_id>', methods=['POST'])
def delete_result(result_id):
    if 'user' not in session:
        return redirect('/')

    supabase.table("results") \
        .delete() \
        .eq("id", result_id) \
        .eq("username", session['user']) \
        .execute()

    return redirect('/dashboard')

# =========================
# PDF EXPORT
# =========================
# =========================
# PDF EXPORT
# =========================
@app.route('/export-pdf')
def export_pdf():
    if 'user' not in session:
        return redirect('/')

    from datetime import datetime

    data = supabase.table("results") \
        .select("*") \
        .eq("username", session['user']) \
        .execute()

    results = data.data
    total = sum(item['percentage'] for item in results)
    avg = round(total / len(results), 2) if results else 0
    grade = calculate_grade(avg)
    now = datetime.now().strftime("%d %B %Y, %I:%M %p")
    passed = sum(1 for r in results if r['percentage'] >= 40)
    failed = len(results) - passed

    # Grade color
    grade_colors = {
        "A+": "#16a34a", "A": "#15803d",
        "B": "#2563eb", "C": "#d97706", "Fail": "#dc2626"
    }
    grade_color = grade_colors.get(grade, "#333")

    # Table rows
    rows = ""
    for item in results:
        g = item['grade']
        g_color = grade_colors.get(g, "#333")
        bar_width = item['percentage']
        rows += f"""
        <tr>
            <td>{item['subject']}</td>
            <td style="text-align:center;">{item['obtained']}/{item['total']}</td>
            <td style="text-align:center;">{item['percentage']}%</td>
            <td style="text-align:center;">
                <span style="
                    display:inline-block;
                    padding:3px 12px;
                    border-radius:999px;
                    background:{g_color}22;
                    color:{g_color};
                    font-weight:800;
                    font-size:12px;
                ">{g}</span>
            </td>
            <td style="min-width:100px;">
                <div style="background:#e2e8f0; border-radius:999px; height:8px; overflow:hidden;">
                    <div style="width:{bar_width}%; height:100%; background:linear-gradient(90deg,#2563eb,#0f9f6e); border-radius:999px;"></div>
                </div>
            </td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}

            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                background: #f6f8fb;
                color: #0f172a;
                padding: 0;
            }}

            /* HEADER */
            .header {{
                background: linear-gradient(135deg, #1e40af, #0f9f6e);
                color: white;
                padding: 36px 40px 28px;
                position: relative;
                overflow: hidden;
            }}
            .header::after {{
                content: '';
                position: absolute;
                right: -40px;
                top: -40px;
                width: 200px;
                height: 200px;
                border-radius: 50%;
                background: rgba(255,255,255,0.08);
            }}
            .header-top {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
            }}
            .portal-name {{
                font-size: 11px;
                font-weight: 900;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                color: #bfdbfe;
                margin-bottom: 8px;
            }}
            .header h1 {{
                font-size: 28px;
                font-weight: 900;
                line-height: 1.1;
            }}
            .header .subtitle {{
                font-size: 13px;
                color: #dbeafe;
                margin-top: 4px;
            }}
            .generated-on {{
                text-align: right;
                font-size: 11px;
                color: #bfdbfe;
                line-height: 1.6;
            }}
            .generated-on strong {{
                display: block;
                font-size: 13px;
                color: white;
            }}

            /* STUDENT INFO BAR */
            .info-bar {{
                background: white;
                border-bottom: 3px solid #e2e8f0;
                padding: 16px 40px;
                display: flex;
                gap: 40px;
                align-items: center;
            }}
            .info-item span {{
                display: block;
                font-size: 10px;
                font-weight: 900;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: #64748b;
                margin-bottom: 3px;
            }}
            .info-item strong {{
                font-size: 14px;
                color: #0f172a;
            }}

            /* MAIN CONTENT */
            .content {{
                padding: 28px 40px;
            }}

            /* SUMMARY CARDS */
            .summary-grid {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 14px;
                margin-bottom: 28px;
            }}
            .summary-card {{
                background: white;
                border-radius: 10px;
                padding: 16px;
                border: 1px solid #e2e8f0;
                text-align: center;
                box-shadow: 0 2px 8px rgba(15,23,42,0.06);
            }}
            .summary-card .label {{
                font-size: 10px;
                font-weight: 900;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: #64748b;
                margin-bottom: 8px;
            }}
            .summary-card .value {{
                font-size: 26px;
                font-weight: 950;
                line-height: 1;
                color: #0f172a;
            }}
            .summary-card .sub {{
                font-size: 11px;
                color: #94a3b8;
                margin-top: 4px;
            }}

            /* SECTION TITLE */
            .section-title {{
                font-size: 11px;
                font-weight: 900;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: #2563eb;
                margin-bottom: 12px;
                padding-bottom: 6px;
                border-bottom: 2px solid #dbeafe;
            }}

            /* TABLE */
            table {{
                width: 100%;
                border-collapse: collapse;
                background: white;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 2px 8px rgba(15,23,42,0.06);
                margin-bottom: 28px;
            }}
            thead tr {{
                background: #1e40af;
                color: white;
            }}
            thead th {{
                padding: 12px 16px;
                font-size: 11px;
                font-weight: 900;
                text-transform: uppercase;
                letter-spacing: 0.07em;
                text-align: left;
            }}
            tbody tr {{
                border-bottom: 1px solid #f1f5f9;
            }}
            tbody tr:last-child {{
                border-bottom: none;
            }}
            tbody tr:nth-child(even) {{
                background: #f8fafc;
            }}
            tbody td {{
                padding: 12px 16px;
                font-size: 13px;
            }}

            /* AVERAGE ROW */
            .average-row {{
                background: #eff6ff !important;
                border-top: 2px solid #2563eb !important;
            }}
            .average-row td {{
                font-weight: 900;
                color: #1e40af;
                font-size: 14px !important;
            }}

            /* PERFORMANCE BAR */
            .perf-section {{
                background: white;
                border-radius: 10px;
                padding: 20px;
                border: 1px solid #e2e8f0;
                box-shadow: 0 2px 8px rgba(15,23,42,0.06);
                margin-bottom: 28px;
            }}
            .perf-row {{
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 10px;
            }}
            .perf-row:last-child {{ margin-bottom: 0; }}
            .perf-subject {{
                width: 100px;
                font-size: 12px;
                font-weight: 700;
                color: #334155;
                flex-shrink: 0;
            }}
            .perf-bar-wrap {{
                flex: 1;
                background: #e2e8f0;
                border-radius: 999px;
                height: 10px;
                overflow: hidden;
            }}
            .perf-bar {{
                height: 100%;
                border-radius: 999px;
                background: linear-gradient(90deg, #2563eb, #0f9f6e);
            }}
            .perf-pct {{
                width: 44px;
                font-size: 12px;
                font-weight: 900;
                color: #0f172a;
                text-align: right;
                flex-shrink: 0;
            }}

            /* FOOTER */
            .footer {{
                background: #0f172a;
                color: #94a3b8;
                padding: 16px 40px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 11px;
            }}
            .footer strong {{ color: white; }}
        </style>
    </head>
    <body>

        <!-- HEADER -->
        <div class="header">
            <div class="header-top">
                <div>
                    <p class="portal-name">🎓 Student Result Portal</p>
                    <h1>Academic Result Report</h1>
                    <p class="subtitle">Official performance summary for the current session</p>
                </div>
                <div class="generated-on">
                    <strong>Generated on</strong>
                    {now}
                </div>
            </div>
        </div>

        <!-- STUDENT INFO BAR -->
        <div class="info-bar">
            <div class="info-item">
                <span>Student Name</span>
                <strong>{session['user']}</strong>
            </div>
            <div class="info-item">
                <span>Total Subjects</span>
                <strong>{len(results)}</strong>
            </div>
            <div class="info-item">
                <span>Subjects Passed</span>
                <strong style="color:#16a34a;">{passed}</strong>
            </div>
            <div class="info-item">
                <span>Needs Improvement</span>
                <strong style="color:#dc2626;">{failed}</strong>
            </div>
            <div class="info-item">
                <span>Export Date</span>
                <strong>{datetime.now().strftime("%d/%m/%Y")}</strong>
            </div>
        </div>

        <div class="content">

            <!-- SUMMARY CARDS -->
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="label">Overall Average</div>
                    <div class="value">{avg}%</div>
                    <div class="sub">across all subjects</div>
                </div>
                <div class="summary-card">
                    <div class="label">Final Grade</div>
                    <div class="value" style="color:{grade_color};">{grade}</div>
                    <div class="sub">overall performance</div>
                </div>
                <div class="summary-card">
                    <div class="label">Subjects Passed</div>
                    <div class="value" style="color:#16a34a;">{passed}</div>
                    <div class="sub">out of {len(results)}</div>
                </div>
                <div class="summary-card">
                    <div class="label">Total Marks</div>
                    <div class="value">{sum(r['obtained'] for r in results)}</div>
                    <div class="sub">out of {sum(r['total'] for r in results)}</div>
                </div>
            </div>

            <!-- RESULTS TABLE -->
            <p class="section-title">📋 Subject-wise Results</p>
            <table>
                <thead>
                    <tr>
                        <th>Subject</th>
                        <th style="text-align:center;">Marks</th>
                        <th style="text-align:center;">Percentage</th>
                        <th style="text-align:center;">Grade</th>
                        <th>Progress</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                    <tr class="average-row">
                        <td>📊 Overall Average</td>
                        <td style="text-align:center;">—</td>
                        <td style="text-align:center;">{avg}%</td>
                        <td style="text-align:center;">{grade}</td>
                        <td>—</td>
                    </tr>
                </tbody>
            </table>

            <!-- PERFORMANCE BARS -->
            <p class="section-title">📈 Performance Overview</p>
            <div class="perf-section">
                {"".join(f'''
                <div class="perf-row">
                    <div class="perf-subject">{r['subject']}</div>
                    <div class="perf-bar-wrap">
                        <div class="perf-bar" style="width:{r['percentage']}%;"></div>
                    </div>
                    <div class="perf-pct">{r['percentage']}%</div>
                </div>
                ''' for r in results)}
            </div>

        </div>

        <!-- FOOTER -->
        <div class="footer">
            <span>🎓 <strong>Student Result Portal</strong> — Confidential Academic Document</span>
            <span>Generated: {now}</span>
        </div>

    </body>
    </html>
    """

    pdf = HTML(string=html).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={session["user"]}_report.pdf'
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
