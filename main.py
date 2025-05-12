from db.conn import init_db
from core.login import register_user, login_user
import core.state
from core.dashboard_router import tampilkan_dashboard

def tampilkan_menu_utama():
    print("="*25 + " WELCOME TO SMARTIN SISTEM " + "="*25)
    print("1. Register")
    print("2. Login")
    print("0. Keluar")
    print("="*78)
    
def proses_menu(pilihan):
    if pilihan == '1':
        print("\n--- Registrasi Pengguna Baru ---")
        nama = input("Nama: ").strip()
        email = input("Email: ").strip()
        password = input("Password: ").strip()
        role = input("Peran (siswa/guru): ").strip().lower()
        register_user(nama, email, password, role)
        return True
    elif pilihan == '2':
        print("\n--- Login Pengguna ---")
        email = input("Email: ").strip()
        password = input("Password: ").strip()
        core.state.current_user = login_user(email, password)
        return True
    elif pilihan == '0':
        print("Keluar dari program. Terima kasih!")
        return False
    else:
        print("Pilihan tidak valid.\n")
        return True

def main():
    init_db()
    while True:
        if core.state.current_user:
            tampilkan_dashboard(core.state.current_user)
        else:
            tampilkan_menu_utama()
            pilihan = input("Pilih menu (0-2): ").strip()
            if not proses_menu(pilihan):
                break
            
if __name__ == "__main__":
    main()