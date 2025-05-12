import sqlite3
from db.conn import get_connection
import core.state

current_user = None

def register_user(name, email, password, role):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO user (name, email, password, role) VALUES (?, ?, ?, ?)", (name, email, password, role))
        conn.commit()
        print("Registrasi berhasil!\n")
    except sqlite3.IntegrityError:
        print("Email sudah digunakan. Silakan gunakan email lain.\n")
    except sqlite3.Error as e:
        print(f"Terjadi kesalahan database saat registrasi: {e}\n")
    finally:
        conn.close()

def login_user(email, password):
    global current_user
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, name, role FROM user WHERE email = ? AND password = ?", (email, password))
        user_data = cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Terjadi kesalahan database saat login: {e}\n")
        user_data = None
    finally:
        conn.close()

    if user_data:
        current_user = {"id": user_data[0], "name": user_data[1], "role": user_data[2], "email": email}
        print(f"Login berhasil! Selamat datang, {current_user['name']} ({current_user['role']})\n")
        return current_user
    else:
        print("Email atau password salah.\n")
        return None

def edit_profile(new_name, new_password=None):
    global current_user
    if not current_user:
        print("Anda belum login.\n")
        return

    conn = get_connection()
    cursor = conn.cursor()
    
    original_name = current_user['name']
    something_changed = False
    updated_fields_messages = []

    try:
        if new_password and new_name != original_name:
            # Update nama dan password
            cursor.execute("UPDATE user SET name = ?, password = ? WHERE id = ?", (new_name, new_password, current_user['id']))
            current_user['name'] = new_name
            current_user['password'] = new_password
            updated_fields_messages.append("Nama dan password")
            something_changed = True
        elif new_name != original_name:
            # Update hanya nama
            cursor.execute("UPDATE user SET name = ? WHERE id = ?", (new_name, current_user['id']))
            current_user['name'] = new_name
            updated_fields_messages.append("Nama")
            something_changed = True
        elif new_password:
            # Update hanya password
            cursor.execute("UPDATE user SET password = ? WHERE id = ?", (new_password, current_user['id']))
            current_user['password'] = new_password
            updated_fields_messages.append("Password")
            something_changed = True
        
        if something_changed:
            conn.commit()
            print(f"{', '.join(updated_fields_messages)} profil berhasil diperbarui.\n")
        else:
            print("Tidak ada perubahan pada profil.\n")

    except sqlite3.Error as e:
        print(f"Terjadi kesalahan database saat memperbarui profil: {e}\n")
    finally:
        conn.close()


def logout_user():
    if core.state.current_user:
        print(f"\nLogout berhasil. Sampai jumpa {core.state.current_user['nama']}!")
        core.state.current_user = None
    else:
        print("Tidak ada pengguna yang login.")