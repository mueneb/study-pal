from flask import Flask, render_template, redirect, request, url_for
from database import init_db, get_db, get_stats, get_user_stats, add_xp, get_xp_progress, check_achievements

app = Flask(__name__)

init_db()

@app.route("/")
def index():
    stats = get_stats()
    user = get_user_stats()
    level, xp_into_level, xp_needed, percentage = get_xp_progress(user["xp"])
    return render_template("index.html", stats=stats, user=user, level=level, xp_into_level=xp_into_level, xp_needed=xp_needed, percentage=percentage)

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


if __name__ == "__main__":
    app.run(debug=True)