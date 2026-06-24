import sqlite3
from datetime import datetime, timedelta

def get_db():
    conn = sqlite3.connect("study.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            duration INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
def get_streaks():
    conn = get_db()
    rows = conn.execute(
        "SELECT DATE(created_at) as day FROM study_sessions GROUP BY DATE(created_at) ORDER BY day DESC"
    ).fetchall()
    conn.close()
    
    if not rows:
        return 0, 0

    # Convert to a list of date objects
    dates = [datetime.strptime(row["day"], "%Y-%m-%d").date() for row in rows]

    today = datetime.today().date()
    yesterday = today - timedelta(days=1)

    # Current streak
    current_streak = 0
    if dates[0] == today or dates[0] == yesterday:
        check = dates[0]
        for date in dates:
            if date == check:
                current_streak += 1
                check -= timedelta(days=1)
            else:
                break
    # Longest streak
    longest_streak = 1
    running = 1
    for i in range(1, len(dates)):
        if (dates[i - 1] - dates[i]).days == 1:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 1

    return current_streak, longest_streak

