#db/conn.py
import sqlite3

DB_NAME = 'db/smartin.db'

#fungsi untuk mendapatkan koneksi ke database
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

#fungsi untuk menginisialisasi database dari file SQL
def init_db():
    with open("db/smartin.sql", 'r') as fileSQL:
        smartin = fileSQL.read()

    #membuka koneksi ke database 
    conn = get_connection()
    cursor = conn.cursor()
    #menjalankan semua perintah SQL yang ada di file smartin.sql
    cursor.executescript(smartin)
    conn.commit()
    conn.close()