#core/log.py
from db.conn import get_connection
from datetime import datetime

def log_aktivitas(user_id, aktivitas):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        timestamp = datetime.now()
        cursor.execute(
            "INSERT INTO log_aktivitas (user_id, aktivitas, timestamp) VALUES (?, ?, ?)", 
            (user_id, aktivitas, timestamp)
        )
        conn.commit()
    except Exception as e:
        print(f"[ERROR LOG] {e}")
    finally:
        conn.close()

def lihat_log(user_id):
    conn = get_connection()
    try:
        cursor = conn.execute(
            """SELECT aktivitas, timestamp
            FROM log_aktivitas  # Pastikan nama tabel sesuai
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 50""",
            (user_id,)
        )
        return cursor.fetchall()
    finally:
        conn.close()
