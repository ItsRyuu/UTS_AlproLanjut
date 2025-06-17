from core.login import register_user

admin_nama = "Admin"
admin_email = "admin@gmail.com"
admin_password = "admin"
admin_role = "admin"

if register_user(admin_nama, admin_email, admin_password, admin_role):
    print("Akun admin berhasil dibuat.")
else:
    print("Gagal membuat akun admin.")
