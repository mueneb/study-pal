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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            xp_earned INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_stats (
            id INTEGER PRIMARY KEY,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            streak_freezes INTEGER DEFAULT 0
        )
    """)

    conn.execute("""
        INSERT OR IGNORE INTO user_stats (id, xp, level, streak_freezes)
        VALUES (1, 0, 1, 0)
    """)

    #Achievements table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        unlocked_at DATETIME DEFAULT NULL
    )
    """)
    # Seed all achievements
    achievements = [
    ("First Session", "Log your first study session"),
    ("5 Hours Studied", "Study for a total of 5 hours"),
    ("10 Hours Studied", "Study for a total of 10 hours"),
    ("50 Hours Studied", "Study for a total of 50 hours"),
    ("100 Hours Studied", "Study for a total of 100 hours"),
    ("7-Day Streak", "Achieve a 7 day streak"),
    ("30-Day Streak", "Achieve a 30 day streak"),
    ("First Past Paper", "Complete your first past paper"),
    ("10 Past Papers", "Complete 10 past papers"),
    ("50 Past Papers", "Complete 50 past papers"),
    ]

    for name, description in achievements:
        conn.execute(
        "INSERT OR IGNORE INTO achievements (name, description) SELECT ?, ? WHERE NOT EXISTS (SELECT 1 FROM achievements WHERE name = ?)",
        (name, description, name)
        )

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
def get_stats():
    conn = get_db()

     # Total study time (all time)
    total = conn.execute(
         "SELECT SUM(duration) as total FROM study_sessions"
        ).fetchone()["total"] or 0
    
    # Study time this week
    weekly_total = conn.execute(
        """SELECT SUM(duration) as total FROM study_sessions
        WHERE created_at >= DATE('now', '-6 days')"""
    ).fetchone()["total"] or 0

    # Weekly time broken down by subject
    weekly_by_subject = conn.execute(
        """SELECT subject, SUM(duration) as total FROM study_sessions
        WHERE created_at >= DATE('now', '-6 days')
        GROUP BY subject
        ORDER BY total DESC"""
    ).fetchall()

    conn.close()

    current_streak, longest_streak = get_streaks()

    return {
        "total": total,
        "weekly_total": weekly_total,
        "weekly_by_subject": weekly_by_subject,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
    }

def get_user_stats():
    conn = get_db()

    stats = conn.execute(
    "SELECT * FROM user_stats WHERE id = 1"
    ).fetchone()
    conn.close()
    return stats

def add_xp(minutes):
    xp_earned = minutes
    conn = get_db()
    conn.execute(
        "UPDATE user_stats SET xp = xp + ? WHERE id = 1",
        (xp_earned,)
    )
    
    # Recalculate level
    new_xp = conn.execute(
        "SELECT xp FROM user_stats WHERE id = 1"
    ).fetchone()["xp"]
    new_level = get_level(new_xp)
    conn.execute(
        "UPDATE user_stats SET level = ? WHERE id = 1",
        (new_level,)
    )
    
    conn.commit()
    conn.close()
    return xp_earned

LEVEL_THRESHOLDS = [0, 100, 300, 600, 1000, 1500, 2100, 2800, 3600, 4500]

def get_level(xp):
    level = 1
    for i, threshold in enumerate(LEVEL_THRESHOLDS):
        if xp>=threshold:
            level = i + 1
    return level

def get_xp_progress(xp):
    level = get_level(xp)
    current_threshold = LEVEL_THRESHOLDS[level - 1]

    #if max level
    if level>= len(LEVEL_THRESHOLDS):
        return level, xp, xp, 100
    
    next_threshold = LEVEL_THRESHOLDS[level]
    xp_into_level = xp - current_threshold
    xp_needed = next_threshold - current_threshold
    percentage = int((xp_into_level/xp_needed)*100)

    return level, xp_into_level, xp_needed, percentage

def check_achievements():
    conn = get_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Total minutes studied
    total_minutes = conn.execute(
        "SELECT SUM(duration) as total FROM study_sessions"
    ).fetchone()["total"] or 0
    total_hours = total_minutes / 60

    # Total sessions
    total_sessions = conn.execute(
        "SELECT COUNT(*) as count FROM study_sessions"
    ).fetchone()["count"]

    # Current longest streak
    conn.close()
    _, longest_streak = get_streaks()

    def unlock(name):
        conn2 = get_db()
        conn2.execute(
            """UPDATE achievements SET unlocked_at = ?
            WHERE name = ? AND unlocked_at IS NULL""",
            (now, name)
        )
        conn2.commit()
        conn2.close()

    if total_sessions >= 1:
        unlock("First Session")
    if total_hours >= 5:
        unlock("5 Hours Studied")
    if total_hours >= 10:
        unlock("10 Hours Studied")
    if total_hours >= 50:
        unlock("50 Hours Studied")
    if total_hours >= 100:
        unlock("100 Hours Studied")
    if longest_streak >= 7:
        unlock("7-Day Streak")
    if longest_streak >= 30:
        unlock("30-Day Streak")
