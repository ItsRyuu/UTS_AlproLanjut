from db.conn import get_connection
from core.log import lihat_log
from core.soal import buat_soal, edit_soal, hapus_soal
from core.profile import edit_profil, ubah_password
from db.conn import get_connection
from core.auth import logout_user

def dashboard_guru(user):
    
    while True:
        print(f"\n{'='*20} DASHBOARD GURU {'='*20}")
        print(f"Selamat datang, {user['nama']}!")
        
        if not user.get('guru_id'):
            print("\nAnda belum terdaftar sebagai guru")
            print("1. Lengkapi data guru")
            print("0. Logout")
            
            pilihan = input("Pilih: ").strip()
            if pilihan == '1':
                from core.profile import lengkapi_data_user
                lengkapi_data_user(user['user_id'], 'guru')
                return
            elif pilihan == '0':
                return False
            continue
                
        print("\nMenu Utama:")
        print("1. Lihat Profil")
        print("2. Kelola Soal")
        print("3. Lihat Nilai Siswa")
        print("4. Lihat Log Aktivitas")
        print("5. Logout")
        
        pilihan = input("Pilih menu: ").strip()
        
        if pilihan == '1':
            menu_profil_guru(user)
        elif pilihan == '2':
            kelola_soal(user)
        elif pilihan == '3':
            tampilkan_statistik_nilai(user['guru_id'])
        elif pilihan == '4':
            lihat_log(user['user_id'])
        elif pilihan == '5':
            logout_user()
            return False
        else:
            print("Pilihan tidak valid!")

def menu_profil_guru(user):
    while True:
        conn = get_connection()
        try:
            cursor = conn.execute("""
                SELECT 
                    u.nama,
                    u.email,
                    g.nip,
                    m.nama_mapel
                FROM user u
                LEFT JOIN guru g ON u.user_id = g.user_id
                LEFT JOIN mapel m ON g.mapel_id = m.mapel_id
                WHERE u.user_id = ?
            """, (user['user_id'],))
            profile = cursor.fetchone()

            if not profile:
                print("Data profil tidak ditemukan")
                return

            print("\n=== PROFIL GURU ===")
            print(f"Nama      : {profile['nama']}")
            print(f"Email     : {profile['email']}")
            print(f"NIP       : {profile['nip'] or 'Belum dilengkapi'}")
            print(f"Mata Ajar : {profile['nama_mapel'] or 'Belum dipilih'}")
            
            print("\n1. Edit Nama")
            print("2. Ubah Password")
            print("3. Kembali")
            
            pilihan = input("Pilih menu: ").strip()
            
            if pilihan == '1':
                new_name = input("Nama baru: ").strip()
                if edit_profil(user, new_name=new_name):
                    # Paksa refresh data dengan keluar dari loop
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
        
def tampilkan_statistik_nilai(guru_id):
    conn = get_connection()
    try:
        # Dapatkan mapel yang diampu
        cursor = conn.execute("""
            SELECT m.mapel_id, m.nama_mapel 
            FROM mapel m
            JOIN guru g ON m.mapel_id = g.mapel_id
            WHERE g.guru_id = ?
        """, (guru_id,))
        
        mapel_list = cursor.fetchall()
        
        if not mapel_list:
            print("\nAnda belum mengampu mata pelajaran apapun")
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
            
            # Ambil statistik nilai
            cursor = conn.execute("""
                SELECT 
                    COUNT(DISTINCT n.siswa_id) AS jumlah_siswa,
                    AVG(n.skor) AS rata_rata,
                    MAX(n.skor) AS nilai_tertinggi,
                    MIN(n.skor) AS nilai_terendah,
                    n.indeks,
                    COUNT(n.indeks) AS total_indeks
                FROM nilai n
                WHERE n.mapel_id = ?
                GROUP BY n.indeks
            """, (mapel_id,))
            
            results = cursor.fetchall()
            
            if not results:
                print("\nBelum ada nilai untuk mapel ini")
                return

            print(f"\n=== STATISTIK NILAI {mapel_list[pilihan]['nama_mapel']} ===")
            print(f"Jumlah Siswa: {results[0]['jumlah_siswa']}")
            print(f"Rata-rata Kelas: {results[0]['rata_rata']:.2f}")
            print(f"Nilai Tertinggi: {results[0]['nilai_tertinggi']}")
            print(f"Nilai Terendah: {results[0]['nilai_terendah']}")
            
            print("\nDistribusi Indeks:")
            for row in results:
                print(f"{row['indeks']}: {row['total_indeks']} siswa")
                
        except (ValueError, IndexError):
            print("\nPilihan tidak valid!")
            
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        conn.close()

def kelola_soal(user):
    conn = get_connection()
    try:
        # Dapatkan mapel yang diampu
        cursor = conn.execute("""
            SELECT m.mapel_id, m.nama_mapel 
            FROM mapel m
            JOIN guru g ON m.mapel_id = g.mapel_id
            WHERE g.guru_id = ?
        """, (user['guru_id'],))
        
        mapel_list = cursor.fetchall()
        
        if not mapel_list:
            print("\nAnda belum mengampu mata pelajaran apapun")
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
            
            while True:
                print(f"\n=== KELOLA SOAL {mapel_list[pilihan]['nama_mapel']} ===")
                print("1. Buat Soal Baru")
                print("2. Edit Soal")
                print("3. Hapus Soal")
                print("4. Lihat Daftar Soal")
                print("0. Kembali")
                
                sub_pilihan = input("\nPilih menu: ").strip()
                
                if sub_pilihan == '1':
                    buat_soal(mapel_id, user['guru_id'])
                elif sub_pilihan == '2':
                    list_soal(mapel_id, mode='edit')
                elif sub_pilihan == '3':
                    list_soal(mapel_id, mode='hapus')
                elif sub_pilihan == '4':
                    list_soal(mapel_id)
                elif sub_pilihan == '0':
                    break
                else:
                    print("\nPilihan tidak valid!")
                    
        except (ValueError, IndexError):
            print("\nPilihan tidak valid!")
            
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        conn.close()

def list_soal(mapel_id, mode=None):
    conn = get_connection()
    try:
        cursor = conn.execute("""
            SELECT * FROM soal 
            WHERE mapel_id = ?
            ORDER BY soal_id
        """, (mapel_id,))
        soal_list = cursor.fetchall()
        
        if not soal_list:
            print("\nBelum ada soal untuk mapel ini")
            return
            
        print("\n=== DAFTAR SOAL ===")
        for idx, soal in enumerate(soal_list, 1):
            print(f"{idx}. {soal['pertanyaan'][:50]}...")
            
        if mode == 'edit':
            pilihan = input("\nPilih nomor soal yang akan diedit: ").strip()
            try:
                pilihan = int(pilihan) - 1
                edit_soal(soal_list[pilihan]['soal_id'])
            except (ValueError, IndexError):
                print("\nInput tidak valid!")
                
        elif mode == 'hapus':
            pilihan = input("\nPilih nomor soal yang akan dihapus: ").strip()
            try:
                pilihan = int(pilihan) - 1
                hapus_soal(soal_list[pilihan]['soal_id'])
            except (ValueError, IndexError):
                print("\nInput tidak valid!")
                
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        conn.close()