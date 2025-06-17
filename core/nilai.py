#core/nilai.py
from db.conn import get_connection

def hitung_nilai_akhir(siswa_id):
    conn = get_connection()
    try:
        # Hitung total nilai per mapel
        nilai_mapel_rows = conn.execute("""
            SELECT j.mapel_id, SUM(j.koreksi) as total_skor_diperoleh
            FROM jawaban j
            WHERE j.siswa_id = ? AND j.koreksi IS NOT NULL
            GROUP BY j.mapel_id
        """, (siswa_id,))
        
        for row_nilai in nilai_mapel_rows:
            mapel_id = row_nilai['mapel_id']
            skor_diperoleh_mapel = row_nilai['total_skor_diperoleh'] if row_nilai['total_skor_diperoleh'] is not None else 0

            # Dapatkan total skor maksimal untuk mapel ini
            skor_maks_row = conn.execute(
                "SELECT SUM(skor) AS total_skor_max_mapel FROM soal WHERE mapel_id = ?",
                (mapel_id,)
            ).fetchone()
            skor_maksimal_mapel = skor_maks_row['total_skor_max_mapel'] if skor_maks_row and skor_maks_row['total_skor_max_mapel'] is not None else 0
            
            indeks_mapel = hitung_indeks(skor_diperoleh_mapel, skor_maksimal_mapel)
            # Update tabel nilai
            conn.execute("""
                INSERT OR REPLACE INTO nilai 
                (siswa_id, mapel_id, skor, indeks)
                VALUES (?, ?, ?, ?)
            """, (siswa_id, mapel_id, skor_diperoleh_mapel, indeks_mapel))
        
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

def hitung_indeks(skor_diperoleh, skor_maksimal):
    if skor_maksimal is None or skor_maksimal == 0:
        return 'N/A' # Tidak ada skor maksimal, tidak bisa hitung persentase
    if skor_diperoleh is None:
        skor_diperoleh = 0

    persentase = (skor_diperoleh / skor_maksimal) * 100
    
    if persentase >= 90: 
        return 'A'
    elif persentase >= 80: 
        return 'B'
    elif persentase >= 70: 
        return 'C'
    elif persentase >= 60: 
        return 'D'
    else: 
        return 'E'