from db.conn import get_connection
import core.state

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
        
        core.state.current_user['nama'] = user['nama']
        core.state.current_user['email'] = user['email']
        
        print("Profil berhasil diperbarui!")
        
    except Exception as e:
        print(f"Gagal memperbarui profil: {e}")
    finally:
        conn.close()