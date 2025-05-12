from db.conn import get_connection

def submit_jawaban(soal_id, siswa_id, jawaban):
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT jawaban, skor, mapel_id FROM soal WHERE soal_id = ?", (soal_id,))
        soal = cursor.fetchone()
        
        # Hitung skor berdasarkan jawaban
        skor = soal['skor'] 
        if jawaban.upper() == soal['jawaban']:
            skor = soal['skor']
        else:
            skor = 0
        
        # Hapus jawaban lama jika ada
        conn.execute("DELETE FROM jawaban WHERE soal_id = ? AND siswa_id = ?", (soal_id, siswa_id))
        
        # Simpan jawaban baru
        conn.execute("""
            INSERT INTO jawaban 
            (soal_id, siswa_id, jawaban, koreksi, mapel_id)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(soal_id, siswa_id) DO UPDATE SET
                jawaban = excluded.jawaban,
                koreksi = excluded.koreksi,
                mapel_id = excluded.mapel_id,
                submit = CURRENT_TIMESTAMP
        """, (soal_id, siswa_id, jawaban.upper(), skor, soal['mapel_id']))
        conn.commit()
        print(f"Jawaban tersimpan! Skor: {skor}/{soal['skor']}")
        
        # Update nilai akhir
        from core.nilai import hitung_nilai_akhir
        hitung_nilai_akhir(siswa_id)
        
    except Exception as e:
        print(f"Gagal menyimpan jawaban: {e}")
    finally:
        conn.close()