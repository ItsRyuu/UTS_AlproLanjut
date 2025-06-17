from flask import Flask, render_template, request, redirect, url_for, session, flash
from db.conn import get_connection, init_db
from core.hash import check_password, hash_password
import sqlite3
import core.state
from core.nilai import tampilkan_nilai, hitung_nilai_akhir, hitung_indeks
from core.dashboard.guru import bp_guru
from core.log import log_aktivitas
from core.enrollment import enroll_mapel, enroll_siswa
from core.dashboard.siswa import  bp_siswa
from core.edit_profil import edit_profil
import logging

app = Flask(__name__, static_folder='static')

logging.basicConfig(filename='log_file.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app.secret_key = 'your_secret_key'
app.register_blueprint(bp_guru)
app.register_blueprint(bp_siswa)

#HOME
@app.route('/')
def home():
    app.logger.info('Halaman home diakses')
    return render_template('home.html')

#KONTAK
@app.route('/contact')
def contact():
    return render_template('contact.html')

#LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form['username']
            password = request.form['password']

            conn = get_connection()
            user = conn.execute(
                """SELECT user_id, nama, email, password, role 
                FROM user WHERE email = ?""",
                (email,)
            ).fetchone()
            
            if user and check_password(password, user['password']):
                session_data = {
                    'user_id': user['user_id'],
                    'nama': user['nama'],
                    'email': user['email'],
                    'role': user['role'].lower()
                }

                # Get role-specific data
                if session_data['role'] == 'guru':
                    guru_data = conn.execute(
                        """SELECT guru_id, mapel_id 
                        FROM guru WHERE user_id = ?""",
                        (user['user_id'],)
                    ).fetchone()
                    
                    if guru_data:
                        session_data.update({
                            'guru_id': guru_data['guru_id'],
                            'mapel_id': guru_data['mapel_id']
                        })
                    else:
                        flash("Akun guru belum dilengkapi data di tabel guru", "danger")
                        return redirect(url_for('login'))

                elif session_data['role'] == 'siswa':
                    siswa_data = conn.execute(
                        """SELECT siswa_id, nis, kelas 
                        FROM siswa WHERE user_id = ?""",
                        (user['user_id'],)
                    ).fetchone()
                    
                    if siswa_data:
                        session_data.update({
                            'siswa_id': siswa_data['siswa_id'],
                            'nis': siswa_data['nis'],
                            'kelas': siswa_data['kelas']
                        })
                
                session['user'] = session_data

                try:
                    log_aktivitas(user['user_id'], "Login berhasil")
                except Exception as e:
                    print(f"[ERROR saat mencatat log login] {e}")

                print("Session:", session['user'])
                conn.close()
                
                if session_data['role'] == 'admin':
                    return redirect(url_for('dashboard_admin'))
                elif session_data['role'] == 'guru':
                    return redirect(url_for('dashboard_guru'))
                else:
                    return redirect(url_for('dashboard_siswa'))

            flash("Email atau password salah", "danger")
            return redirect(url_for('login'))
            
        except Exception as e:
            print(f"Login error: {str(e)}")
            flash("Terjadi kesalahan sistem", "danger")
            return redirect(url_for('login'))
            
    return render_template('login.html')

#DASHBOARD ADMIN
@app.route('/dashboard_admin')
def dashboard_admin():
    if 'user' not in session or session['user']['role'] != 'admin':
        flash("Anda harus login sebagai admin untuk mengakses halaman ini.", "danger")
        return redirect(url_for('login'))
    return render_template('dashboard_admin.html', user=session['user'])

#ADMIN LIST USER
@app.route('/admin/list_users')
def admin_list_users():
    if 'user' not in session or session['user']['role'] != 'admin':
        flash("Anda harus login sebagai admin untuk mengakses halaman ini.", "danger")
        return redirect(url_for('login'))
    conn = get_connection()
    users = conn.execute("SELECT user_id, nama, email, role FROM user").fetchall()
    conn.close()
    return render_template('admin_list_users.html', users=users, user=session['user'])
         
#REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():  
    if 'user' not in session or session['user']['role'] != 'admin':
        flash("Hanya admin yang dapat mengakses halaman registrasi.", "danger")
        return redirect(url_for('home'))

    if request.method == 'POST':
        nama = request.form['nama']
        email = request.form['username']
        password = request.form['password']
        role = request.form['role']
        nis = request.form.get('nis')
        kelas = request.form.get('kelas')
        nip = request.form.get('nip')
        mapel_id = request.form.get('mapel')

        conn = get_connection()
        try:
            # Hash password
            hashed_pw = hash_password(password)
            
            # Insert user
            conn.execute(
                """INSERT INTO user (nama, email, password, role)
                VALUES (?, ?, ?, ?)""",
                (nama, email, hashed_pw, role)
            )
            user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            
            # Insert role-specific data
            if role == 'siswa':
                conn.execute(
                    """INSERT INTO siswa (user_id, nis, kelas)
                    VALUES (?, ?, ?)""",
                    (user_id, nis, kelas)
                )
            elif role == 'guru':
                conn.execute(
                    """INSERT INTO guru (user_id, nip, mapel_id)
                    VALUES (?, ?, ?)""",
                    (user_id, nip, mapel_id)
                )
            
            conn.commit()
            flash("Registrasi berhasil! Silakan login.", "success")

            log_aktivitas(user_id, f'Registrasi berhasil sebagai {role}')

            return redirect(url_for('login'))
            
        except Exception as e:
            conn.rollback()
            flash(f"Registrasi gagal: {str(e)}", "danger")
            return redirect(url_for('register'))
            
        finally:
            conn.close()
    
    # GET request
    conn = get_connection()
    mapel_list = conn.execute("SELECT * FROM mapel").fetchall()
    conn.close()
    return render_template('register.html', mapel_list=mapel_list)

#LOG AKTIVITAS - DASHBOARD GURU
@app.route('/log_aktivitas')
def log_aktivitas_page():
    if 'user' not in session:
        flash("Anda harus login terlebih dahulu", "warning")
        return redirect(url_for('login'))
    
    user = session['user']
    conn = get_connection()
    #  agar bisa diakses dengan key
    conn.row_factory = sqlite3.Row 
    
    try:
        if user['role'] == 'siswa':
            # Log aktivitas siswa sendiri + nama siswa
            logs = conn.execute(
                """SELECT la.timestamp, la.aktivitas, u.nama AS nama_siswa
                   FROM log_aktivitas la
                   JOIN user u ON la.user_id = u.user_id
                   WHERE la.user_id = ?
                   ORDER BY la.timestamp DESC
                """,
                (user['user_id'],)
            ).fetchall()
            
        elif user['role'] == 'guru':
            # Log aktivitas siswa yang diajar guru + nama siswa
            logs = conn.execute(
                """SELECT la.timestamp, la.aktivitas, u.nama AS nama_siswa
                   FROM log_aktivitas la
                   JOIN user u ON la.user_id = u.user_id
                   JOIN siswa s ON s.user_id = u.user_id
                   JOIN enrollment e ON e.siswa_id = s.siswa_id
                   JOIN guru g ON g.mapel_id = e.mapel_id
                   WHERE g.guru_id = ?
                   ORDER BY la.timestamp DESC
                """,
                (user['guru_id'],)
            ).fetchall()
        else:
            flash("Akses ditolak", "danger")
            return redirect(url_for('home'))
        
        # Ubah hasil fetchall (list of sqlite3.Row) ke list of dict
        logs_dict = [dict(log) for log in logs]
        
        return render_template('log_aktivitas.html', logs=logs_dict)
        
    except Exception as e:
        print(f"Error log aktivitas: {str(e)}")
        flash("Gagal memuat log aktivitas", "danger")
        return redirect(url_for('dashboard_siswa' if user['role'] == 'siswa' else 'dashboard_guru'))
        
    finally:
        conn.close()

#LOG AKTIVITAS - DASHBOARD SISWA
@app.route('/log_aktivitas_siswa')
def log_aktivitas_siswa():
    if 'user' not in session:
        flash("Anda harus login terlebih dahulu", "warning")
        return redirect(url_for('login'))
    
    user = session['user']
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    
    try:
        if user['role'] == 'siswa':
            logs = conn.execute(
                """SELECT la.timestamp, la.aktivitas, u.nama AS nama_siswa
                   FROM log_aktivitas la
                   JOIN user u ON la.user_id = u.user_id
                   WHERE la.user_id = ?
                   ORDER BY la.timestamp DESC
                """,
                (user['user_id'],)
            ).fetchall()
            
        elif user['role'] == 'guru':
            logs = conn.execute(
                """SELECT la.timestamp, la.aktivitas, u.nama AS nama_siswa
                   FROM log_aktivitas la
                   JOIN user u ON la.user_id = u.user_id
                   JOIN siswa s ON s.user_id = u.user_id
                   JOIN enrollment e ON e.siswa_id = s.siswa_id
                   JOIN guru g ON g.mapel_id = e.mapel_id
                   WHERE g.guru_id = ?
                   ORDER BY la.timestamp DESC
                """,
                (user['guru_id'],)
            ).fetchall()
        else:
            flash("Akses ditolak", "danger")
            return redirect(url_for('home'))
        
        # Ubah hasil fetchall (list of sqlite3.Row) ke list of dict
        logs_dict = [dict(log) for log in logs]
        
        return render_template('log_aktivitas_siswa.html', logs=logs_dict)
        
    except Exception as e:
        print(f"Error log aktivitas: {str(e)}")
        flash("Gagal memuat log aktivitas", "danger")
        return redirect(url_for('dashboard_siswa' if user['role'] == 'siswa' else 'dashboard_guru'))
        
    finally:
        conn.close()
        
#DASHBOARD GURU
@app.route('/dashboard_guru')
def dashboard_guru():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user = session['user']

    log_aktivitas(user['user_id'], 'Mengakses dashboard guru')

    print("Session (dashboard_guru):", session['user'])
    return render_template('dashboard_guru.html', user=user)

#DASHBOARD SISWA
@app.route('/dashboard_siswa')
def dashboard_siswa():
    if 'user' not in session or session['user']['role'] != 'siswa':
        return redirect(url_for('login'))

    user = session['user']
    conn = get_connection()
    
    try:
        cursor = conn.execute("""
        SELECT 
            m.mapel_id AS id,
            m.nama_mapel AS nama,
            'Klik “more” untuk melihat mempelajari setiap materi dan latihan!' AS deskripsi,
            '' AS gambar
        FROM mapel m
        INNER JOIN enrollment e 
            ON m.mapel_id = e.mapel_id 
            AND e.siswa_id = ?
    """, (user['siswa_id'],))
        mapel_list = cursor.fetchall()

        return render_template('dashboard_siswa.html', user=user, daftar_mapel=mapel_list)

    finally:
        conn.close()

#ENROLLMENT MATA PELAJARAN - KHUSUS SISWA
@app.route('/enrollment_mapel', methods=['GET', 'POST'])
def enrollment_mapel():
    if 'user' not in session or session['user']['role'] != 'siswa':
        return redirect(url_for('login'))

    user = session['user']
    if request.method == 'POST':
        mapel_id = request.form.get('mapel_id')
        if mapel_id:
            try:
                enroll_siswa(mapel_id, user['siswa_id'])
                flash('Berhasil enroll mata pelajaran!', 'success')

                log_aktivitas(user ['user_id'], 'Telah mengenroll mata pelajaran')
                
                return redirect(url_for('dashboard_siswa'))
            except Exception as e:
                flash(f'Gagal enroll mata pelajaran: {e}', 'error')

    mapel_list = enroll_mapel(user['siswa_id'])
    if not mapel_list:
        flash('Tidak ada mata pelajaran yang tersedia untuk di-enroll.', 'error')
        return redirect(url_for('dashboard_siswa'))

    return render_template('enrollment_mapel.html', mapel_list=mapel_list)

#KERJAKAN SOAL - KHUSUS SISWA
@app.route('/kerjakan_soal/<int:materi_id>', methods=['GET', 'POST'])
def kerjakan_soal(materi_id):
    if 'user' not in session or session['user']['role'] != 'siswa':
        return redirect(url_for('login'))

    user = session['user']
    conn = get_connection()

    try:
        # Ambil informasi materi dan mapel_id terkait
        materi = conn.execute("SELECT * FROM materi WHERE materi_id = ?", (materi_id,)).fetchone()
        if not materi:
            flash("Materi tidak ditemukan", "danger")
            # Pastikan koneksi ditutup jika materi tidak ditemukan
            conn.close() 
            return redirect(url_for('dashboard_siswa'))
        # mapel_id yang benar untuk materi ini
        actual_mapel_id = materi['mapel_id'] 

        if request.method == 'POST':
            try:
                jawaban_data = []
                # Iterasi key dan value untuk mendapatkan jawaban siswa
                for key, value in request.form.items(): 
                    parts = key.split('_')
                    # Pastikan key adalah untuk jawaban soal (e.g., "jawaban_SOALID")
                    if key.startswith("jawaban_") and len(parts) == 2 and parts[1].isdigit():
                        soal_id = int(parts[1])
                        jawaban_siswa_value = value
                        jawaban_data.append((soal_id, jawaban_siswa_value))

                if not jawaban_data:
                    flash("Tidak ada jawaban yang terkirim.", "warning")
                    # Jika tidak ada jawaban, render kembali halaman soal dengan data yang ada
                    mapel_info_for_get = conn.execute("SELECT nama_mapel FROM mapel WHERE mapel_id = ?", (actual_mapel_id,)).fetchone()
                    nama_mapel_for_get = mapel_info_for_get['nama_mapel'] if mapel_info_for_get else "Nama Mapel Tidak Diketahui"
                    soal_list_for_get = conn.execute("SELECT * FROM soal WHERE materi_id = ?", (materi_id,)).fetchall()
                    return render_template('kerjakan_soal.html', soal_list=soal_list_for_get, materi=materi, nama_mapel=nama_mapel_for_get, mapel_id=actual_mapel_id)

                for soal_id, jawaban_siswa_value in jawaban_data:
                    conn.execute("""
                        INSERT OR REPLACE INTO jawaban 
                        (soal_id, siswa_id, jawaban, mapel_id, koreksi)
                        VALUES (?, ?, ?, ?, NULL)
                    """, (soal_id, user['siswa_id'], jawaban_siswa_value, actual_mapel_id))

                conn.commit()
                flash('Jawaban berhasil disimpan!', 'success')
            except Exception as e:
                conn.rollback()
                flash(f'Gagal menyimpan jawaban: {str(e)}', 'danger')
            
            log_aktivitas(user ['user_id'], 'Telah mengerjakan quiz')
            
            # Redirect ke halaman materi per mapel setelah submit, menggunakan actual_mapel_id
            if actual_mapel_id is not None:
                 return redirect(url_for('siswa.materi_per_mapel', mapel_id=actual_mapel_id))
            else:
                # Fallback jika actual_mapel_id adalah None (seharusnya tidak terjadi jika data materi valid)
                app.logger.error(f"actual_mapel_id is None untuk materi_id {materi_id} setelah pengerjaan soal. Redirecting ke dashboard.")
                flash("Jawaban telah disimpan, namun terjadi kesalahan saat kembali ke daftar materi (mapel tidak terdefinisi untuk materi ini).", "warning")
                return redirect(url_for('dashboard_siswa'))
 
        # Bagian untuk GET request
        mapel_info = conn.execute("SELECT nama_mapel FROM mapel WHERE mapel_id = ?", (actual_mapel_id,)).fetchone()
        nama_mapel = mapel_info['nama_mapel'] if mapel_info else "Mapel Tidak Diketahui"

        soal_list = conn.execute("SELECT * FROM soal WHERE materi_id = ?", (materi_id,)).fetchall()
        if not soal_list:
            flash("Belum ada soal untuk materi ini", "warning")
            # Redirect ke detail materi jika tidak ada soal, menggunakan blueprint siswa
            return redirect(url_for('siswa.lihat_detail_materi', materi_id=materi_id))

        # Kirim actual_mapel_id sebagai mapel_id ke template untuk konsistensi
        return render_template('kerjakan_soal.html', soal_list=soal_list, materi=materi, nama_mapel=nama_mapel, mapel_id=actual_mapel_id)
    except Exception as e:
        app.logger.error(f"Error di kerjakan_soal materi_id {materi_id}: {str(e)}")
        flash("Terjadi kesalahan sistem", "danger")
        return redirect(url_for('dashboard_siswa'))
    finally:
        # Pastikan conn ada sebelum ditutup
        if conn: 
            conn.close()
            
#TAMPILKAN MATERI
@app.route('/materi/<int:materi_id>')
def tampilkan_materi(materi_id):
    if 'user' not in session or session['user']['role'] != 'siswa':
        flash("Silakan login sebagai siswa.", "warning")
        return redirect(url_for('login'))

    user = session['user']
    conn = get_connection()

    # Cek apakah materi tersedia
    materi = conn.execute("SELECT * FROM materi WHERE materi_id = ?", (materi_id,)).fetchone()
    if not materi:
        flash("Materi tidak ditemukan.", "danger")
        return redirect(url_for('dashboard_siswa'))

    # Ambil nama mapel untuk navigasi
    mapel_info = conn.execute("SELECT nama_mapel FROM mapel WHERE mapel_id = ?", (materi['mapel_id'],)).fetchone()
    nama_mapel = mapel_info['nama_mapel'] if mapel_info else "Mapel Tidak Diketahui"

    return render_template('tampilkan_materi.html', materi=materi, nama_mapel=nama_mapel)

#LIHAT NILAI SISWA - DASHBOARD SISWA                 
@app.route('/lihat_nilai_siswa', methods=['GET', 'POST'])
def lihat_nilai_siswa():
    if 'user' not in session or session['user']['role'] != 'siswa':
        return redirect(url_for('login'))

    user = session['user']
    siswa_id = user['siswa_id']
    conn = None
    
    try:
        conn = get_connection()
        # Menampilkan daftar mapel yang di-enroll siswa
        mapel_list_rows = conn.execute("""
            SELECT m.mapel_id, m.nama_mapel
            FROM enrollment e
            JOIN mapel m ON e.mapel_id = m.mapel_id
            WHERE e.siswa_id = ?
            ORDER BY m.nama_mapel
        """, (siswa_id,)).fetchall()
        mapel_list = [dict(row) for row in mapel_list_rows]

        # Handle jika siswa belum enroll mapel sama sekali
        if not mapel_list_rows and request.method == 'GET': 
            flash("Anda belum terdaftar pada mata pelajaran manapun. Silakan enroll terlebih dahulu.", "warning")

        if request.method == 'POST':
            pilihan_mapel = request.form.get('mapel_id')
            if not pilihan_mapel:
                flash('Pilih mata pelajaran terlebih dahulu', 'warning')
                return render_template('lihat_nilai_siswa.html', mapel_list=mapel_list, user=user)
            
            mapel_id = int(pilihan_mapel)
            
            # Query utama untuk mendapatkan jawaban dan skor per materi
            query_jawaban_utama = """
                SELECT ma.materi_id, ma.judul AS nama_materi, j.jawaban, s.jawaban AS jawaban_benar, s.skor
                FROM jawaban j
                JOIN soal s ON j.soal_id = s.soal_id
                JOIN materi ma ON s.materi_id = ma.materi_id
                WHERE j.siswa_id = ? AND j.mapel_id = ? AND s.materi_id IS NOT NULL
                ORDER BY ma.judul
            """
            rows = conn.execute(query_jawaban_utama, (siswa_id, mapel_id)).fetchall()
            
            if not rows:
                flash("Tidak ada nilai untuk mata pelajaran ini.", "info")
                return render_template('lihat_nilai_siswa.html', mapel_list=mapel_list, selected_mapel=mapel_id, user=user)
            
            materi_scores = {}
            for row in rows:
                materi_id_row = row['materi_id']
                if materi_id_row not in materi_scores:
                    materi_scores[materi_id_row] = {
                        'nama_materi': row['nama_materi'],
                        'total_skor': 0,
                        'total_maks': 0
                    }
                materi_scores[materi_id_row]['total_maks'] += row['skor'] or 0
                if row['jawaban'] == row['jawaban_benar']:
                    materi_scores[materi_id_row]['total_skor'] += row['skor'] or 0
            
            nilai_details = []
            total_skor_mapel = 0
            total_maksimal_mapel = 0
            for materi_id_key, data in materi_scores.items():
                
                # Ambil detail jawaban untuk setiap materi
                query_detail_jawaban = """
                    SELECT
                        s.pertanyaan,
                        s.opsi_a,
                        s.opsi_b,
                        s.opsi_c,
                        s.opsi_d,
                        j.jawaban AS jawaban_siswa,
                        s.jawaban AS jawaban_benar
                    FROM soal s
                    LEFT JOIN jawaban j ON s.soal_id = j.soal_id AND j.siswa_id = ?
                    WHERE s.materi_id = ?
                """
                detail_jawaban_rows = conn.execute(query_detail_jawaban, (siswa_id, materi_id_key)).fetchall()
                detail_jawaban_list = [dict(row) for row in detail_jawaban_rows]

                skor_diperoleh_materi = data['total_skor'] 
                skor_maksimal_materi = data['total_maks']
                
                nilai_details.append({
                    'materi_id': materi_id_key,
                    'nama_materi': data['nama_materi'], 
                    'nilai_akhir': skor_diperoleh_materi,
                    'skor_maksimal_materi': skor_maksimal_materi,
                    'indeks_materi': hitung_indeks(skor_diperoleh_materi, skor_maksimal_materi),
                    'detail_jawaban': detail_jawaban_list 
                })
                total_skor_mapel += data['total_skor']
                total_maksimal_mapel += data['total_maks']

            # Hitung indeks keseluruhan mapel
            indeks = hitung_indeks(total_skor_mapel, total_maksimal_mapel)

            return render_template(
                'lihat_nilai_siswa.html', 
                mapel_list=mapel_list, 
                nilai_details=nilai_details, 
                total_skor=total_skor_mapel, 
                total_maksimal=total_maksimal_mapel, 
                indeks=indeks,
                selected_mapel=mapel_id,
                user=user
            )
        else:
            return render_template('lihat_nilai_siswa.html', mapel_list=mapel_list, user=user)

    except Exception as e:
        app.logger.error(f"Error di lihat_nilai_siswa: {str(e)}")
        flash("Terjadi kesalahan saat memuat nilai.", "danger")
        return redirect(url_for('dashboard_siswa'))
    finally:
        if conn:
            conn.close()

            
#LIHAT PROFIL SISWA
@app.route('/profil_siswa', methods=['GET', 'POST'])
def profil_siswa():
    if 'user' not in session or session['user']['role'] != 'siswa':
        return redirect(url_for('login'))

    user = session['user']

    with get_connection() as conn:
        # agar bisa diakses seperti dict
        conn.row_factory = sqlite3.Row  
        cursor = conn.cursor()

        if request.method == 'POST':
            # Update Nama
            if 'edit_nama' in request.form:
                new_nama = request.form.get('nama_baru', '').strip()
                if new_nama:
                    cursor.execute("UPDATE user SET nama = ? WHERE user_id = ?", (new_nama, user['user_id']))
                    conn.commit()
                    session['user']['nama'] = new_nama
                    flash("Nama berhasil diperbarui", "success")
                else:
                    flash("Nama tidak boleh kosong", "error")

            # Update Password
            elif 'ubah_password' in request.form:
                password_lama = request.form.get('password_lama', '').strip()
                password_baru = request.form.get('password_baru', '').strip()
                konfirmasi = request.form.get('konfirmasi', '').strip()

                if not password_lama or not password_baru or not konfirmasi:
                    flash("Semua kolom password harus diisi", "error")
                else:
                    cursor.execute("SELECT password FROM user WHERE user_id = ?", (user['user_id'],))
                    user_db = cursor.fetchone()

                    if not user_db or not check_password(password_lama, user_db['password']):
                        flash("Password lama salah", "error")
                    elif password_baru != konfirmasi:
                        flash("Konfirmasi password tidak cocok", "error")
                    else:
                        hashed_password = hash_password(password_baru)
                        cursor.execute("UPDATE user SET password = ? WHERE user_id = ?", (hashed_password, user['user_id']))
                        conn.commit()
                        flash("Password berhasil diubah", "success")

        #Ambil data profil terbaru
        cursor.execute("""
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
        flash("Data siswa tidak ditemukan", "error")
        return redirect(url_for('dashboard_siswa'))

    return render_template('profil_siswa.html', profile=profile)

#LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

#EDIT PROFIL
@app.route('/edit_profil', methods=['GET', 'POST'])
def edit_profil():
    user = core.state.current_user

    if request.method == 'POST':
        new_name = request.form['name']
        new_email = request.form['email']

        edit_profil(user, new_name, new_email)
        return redirect(url_for('dashboard'))

    return render_template('edit_profil.html', user=user)

# Rute untuk dashboard (misalnya untuk mengarahkan setelah edit profil)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

    nama_mapel = conn.execute(
        '''SELECT mapel.id AS mapel_id, mapel.nama AS nama_mapel, em.is_enrolled
           FROM mapel
           LEFT JOIN enrollments em ON mapel.id = em.mapel_id AND em.siswa_id = ?''',
        (user['id'],)
    ).fetchall()

    conn.close()
    return render_template('dashboard_siswa.html', user=user, nama_mapel=nama_mapel)

#LIHAT NILAI - DARI SUDUT PANDANG GURU
@app.route('/lihat_nilai_guru')
def lihat_nilai_guru():
    user = core.state.current_user
    siswa_id = user['siswa_id']
    
    hitung_nilai_akhir(siswa_id)

    nilai_akhir = tampilkan_nilai(siswa_id)

    return render_template('lihat_nilai_guru.html', nilai_akhir=nilai_akhir)

#MENJALANKAN APLIKASI
if __name__ == "__main__":
    app.run(debug=True)
