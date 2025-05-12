from db.conn import get_connection
from core.log import lihat_log
from core.enrollment import enroll_mapel
from core.jawaban import submit_jawaban
from core.nilai import hitung_nilai_akhir, hitung_indeks
from core.profile import edit_profil, ubah_password
from db.conn import get_connection
from core.auth import logout_user  # Ganti ini


def dashboard_siswa(user):
    while True:
        print(f"\n{'='*20} DASHBOARD SISWA {'='*20}")
        print(f"Selamat datang, {user['nama']}!")
        print("\nMenu Utama:")
        print("1. Lihat Profil")
        print("2. Enroll Mata Pelajaran")
        print("3. Kerjakan Soal")
        print("4. Lihat Nilai")
        print("5. Lihat Log Aktivitas")
        print("6. Logout")
        
        pilihan = input("Pilih menu: ").strip()
        
        if pilihan == '1':
            menu_profil_siswa(user)
        elif pilihan == '2':
            enroll_mapel(user['siswa_id'])
        elif pilihan == '3':
            kerjakan_soal(user)
        elif pilihan == '4':
            tampilkan_nilai_siswa(user['siswa_id'])
        elif pilihan == '5':
            lihat_log(user['user_id'])
        elif pilihan == '6':
            logout_user()
            return False

def menu_profil_siswa(user):
    while True:
        conn = get_connection()
        try:
            cursor = conn.execute("""
                SELECT 
                    u.nama,
                    u.email,
                    s.nis,
                    s.kelas
                FROM user u
                LEFT JOIN siswa s ON u.user_id = s.user_id
                WHERE u.user_id = ?
            """, (user['user_id'],))
            
            profile = cursor.fetchone()
            
            if not profile:
                print("Data siswa tidak ditemukan")
                return

            print("\n=== PROFIL SISWA ===")
            print(f"Nama    : {profile['nama']}")
            print(f"Email   : {profile['email']}")
            print(f"NIS     : {profile['nis'] or 'Belum diisi'}")
            print(f"Kelas   : {profile['kelas'] or 'Belum diisi'}")
            
            print("\n1. Edit Nama")
            print("2. Ubah Password")
            print("3. Kembali")
            
            pilihan = input("Pilih menu: ").strip()
            
            if pilihan == '1':
                new_name = input("Nama baru: ").strip()
                if edit_profil(user, new_name=new_name):
                    print("Perubahan berhasil! Memuat ulang data...")
                    break
            elif pilihan == '2':
                ubah_password(user)
            elif pilihan == '3':
                break
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            conn.close()
        
def tampilkan_data_siswa(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT nis, kelas FROM siswa WHERE user_id = ?", 
        (user_id,)
    )
    data = cursor.fetchone()
    conn.close()

    if data:
        print(f" - NIS : {data[0]}")
        print(f" - Kelas : {data[1]}")
    else:
        print("Data siswa belum dilengkapi")
        
def tampilkan_nilai_siswa(siswa_id):
    conn = get_connection()
    try:
        # Daftar mapel yang di-enroll
        cursor = conn.execute("""
            SELECT m.mapel_id, m.nama_mapel 
            FROM enrollment e
            JOIN mapel m ON e.mapel_id = m.mapel_id
            WHERE e.siswa_id = ?
        """, (siswa_id,))
        mapel_list = cursor.fetchall()
        
        if not mapel_list:
            print("\nBelum enroll mata pelajaran")
            return

        print("\n=== PILIH MATA PELAJARAN ===")
        for idx, mapel in enumerate(mapel_list, 1):
            print(f"{idx}. {mapel['nama_mapel']}")
        print("0. Kembali")
            
        pilihan = input("\nPilih mata pelajaran: ").strip()
        
        # Validasi input
        if not pilihan.isdigit():
            print("\nInput harus berupa angka!")
            return
            
        pilihan = int(pilihan)
        if pilihan == 0:
            return
            
        if pilihan < 1 or pilihan > len(mapel_list):
            print("\nNomor tidak valid!")
            return

        mapel_id = mapel_list[pilihan-1]['mapel_id']
        
        cursor = conn.execute("""
            SELECT 
                j.soal_id,
                s.pertanyaan,
                j.jawaban AS jawaban_siswa,
                s.jawaban AS jawaban_benar,
                j.koreksi,
                s.skor AS skor_maks
            FROM jawaban j
            JOIN soal s ON j.soal_id = s.soal_id
            WHERE j.siswa_id = ? AND j.mapel_id = ?
            GROUP BY j.soal_id
        """, (siswa_id, mapel_id))
        
        results = cursor.fetchall()
        
        if not results:
            print("\nBelum ada nilai untuk mapel ini")
            return

        print("\n=== DETAIL NILAI ===")
        total_skor = 0
        total_maksimal = 0
        
        for idx, row in enumerate(results, 1):
            total_skor += row['koreksi']
            total_maksimal += row['skor_maks']
            
            print(f"\nSoal {idx}: {row['pertanyaan']}")
            print(f"Jawaban Anda: {row['jawaban_siswa']}")
            print(f"Jawaban Benar: {row['jawaban_benar']}")
            print(f"Skor: {row['koreksi']}/{row['skor_maks']}")

        print(f"\nTotal Skor: {total_skor}/{total_maksimal}")
        print(f"Indeks Nilai: {hitung_indeks(total_skor)}")
        
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        conn.close()
        
