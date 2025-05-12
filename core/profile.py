from db.conn import get_connection
from core.hash import hash_password, check_password
import core.state
import  sqlite3

def lengkapi_data_user(user_id, role):
    conn = get_connection()
    cursor = conn.cursor()
    
    if role == 'siswa':
        print("\n=== LENGKAPI DATA SISWA ===")
        while True:
            nis = input("Masukkan NIS: ").strip()
            kelas = input("Masukkan Kelas: ").strip()
            
            try:
                cursor.execute(
                    "INSERT INTO siswa(user_id, nis, kelas) VALUES (?,?,?)",
                    (user_id, nis, kelas)
                )
                conn.commit()
                core.state.current_user['siswa_id'] = cursor.lastrowid
                print("Sata siswa berhasil dilengkapi!")
                return
            except sqlite3.IntegrityError as e:
                print(f"NIS sudah terdaftar: {str(e)}")
                conn.rollback()
            except Exception as e:
                print(f"Error: {e}")
                conn.rollback()

    if role == 'guru':
        while True:
            nip = input("Masukan NIP: ").strip()
            
            cursor.execute("SELECT nip FROM guru WHERE nip = ?", (nip,))
            if cursor.fetchone():
                print("NIP sudah terdaftar. Gunakan NIP lain.")
                continue
                
            cursor.execute("SELECT mapel_id, nama_mapel FROM mapel")
            daftar_mapel = cursor.fetchall()
            
            if not daftar_mapel:
                print("\nSistem belum memiliki mata pelajaran")
                print("Silakan hubungi admin untuk menambahkan mapel")
                # Keluar dari proses registrasi
                return  

            print("\nDaftar Mata Pelajaran:")

            for m in daftar_mapel:
                print(f"{m['mapel_id']}. {m['nama_mapel']}")

            try:
                mapel_id = int(input("Masukan ID mapel yang diampu: ").strip())
                # Validasi mapel_id
                if mapel_id not in [m['mapel_id'] for m in daftar_mapel]:
                    print("ID mapel tidak valid")
                    continue
            except ValueError:
                print("Input harus angka")
                continue

            try:
                # Cek apakah user sudah terdaftar sebagai guru
                cursor.execute("SELECT guru_id FROM guru WHERE user_id = ?", (user_id,))
                if cursor.fetchone():
                    print("Anda sudah terdaftar sebagai guru")
                    return
                    
                # Insert data guru
                cursor.execute(
                    "INSERT INTO guru(user_id, nip, mapel_id) VALUES (?,?,?)", 
                    (user_id, nip, mapel_id)
                )
                conn.commit()
                print("Data guru berhasil dilengkapi")
                # Update session
                core.state.current_user = {  #Inisialisasi ulang
                **core.state.current_user,
                'guru_id': cursor.lastrowid,
                'mapel_id': mapel_id
            }
                break
                
            except sqlite3.IntegrityError as e:
                print(f"Gagal: {str(e)}")
                conn.rollback()
            except Exception as e:
                print(f"Error: {e}")
                conn.rollback()
                
        conn.close()
        
def edit_profil(user, new_name=None, new_email=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if new_name:
            user['nama'] = new_name
        if new_email:
            user['email'] = new_email

        cursor.execute(
            "UPDATE user SET nama = ?, email = ? WHERE user_id = ?",
            (user['nama'], user['email'], user['user_id'])
        )
        conn.commit()
        
        # Update state
        core.state.current_user['nama'] = user['nama']
        core.state.current_user['email'] = user['email']
        
        print("Profil berhasil diperbarui!")
        
    except Exception as e:
        print(f"Gagal memperbarui profil: {e}")
    finally:
        conn.close()
        
def ubah_password(user):
    conn = get_connection()
    cursor = conn.cursor()

    current = input("Masukkan password saat ini: ").strip()
    new = input("Masukkan password baru: ").strip()
    confirm = input("Konfirmasi password baru: ").strip()

    cursor.execute("SELECT password FROM user WHERE user_id = ?", (user["user_id"],))
    stored_hash = cursor.fetchone()[0]

    if not check_password(current, stored_hash):
        print("Password saat ini salah.")
        return

    if new != confirm:
        print("Password baru dan konfirmasi tidak cocok.")
        return

    hashed = hash_password(new)
    cursor.execute("UPDATE user SET password = ? WHERE user_id = ?", (hashed, user["user_id"]))
    conn.commit()
    print("Password berhasil diubah.")
    conn.close()