from db.conn import get_connection

def log_aktivitas(user_id, aktivitas):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO log_aktivitas (user_id, aktivitas) VALUES (?, ?)", (user_id, aktivitas)
        )
        conn.commit()
    except Exception as e:
        print(f"[ERROR LOG] {e}")
    finally:
        conn.close()

def lihat_log(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT aktivitas, timestamp FROM log_aktivitas WHERE user_id = ? ORDER BY timestamp DESC LIMIT 50", (user_id,)
    )
    #menggunakan fetchall bukan fetchone karena dibatasi baris yang ditampilkannya yaitu 50
    logs = cursor.fetchall()
    conn.close()

    print("\nRiwayat aktivitas terakhir: ")
    for log in logs:
        print(f"-[{log[1]}] {log[0]}")