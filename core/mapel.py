#core/mapel.py
import sqlite3
from db.conn import get_connection
import core.state
from core.log import log_aktivitas

def buat_mapel():
    conn = get_connection()
    try:
        nama_mapel = input("Nama mata pelajaran: ").strip()
        conn.execute(
            "INSERT INTO mapel (nama_mapel) VALUES (?)", (nama_mapel,)
        )
        conn.commit()
        print("Mata pelajaran berhasil dibuat!")
        
        log_aktivitas(core.state.current_user['user_id'], f"Membuat mapel {nama_mapel}")
        
    except sqlite3.IntegrityError:
        print("Nama mata pelajaran sudah ada")
    except Exception as e:
        print(f"Gagal membuat mata pelajaran: {e}")
    finally:
        conn.close()

def get_mapel_by_guru(guru_id):
    "Mendapatkan daftar mapel yang diampu guru"
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT m.mapel_id, m.nama_mapel FROM mapel m JOIN guru g ON m.mapel_id = g.mapel_id WHERE g.guru_id = ?", (guru_id,))
        return cursor.fetchall()
    finally:
        conn.close()