from core.dashboard.guru import dashboard_guru
from core.dashboard.siswa import dashboard_siswa
import core.state

def tampilkan_dashboard(user):
    while True:
        if not core.state.current_user:
            return
        
        if user["role"] == "guru":
            if not dashboard_guru(user):
                break
        elif user["role"] == "siswa":
            if not dashboard_siswa(user):
                break