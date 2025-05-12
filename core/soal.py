from db.conn import get_connection

def buat_soal(mapel_id, guru_id):
    conn = get_connection()
    try:
        pertanyaan = input("Pertanyaan: ").strip()
        opsi_a = input("Opsi A: ").strip()
        opsi_b = input("Opsi B: ").strip()
        opsi_c = input("Opsi C: ").strip()
        opsi_d = input("Opsi D: ").strip()
        jawaban = input("Jawaban benar (A/B/C/D): ").strip().upper()
        skor = int(input("Skor soal: ").strip()) 
        
        conn.execute("""
            INSERT INTO soal 
            (mapel_id, guru_id, pertanyaan, opsi_a, opsi_b, opsi_c, opsi_d, jawaban, skor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (mapel_id, guru_id, pertanyaan, opsi_a, opsi_b, opsi_c, opsi_d, jawaban, skor))
        
        conn.commit()
        print("Soal berhasil ditambahkan!")
        
    except Exception as e:
        print(f"Gagal membuat soal: {e}")
    finally:
        conn.close()

def edit_soal(soal_id):
    conn = get_connection()
    try:
        soal = conn.execute("SELECT * FROM soal WHERE soal_id = ?", (soal_id,)).fetchone()
        
        print("\n=== EDIT SOAL ===")
        pertanyaan = input(f"Pertanyaan baru [{soal['pertanyaan']}]: ").strip() or soal['pertanyaan']
        opsi_a = input(f"Opsi A baru [{soal['opsi_a']}]: ").strip() or soal['opsi_a']
        opsi_b = input(f"Opsi B baru [{soal['opsi_b']}]: ").strip() or soal['opsi_b']
        opsi_c = input(f"Opsi C baru [{soal['opsi_c']}]: ").strip() or soal['opsi_c']
        opsi_d = input(f"Opsi D baru [{soal['opsi_d']}]: ").strip() or soal['opsi_d']
        jawaban = input(f"Jawaban benar [{soal['jawaban']}]: ").strip().upper() or soal['jawaban']
        skor = input(f"Skor soal [{soal['skor']}]: ").strip() or soal['skor']

        conn.execute("""
            UPDATE soal SET
            pertanyaan = ?,
            opsi_a = ?,
            opsi_b = ?,
            opsi_c = ?,
            opsi_d = ?,
            jawaban = ?,
            skor = ? 
            WHERE soal_id = ?
        """, (pertanyaan, opsi_a, opsi_b, opsi_c, opsi_d, jawaban, skor, soal_id))
        conn.commit()
        
        print("Soal berhasil diupdate!")
        
    except Exception as e:
        print(f"Gagal edit soal: {e}")
    finally:
        conn.close()

def hapus_soal(soal_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM soal WHERE soal_id = ?", (soal_id,))
        conn.commit()
        print("Soal berhasil dihapus!")
    except Exception as e:
        print(f"Gagal hapus soal: {e}")
    finally:
        conn.close()

def get_soal_by_mapel(mapel_id):
    conn = get_connection()
    try:
        cursor = conn.execute("""
            SELECT * FROM soal 
            WHERE mapel_id = ?
        """, (mapel_id,))
        return cursor.fetchall()
    finally:
        conn.close()