def kerjakan_soal(user):
    conn = get_connection()
    try:
        
        cursor = conn.execute("SELECT siswa_id FROM siswa WHERE siswa_id = ?", (user['siswa_id'],))
        if not cursor.fetchone():
            print("Data siswa tidak valid")
            return
        
        # Daftar mapel yang di-enroll
        cursor = conn.execute("""
            SELECT m.mapel_id, m.nama_mapel
            FROM enrollment e
            JOIN mapel m ON e.mapel_id = m.mapel_id
            WHERE e.siswa_id = ?
        """, (user['siswa_id'],))
        
        mapel_list = cursor.fetchall()
        
        if not mapel_list:
            print("\nBelum enroll mata pelajaran")
            return

        print("\n=== PILIH MATA PELAJARAN ===")
        for idx, mapel in enumerate(mapel_list, 1):
            print(f"{idx}. {mapel['nama_mapel']}")
        print("0. Kembali")
            
        pilihan = input("\nPilih mata pelajaran: ").strip()
        if pilihan == '0':
            return
            
        try:
            pilihan = int(pilihan) - 1
            mapel_id = mapel_list[pilihan]['mapel_id']
            
            # Cek apakah sudah pernah mengerjakan
            cursor = conn.execute("""
                SELECT COUNT(*) FROM jawaban j
                JOIN soal s ON j.soal_id = s.soal_id
                WHERE j.siswa_id = ? AND s.mapel_id = ?
            """, (user['siswa_id'], mapel_id))
            
            if cursor.fetchone()[0] > 0:
                konfirmasi = input("\nAnda sudah mengerjakan soal ini. Ulang? (y/t): ").lower()
                if konfirmasi != 'y':
                    return
                # Hapus jawaban lama
                conn.execute("""
                    DELETE FROM jawaban
                    WHERE siswa_id = ? AND soal_id IN (
                        SELECT soal_id FROM soal WHERE mapel_id = ?
                    )
                """, (user['siswa_id'], mapel_id))
                conn.commit()

            # Ambil soal
            cursor = conn.execute("""
                SELECT * FROM soal
                WHERE mapel_id = ?
                ORDER BY soal_id
            """, (mapel_id,))
            soal_list = cursor.fetchall()
            
            if not soal_list:
                print("\nBelum ada soal untuk mapel ini")
                return

            print("\n=== MULAI MENGERJAKAN SOAL ===")
            for soal in soal_list:
                print(f"\nSoal: {soal['pertanyaan']}")
                print(f"A. {soal['opsi_a']}")
                print(f"B. {soal['opsi_b']}")
                print(f"C. {soal['opsi_c']}")
                print(f"D. {soal['opsi_d']}")
                
                while True:
                    jawaban = input("Jawaban Anda (A/B/C/D): ").strip().upper()
                    if jawaban in ['A','B','C','D']:
                        break
                    print("Input tidak valid!")
                
                submit_jawaban(soal['soal_id'], user['siswa_id'], jawaban)
            
            hitung_nilai_akhir(user['siswa_id'])
            print("\nAnda telah menyelesaikan semua soal!")

        except (ValueError, IndexError):
            print("\nPilihan tidak valid!")
            
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        conn.close()