from db.conn import get_connection

def hitung_nilai_akhir(siswa_id):
    conn = get_connection()
    try:
        # Hitung total nilai per mapel
        cursor = conn.execute("""
            SELECT j.mapel_id, SUM(j.koreksi) as total
            FROM jawaban j
            JOIN soal s ON j.soal_id = s.soal_id
            WHERE j.siswa_id = ?
            GROUP BY s.mapel_id
        """, (siswa_id,))
        
        for row in cursor.fetchall():
            # Update tabel nilai
            conn.execute("""
                INSERT OR REPLACE INTO nilai 
                (siswa_id, mapel_id, skor, indeks)
                VALUES (?, ?, ?, ?)
            """, (siswa_id, row['mapel_id'], row['total'], hitung_indeks(row['total'])))
        
        conn.commit()
    finally:
        conn.close()

def tampilkan_nilai(siswa_id):
    conn = get_connection()
    try:
        cursor = conn.execute("""
            SELECT m.nama_mapel, n.skor, n.indeks
            FROM nilai n
            JOIN mapel m ON n.mapel_id = m.mapel_id
            WHERE n.siswa_id = ?
        """, (siswa_id,))
        
        print("\n=== HASIL NILAI AKHIR ===")
        for row in cursor.fetchall():
            print(f"Mata Pelajaran: {row['nama_mapel']}")
            print(f"Total Skor: {row['skor']}")
            print(f"Indeks Nilai: {row['indeks']}\n")
    finally:
        conn.close()

def hitung_indeks(total):
    if total >= 90: 
        return 'A'
    elif total >= 80: 
        return 'B'
    elif total >= 70: 
        return 'C'
    elif total >= 60: 
        return 'D'
    else: 
        return 'E'