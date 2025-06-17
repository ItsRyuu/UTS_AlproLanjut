from db.conn import get_connection

def enroll_mapel(siswa_id):
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT siswa_id FROM siswa WHERE siswa_id = ?", (siswa_id,))
        if not cursor.fetchone():
            raise ValueError("Data siswa tidak valid")

        cursor = conn.execute("""
            SELECT m.mapel_id, m.nama_mapel
            FROM mapel m
            WHERE NOT EXISTS (
                SELECT 1 FROM enrollment e
                WHERE e.mapel_id = m.mapel_id
                AND e.siswa_id = ?
            )
        """, (siswa_id,))
        
        mapel_list = cursor.fetchall()

        if not mapel_list:
            raise ValueError("Tidak ada mata pelajaran tersedia untuk di-enroll")

        return mapel_list  # Mengembalikan daftar mata pelajaran yang tersedia

    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        conn.close()

def enroll_siswa(mapel_id, siswa_id):
    conn = get_connection()
    try:
        # Menambahkan enrollment baru
        conn.execute("INSERT INTO enrollment (mapel_id, siswa_id) VALUES (?, ?)", (mapel_id, siswa_id))
        conn.commit()
    except Exception as e:
        print(f"Error enrolling siswa: {e}")
    finally:
        conn.close()

def get_enrolled_mapel(siswa_id):
    conn = get_connection()
    try:
        cursor = conn.execute("""
            SELECT m.mapel_id, m.nama_mapel
            FROM mapel m
            JOIN enrollment e ON m.mapel_id = e.mapel_id
            WHERE e.siswa_id = ?
        """, (siswa_id,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error getting enrolled mapel: {e}")
        return None
    finally:
        conn.close()
