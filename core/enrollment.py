from db.conn import get_connection

def enroll_mapel(siswa_id):
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT siswa_id FROM siswa WHERE siswa_id = ?", (siswa_id,))
        if not cursor.fetchone():
            print("Data siswa tidak valid")
            return
        while True:
            cursor = conn.execute("""
                SELECT m.mapel_id, m.nama_mapel 
                FROM mapel m
                WHERE NOT EXISTS (
                    SELECT 1 FROM enrollment e 
                    WHERE e.mapel_id = m.mapel_id 
                    AND e.siswa_id = ?
                )""", (siswa_id,))
            
            mapel_list = cursor.fetchall()
            
            if not mapel_list:
                print("\nTidak ada mata pelajaran tersedia untuk di-enroll")
                return

            print("\n=== ENROLL MATA PELAJARAN ===")
            print("0. Kembali ke Menu Utama")
            for idx, mapel in enumerate(mapel_list, 1):
                print(f"{idx}. {mapel['nama_mapel']}")

            pilihan = input("\nPilih mata pelajaran (0 untuk kembali): ")
            if pilihan == '0':
                return
            
            try:
                pilihan = int(pilihan) - 1
                if pilihan < 0 or pilihan >= len(mapel_list):
                    raise ValueError
                
                mapel_id = mapel_list[pilihan]['mapel_id']
                conn.execute("INSERT INTO enrollment VALUES (NULL, ?, ?)", (mapel_id, siswa_id))
                conn.commit()
                print("\nBerhasil enroll mata pelajaran!")
                return
                
            except (ValueError, IndexError):
                print("\nPilihan tidak valid!")
                
    except Exception as e:
        print(f"\nGagal enroll: {e}")
    finally:
        conn.close()