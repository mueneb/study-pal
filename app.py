from flask import Flask, render_template, redirect, request, url_for
from database import init_db, get_db, get_stats, get_user_stats, add_xp, get_xp_progress, check_achievements, buy_streak_freeze, get_goal_progress, get_heatmap_data
import json
from datetime import datetime, timedelta, date

app = Flask(__name__)

init_db()

@app.route("/")
def index():
    stats = get_stats()
    user = get_user_stats()
    level, xp_into_level, xp_needed, percentage = get_xp_progress(user["xp"])
    message = request.args.get("message")
    return render_template("index.html", stats=stats, user=user, level=level, xp_into_level=xp_into_level, xp_needed=xp_needed, percentage=percentage, message=message)

@app.route("/log", methods=["GET", "POST"])
def log_session():
    if request.method == "POST":
        subject = request.form["subject"]
        duration = int(request.form["duration"])

        xp_earned = duration

        conn = get_db()
        conn.execute(
            "INSERT INTO study_sessions (subject, duration, xp_earned) VALUES (?,?,?)",
            (subject, duration, xp_earned)
        )
        conn.commit()
        conn.close()

        add_xp(duration)
        check_achievements()

        return redirect(url_for("index"))
    
    return render_template("log.html")

@app.route("/history")
def history():
    conn = get_db()
    sessions = conn.execute(
        "SELECT * FROM study_sessions ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    
    return render_template("history.html", sessions=sessions)

@app.route("/achievements")
def achievements():
    conn = get_db()
    all_achievements = conn.execute(
        "SELECT * FROM achievements ORDER BY unlocked_at ASC"
    ).fetchall()
    conn.close()
    return render_template("achievements.html", achievements=all_achievements)

@app.route("/buy-freeze", methods=["POST"])
def buy_freeze():
    success, message = buy_streak_freeze()
    return redirect(url_for("index", message=message))

@app.route("/papers", methods=["GET", "POST"])
def papers():
    if request.method == "POST":
        # Handle paper submission logic here
        subject = request.form["subject"]
        paper_name = request.form["paper_name"]
        score = int(request.form["score"])
        max_score = int(request.form["max_score"])

        conn = get_db()
        conn.execute(
            "INSERT INTO past_papers (subject, paper_name, score, max_score) VALUES (?,?,?,?)",
            (subject, paper_name, score, max_score)
        )

        conn.commit()
        conn.close()

        check_achievements()
        return redirect(url_for("papers"))
    
    conn = get_db()
    all_papers = conn.execute(
        "SELECT * FROM past_papers ORDER BY completed_at DESC"
    ).fetchall()

    by_subject = conn.execute(
        """SELECT subject, COUNT(*) as count,
        ROUND(AVG(CAST(score AS REAL) / max_score * 100), 1) as avg_percentage
        FROM past_papers GROUP BY subject"""
    ).fetchall()
    conn.close()

    return render_template("papers.html", papers=all_papers, by_subject=by_subject)

@app.route("/goals", methods=["GET", "POST"])
def goals():
    if request.method == "POST":
        goal_type = request.form["type"]
        subject = request.form["subject"]
        target = int(request.form["target"])
        deadline = request.form["deadline"]

        conn = get_db()
        conn.execute(
            "INSERT INTO goals (type, subject, target, deadline) VALUES (?, ?, ?, ?)",
            (goal_type, subject, target, deadline)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("goals"))

    conn = get_db()
    all_goals = conn.execute(
        "SELECT * FROM goals ORDER BY deadline ASC"
    ).fetchall()
    conn.close()

    goals_with_progress = []
    for goal in all_goals:
        progress = get_goal_progress(goal)
        goals_with_progress.append({"goal": goal, "progress": progress})

    return render_template("goals.html", goals=goals_with_progress)

@app.route("/heatmap")
def heatmap():
    data = get_heatmap_data()
    
    # Build list of last 365 days
    today = date.today()
    days = []
    for i in range(364, -1, -1):
        d = today - timedelta(days=i)
        day_str = d.strftime("%Y-%m-%d")
        days.append({
            "date": day_str,
            "minutes": data.get(day_str, 0),
            "weekday": d.weekday()  # 0 = Monday, 6 = Sunday
        })

    return render_template("heatmap.html", days=json.dumps(days))

if __name__ == "__main__":
    app.run(debug=True)