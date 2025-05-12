import sqlite3
from db.conn import get_connection
from core.profile import lengkapi_data_user
from core.hash import hash_password, check_password
import core.state
from core.log import log_aktivitas

def register_user(nama, email, password, role):
    conn = get_connection()
    cursor = conn.cursor()
    hashed = hash_password(password)

    try:
        cursor.execute(
            "INSERT INTO user (nama, email, password, role) VALUES (?, ?, ?, ?)", 
            (nama, email, hashed, role)
        )
        conn.commit()
        print("Register berhasil!\n")
        user_id = cursor.lastrowid
        
        from core.log import log_aktivitas
        try:
            log_aktivitas(user_id, f"Registrasi sebagai {role}")
        except Exception as e:
            print(f"[Gagal mencatat log] {e}")
        
        core.state.current_user = {
        "user_id": user_id,
        "nama": nama,
        "email": email,
        "role": role,
        "guru_id": None,
        "siswa_id": None
        }   
        lengkapi_data_user(user_id, role) 
    except sqlite3.IntegrityError:
        print("Email sudah digunakan")
    finally:
        conn.close()

def login_user(email, password):
    conn = get_connection()
    cursor = conn.cursor()
    
    # ========== PERUBAHAN QUERY ==========
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
    # ========== END PERUBAHAN ==========
    
    user = cursor.fetchone()
    conn.close()

    if user:
        if check_password(password, user[3]):
            core.state.current_user = {
                "user_id": user[0],
                "nama": user[1],
                "role": user[2],
                "guru_id": user[4] if user[4] else None,  # Handle NULL dari database
                "siswa_id": user[5] if user[5] else None,  # Handle NULL dari database
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
    