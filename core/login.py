import sqlite3
from db.conn import get_connection
from core.hash import hash_password, check_password
import core.state
from core.log import log_aktivitas

def register_user(nama, email, password, role, nis=None, kelas=None, nip=None, created_by=None):
    if role in ("guru", "siswa"):
        if not created_by or created_by.get("role") != "admin":
            print("Hanya admin yang dapat membuat akun guru atau siswa.")
            return False

    hashed = hash_password(password)
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Insert ke tabel user
        cursor.execute(
            "INSERT INTO user (nama, email, password, role) VALUES (?, ?, ?, ?)", 
            (nama, email, hashed, role)
        )
        conn.commit()
        user_id = cursor.lastrowid

        # Insert data detail sesuai role
        if role == "siswa":
            if nis is None or kelas is None:
                print("NIS dan kelas harus diisi untuk siswa.")
                return False
            cursor.execute("INSERT INTO siswa (user_id, nis, kelas) VALUES (?, ?, ?)", (user_id, nis, kelas))
        elif role == "guru":
            if nip is None:
                print("NIP harus diisi untuk guru.")
                return False
            cursor.execute("INSERT INTO guru (user_id, nip) VALUES (?, ?)", (user_id, nip))
        conn.commit()

        print(f"Register {role} berhasil! Nama: {nama}")
        try:
            log_aktivitas(user_id, f"Registrasi sebagai {role}")
        except Exception as e:
            print(f"[Gagal mencatat log] {e}")

        return True
    except sqlite3.IntegrityError as e:
        print("Gagal register:", e)
        print("Kemungkinan email atau NIS/NIP sudah digunakan.")
        return False
    finally:
        conn.close()

def admin_create_user(nama, email, password, role, nis=None, kelas=None, nip=None, admin_user=None):
    """
    Fungsi khusus untuk admin membuat user guru atau siswa.
    """
    if not admin_user or admin_user.get("role") != "admin":
        print("Hanya admin yang dapat membuat akun.")
        return False
    
    return register_user(nama, email, password, role, nis, kelas, nip, created_by=admin_user)

def login_user(email, password):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            u.user_id, 
            u.nama, 
            u.role, 
            u.password,
            g.guru_id,
            s.siswa_id
        FROM user u
        LEFT JOIN guru g ON u.user_id = g.user_id
        LEFT JOIN siswa s ON u.user_id = s.user_id
        WHERE u.email = ?
    """, (email,))
    
    user = cursor.fetchone()
    conn.close()

    if user:
        if check_password(password, user[3]):
            core.state.current_user = {
                "user_id": user[0],
                "nama": user[1],
                "role": user[2],
                "guru_id": user[4] if user[4] else None,
                "siswa_id": user[5] if user[5] else None,
                "email": email
            }
            print(f"Login berhasil!")
            print(f"Halo {user[1]}, selamat datang di SMARTIN,\n")
            try:
                log_aktivitas(user[0], "Login")
            except Exception as e:
                print(f"[Gagal mencatat log aktivitas] {e}")
            return core.state.current_user
        else:
            print("Password salah.\n")
            return None
    else:
        print("Email tidak ditemukan.")
        return None