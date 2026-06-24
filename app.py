from flask import Flask, render_template, redirect, request, url_for
from database import init_db, get_db, get_stats

app = Flask(__name__)

init_db()

@app.route("/")
def index():
    stats = get_stats()
    return render_template("index.html", stats=stats)

@app.route("/log", methods=["GET", "POST"])
def log_session():
    if request.method == "POST":
        subject = request.form["subject"]
        duration = int(request.form["duration"])

        conn = get_db()
        conn.execute(
            "INSERT INTO study_sessions (subject, duration) VALUES (?,?)",
            (subject, duration)
        )
        conn.commit()
        conn.close()

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


if __name__ == "__main__":
    app.run(debug=True)