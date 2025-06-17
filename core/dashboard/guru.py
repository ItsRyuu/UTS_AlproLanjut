from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from db.conn import get_connection
from core.hash import hash_password
from core.nilai import hitung_indeks

bp_guru = Blueprint('guru', __name__, template_folder='../../templates')

# Dashboard Guru
@bp_guru.route('/dashboard_guru')
def dashboard_guru_view():
    if 'user' not in session or session['user'].get('role') != 'guru':
        return redirect(url_for('login'))
    return render_template('dashboard_guru.html', user=session['user'])

# Kelola/Manajemen Materi
@bp_guru.route('/kelola_materi')
def kelola_materi():
    if 'user' not in session or session['user']['role'] != 'guru':
        flash("Akses ditolak", "danger")
        return redirect(url_for('login'))

    conn = get_connection()
    guru_id = session['user']['guru_id']

    materi = conn.execute("""
    SELECT m.materi_id, m.judul, m.deskripsi, mp.nama_mapel, m.is_locked
    FROM materi m
    JOIN mapel mp ON m.mapel_id = mp.mapel_id
    JOIN guru g ON g.mapel_id = mp.mapel_id
    WHERE g.guru_id = ?
    """, (guru_id,)).fetchall()
    
    conn.close()
    return render_template("kelola_materi_guru.html", materi=materi)
        
#tambah materi
@bp_guru.route('/tambah-materi', methods=['GET', 'POST'])
def tambah_materi():
    conn = get_connection()

    user = session.get('user')
    if not user or user.get('role') != 'guru':
        conn.close()
        return "Akses ditolak", 403

    user_id = user['user_id']

    guru = conn.execute("SELECT guru_id, mapel_id FROM guru WHERE user_id = ?", (user_id,)).fetchone()
    if not guru:
        conn.close()
        return "Guru tidak ditemukan", 404

    if request.method == 'POST':
        judul = request.form['judul']
        deskripsi = request.form['deskripsi']
        video_url = request.form.get('video_url', None) #bisa kosong
        mapel_id = guru['mapel_id']  # otomatis sesuai dengan guru

        conn.execute("""
            INSERT INTO materi (judul, deskripsi, mapel_id, video_url)
            VALUES (?, ?, ?, ?)
        """, (judul, deskripsi, mapel_id, video_url))
        conn.commit()
        conn.close()
        return redirect(url_for('guru.kelola_materi'))

    conn.close()
    return render_template('tambah_materi_guru.html')

@bp_guru.route('/edit-materi/<int:materi_id>', methods=['GET', 'POST'])
def edit_materi(materi_id):
    conn = get_connection()

    user = session.get('user')
    if not user or user.get('role') != 'guru':
        conn.close()
        return "Akses ditolak", 403

    materi = conn.execute("SELECT * FROM materi WHERE materi_id = ?", (materi_id,)).fetchone()
    if not materi:
        conn.close()
        return "Materi tidak ditemukan", 404

    if request.method == 'POST':
        judul = request.form['judul']
        deskripsi = request.form['deskripsi']
        video_url = request.form.get('video_url', None)

        try:
            conn.execute("""
                UPDATE materi
                SET judul = ?, deskripsi = ?, video_url = ?
                WHERE materi_id = ?
            """, (judul, deskripsi, video_url, materi_id))
            conn.commit()
            conn.close()
            return redirect(url_for('guru.kelola_materi'))
        except Exception as e:
            conn.rollback()
            conn.close()
            return f"Error saat memperbarui materi: {e}", 500

    conn.close()
    return render_template('edit_materi_guru.html', materi=materi)

@bp_guru.route('/hapus-materi/<int:materi_id>', methods=['POST'])
def hapus_materi(materi_id):
    conn = get_connection()

    user = session.get('user')
    if not user or user.get('role') != 'guru':
        conn.close()
        flash("Akses ditolak", "danger")
        return redirect(url_for('guru.kelola_materi'))

    try:
        conn.execute("DELETE FROM materi WHERE materi_id = ?", (materi_id,))
        conn.commit()
        flash("Materi berhasil dihapus", "success")
        conn.close()
        return redirect(url_for('guru.kelola_materi'))
    except Exception as e:
        conn.rollback()
        flash(f"Error saat menghapus materi: {e}", "danger")
        conn.close()
        return redirect(url_for('guru.kelola_materi'))

@bp_guru.route('/toggle_lock_materi/<int:materi_id>', methods=['POST'])
def toggle_lock_materi(materi_id):
    conn = get_connection()
    user = session.get('user')
    if not user or user.get('role') != 'guru':
        conn.close()
        flash("Akses ditolak", "danger")
        return redirect(url_for('guru.kelola_materi'))

    is_locked_list = request.form.getlist('is_locked')
    if not is_locked_list or is_locked_list[-1] not in ['0', '1']:
        flash("Status kunci tidak valid", "danger")
        conn.close()
        return redirect(url_for('guru.kelola_materi'))

    is_locked = is_locked_list[-1]

    try:
        conn.execute("UPDATE materi SET is_locked = ? WHERE materi_id = ?", (int(is_locked), materi_id))
        conn.commit()
        flash("Status kunci materi berhasil diperbarui", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Gagal memperbarui status kunci materi: {e}", "danger")
    finally:
        conn.close()

    return redirect(url_for('guru.kelola_materi'))
        
# Diskusi Guru
@bp_guru.route('/diskusi_guru', methods=['GET', 'POST'])
def diskusi_guru():
    if 'user' not in session or session['user'].get('role') != 'guru':
        return redirect(url_for('login'))
    conn = get_connection()
    user = session['user']
    if request.method == 'POST':
        answer_text = request.form.get('answer')
        question_id = request.form.get('question_id')
        if answer_text and question_id:
            conn.execute(
                "INSERT INTO jawaban_guru (guru_id, pertanyaan_id, text) VALUES (?, ?, ?)",
                (user['guru_id'], question_id, answer_text)
            )
            conn.commit()
            flash('Jawaban berhasil dikirim', 'success')
        else:
            flash('Jawaban dan pertanyaan harus diisi', 'danger')
        return redirect(url_for('guru.diskusi_guru'))
            # Fetch questions and their answers
    questions = conn.execute("""
        SELECT ps.id, ps.text, ps.timestamp, 
               IFNULL(jg.text, '') AS jawaban, jg.timestamp AS jawaban_timestamp,
               u_siswa.nama AS nama_siswa,
               u_guru.nama AS nama_guru
        FROM pertanyaan_siswa ps
        JOIN siswa s ON ps.siswa_id = s.siswa_id
        JOIN user u_siswa ON s.user_id = u_siswa.user_id
        LEFT JOIN jawaban_guru jg ON ps.id = jg.pertanyaan_id
        LEFT JOIN guru g ON jg.guru_id = g.guru_id
        LEFT JOIN user u_guru ON g.user_id = u_guru.user_id
        ORDER BY ps.timestamp DESC
    """).fetchall()
    conn.close()
    return render_template('diskusi_guru.html', user=user, questions=questions)

# Manage Soal    
@bp_guru.route('/manage_soal')
def manage_soal():
    # SEKARANG session['user']['guru_id'] pasti ada
    guru_id = session['user']['guru_id']

    conn = get_connection()
    soal_list = conn.execute(
        """
        SELECT s.soal_id, s.pertanyaan, s.opsi_a, s.opsi_b, s.opsi_c, s.opsi_d,
               s.skor, s.jawaban, m.judul AS materi_judul
          FROM soal s
          LEFT JOIN materi m ON s.materi_id = m.materi_id
         WHERE s.guru_id = ?
         ORDER BY s.soal_id
        """, (guru_id,)
    ).fetchall()
    conn.close()

    return render_template('manage_soal.html', soal_list=soal_list)
    
# Create Soal
@bp_guru.route('/manage_soal/create', methods=['GET', 'POST'])
def create_soal():
    if 'user' not in session or session['user'].get('role') != 'guru':
        return redirect(url_for('login'))
    guru = session['user']
    if request.method == 'POST':
        materi_id = request.form['materi_id']
        pertanyaan = request.form['pertanyaan']
        opsi_a = request.form['opsi_a']
        opsi_b = request.form['opsi_b']
        opsi_c = request.form['opsi_c']
        opsi_d = request.form['opsi_d']
        skor = request.form.get('skor', 10)
        jawaban = request.form['jawaban']
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO soal (materi_id, guru_id, pertanyaan, opsi_a, opsi_b, opsi_c, opsi_d, skor, jawaban) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (materi_id, guru['guru_id'], pertanyaan, opsi_a, opsi_b, opsi_c, opsi_d, skor, jawaban)
            )
            conn.commit()
            flash('Soal berhasil dibuat', 'success')
            return redirect(url_for('guru.manage_soal'))
        except Exception as e:
            conn.rollback()
            flash(f'Error membuat soal: {e}', 'danger')
        finally:
            conn.close()
    # GET: siapkan form
    conn = get_connection()
    materi_list = conn.execute(
        "SELECT materi_id, judul FROM materi WHERE mapel_id IN (SELECT mapel_id FROM guru WHERE guru_id=?)", (guru['guru_id'],)
    ).fetchall()
    conn.close()
    return render_template('soal_form.html', materi_list=materi_list, action='create')
        
# Edit Soal
@bp_guru.route('/manage_soal/<int:soal_id>/edit', methods=['GET', 'POST'])
def edit_soal_view(soal_id):
    if 'user' not in session or session['user'].get('role') != 'guru':
        return redirect(url_for('login'))
    guru = session['user']
    conn = get_connection()
    soal = conn.execute(
        "SELECT * FROM soal WHERE soal_id = ? AND guru_id = ?", (soal_id, guru['guru_id'])
    ).fetchone()
    if not soal:
        conn.close()
        flash('Soal tidak ditemukan', 'warning')
        return redirect(url_for('guru.manage_soal'))
    if request.method == 'POST':
        pertanyaan = request.form['pertanyaan']
        opsi_a = request.form['opsi_a']
        opsi_b = request.form['opsi_b']
        opsi_c = request.form['opsi_c']
        opsi_d = request.form['opsi_d']
        materi_id = request.form['materi_id']
        skor = request.form.get('skor', soal['skor'])
        jawaban = request.form['jawaban']
        try:
            conn.execute(
                """
                UPDATE soal SET pertanyaan=?, opsi_a=?, opsi_b=?, opsi_c=?, opsi_d=?, materi_id=?, skor=?, jawaban=?
                 WHERE soal_id=? AND guru_id=?
                """,
                (pertanyaan, opsi_a, opsi_b, opsi_c, opsi_d, materi_id, skor, jawaban, soal_id, guru['guru_id'])
            )
            conn.commit()
            flash('Soal berhasil diperbarui', 'success')
            return redirect(url_for('guru.manage_soal'))
        except Exception as e:
            conn.rollback()
            flash(f'Error mengedit soal: {e}', 'danger')
        finally:
            conn.close()
    # GET: siapkan materi_list untuk select dropdown
    materi_list = conn.execute(
        "SELECT materi_id, judul FROM materi WHERE mapel_id IN (SELECT mapel_id FROM guru WHERE guru_id=?)", (guru['guru_id'],)
    ).fetchall()
    conn.close()
    return render_template('soal_form.html', soal=soal, materi_list=materi_list, action='edit')
        
# Delete Soal
@bp_guru.route('/manage_soal/<int:soal_id>/delete', methods=['POST'])
def delete_soal(soal_id):
    if 'user' not in session or session['user'].get('role') != 'guru':
        return redirect(url_for('login'))
    guru = session['user']
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM soal WHERE soal_id = ? AND guru_id = ?", (soal_id, guru['guru_id'])
        )
        conn.commit()
        flash('Soal berhasil dihapus', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error menghapus soal: {e}', 'danger')
    finally:
        conn.close()
    return redirect(url_for('guru.manage_soal'))


@bp_guru.route('/lihat_nilai_guru', methods=['GET', 'POST']) # Tambahkan POST
def lihat_nilai_guru():
    if 'user' not in session or session['user']['role'] != 'guru':
        flash("Akses ditolak.", "danger")
        return redirect(url_for('login'))
    
    guru = session['user']
    conn = get_connection()
    
    # Ambil daftar mapel yang diajar guru
    # Jika guru hanya punya 1 mapel_id di session, bisa disederhanakan
    mapel_diajar_list = conn.execute("""
        SELECT m.mapel_id, m.nama_mapel 
        FROM mapel m
        JOIN guru g ON m.mapel_id = g.mapel_id 
        WHERE g.guru_id = ?
        ORDER BY m.nama_mapel
    """, (guru['guru_id'],)).fetchall()
    
    if not mapel_diajar_list:
        flash("Anda tidak mengajar mata pelajaran apapun atau data mapel tidak ditemukan.", "warning")
        conn.close()
        return render_template('lihat_nilai_guru.html', nilai_siswa_list=[], mapel_list=[], user=guru)

    selected_mapel_id_str = request.form.get('mapel_id') if request.method == 'POST' else None
    
    # Default ke mapel pertama guru jika tidak ada pilihan (atau GET request)
    if not selected_mapel_id_str and mapel_diajar_list:
        selected_mapel_id_str = str(mapel_diajar_list[0]['mapel_id'])

    nilai_siswa_list = []
    nama_mapel_terpilih = ""
    total_skor_maksimal_mapel = 0

    if selected_mapel_id_str:
        try:
            selected_mapel_id = int(selected_mapel_id_str)
            mapel_info = conn.execute("SELECT nama_mapel FROM mapel WHERE mapel_id = ?", (selected_mapel_id,)).fetchone()
            if mapel_info:
                nama_mapel_terpilih = mapel_info['nama_mapel']

            # 1. Dapatkan total skor maksimal untuk mapel yang dipilih
            skor_maks_row = conn.execute("""
                SELECT SUM(s.skor) AS total_skor_max
                FROM soal s
                JOIN materi m ON s.materi_id = m.materi_id
                WHERE m.mapel_id = ?
            """, (selected_mapel_id,)).fetchone()
            total_skor_maksimal_mapel = skor_maks_row['total_skor_max'] if skor_maks_row and skor_maks_row['total_skor_max'] is not None else 0

            # 2. Dapatkan skor perolehan masing-masing siswa yang di-enroll di mapel tersebut
            siswa_enrolled_rows = conn.execute("""
                SELECT s.siswa_id, u.nama AS nama_siswa, s.nis, s.kelas
                FROM siswa s
                JOIN user u ON s.user_id = u.user_id
                JOIN enrollment e ON s.siswa_id = e.siswa_id
                WHERE e.mapel_id = ?
                ORDER BY u.nama
            """, (selected_mapel_id,)).fetchall()

            for siswa_data in siswa_enrolled_rows:
                skor_diperoleh_row = conn.execute("""
                    SELECT SUM(soal.skor) AS total_skor_diperoleh
                    FROM jawaban j
                    JOIN soal ON j.soal_id = soal.soal_id
                    WHERE j.siswa_id = ? AND j.mapel_id = ? AND j.jawaban = soal.jawaban
                """, (siswa_data['siswa_id'], selected_mapel_id)).fetchone()
                
                skor_diperoleh = skor_diperoleh_row['total_skor_diperoleh'] if skor_diperoleh_row and skor_diperoleh_row['total_skor_diperoleh'] is not None else 0
                indeks = hitung_indeks(skor_diperoleh, total_skor_maksimal_mapel)
                
                # Ambil detail skor per materi untuk siswa ini
                materi_nilai_rows = conn.execute("""
                    SELECT 
                        m.materi_id, 
                        m.judul AS nama_materi,
                        s.skor AS skor_soal,
                        j.jawaban AS jawaban_siswa,
                        s.jawaban AS jawaban_benar
                    FROM materi m
                    JOIN soal s ON m.materi_id = s.materi_id
                    LEFT JOIN jawaban j ON s.soal_id = j.soal_id AND j.siswa_id = ?
                    WHERE m.mapel_id = ?
                    ORDER BY m.judul, s.soal_id
                """, (siswa_data['siswa_id'], selected_mapel_id)).fetchall()

                student_materi_scores_dict = {}
                for row_mn in materi_nilai_rows:
                    materi_id_key = row_mn['materi_id']
                    if materi_id_key not in student_materi_scores_dict:
                        student_materi_scores_dict[materi_id_key] = {
                            'nama_materi': row_mn['nama_materi'],
                            'skor_diperoleh_materi': 0,
                            'skor_maksimal_materi': 0
                        }
                    if row_mn['skor_soal'] is not None:
                        student_materi_scores_dict[materi_id_key]['skor_maksimal_materi'] += row_mn['skor_soal']
                    if row_mn['jawaban_siswa'] and row_mn['jawaban_siswa'] == row_mn['jawaban_benar'] and row_mn['skor_soal'] is not None:
                        student_materi_scores_dict[materi_id_key]['skor_diperoleh_materi'] += row_mn['skor_soal']
                
                student_materi_details_list = [{
                    'nama_materi': data['nama_materi'],
                    'skor_diperoleh_materi': data['skor_diperoleh_materi'],
                    'skor_maksimal_materi': data['skor_maksimal_materi'],
                    'indeks_materi': hitung_indeks(data['skor_diperoleh_materi'], data['skor_maksimal_materi'])
                } for mid, data in student_materi_scores_dict.items()]

                nilai_siswa_list.append({
                    'nama_siswa': siswa_data['nama_siswa'],
                    'nis': siswa_data['nis'],
                    'kelas': siswa_data['kelas'],
                    'skor_diperoleh_mapel': skor_diperoleh, # Total skor mapel siswa
                    'skor_maksimal_mapel': total_skor_maksimal_mapel, # Max skor mapel (sama untuk semua)
                    'indeks_mapel': indeks, # Indeks mapel siswa
                    'materi_details': student_materi_details_list # Rincian per materi
                })
        except ValueError:
            flash("Mapel ID tidak valid.", "danger")
        except Exception as e:
            flash(f"Terjadi kesalahan saat memuat nilai: {str(e)}", "danger")
            # Pertimbangkan logging error di sini jika app logger tersedia
            print(f"Error di lihat_nilai_guru: {str(e)}")
            
    conn.close()
    return render_template(
        'lihat_nilai_guru.html', 
        nilai_siswa_list=nilai_siswa_list, 
        mapel_list=mapel_diajar_list, # Untuk dropdown pemilihan mapel
        selected_mapel_id=int(selected_mapel_id_str) if selected_mapel_id_str else None,
        nama_mapel_terpilih=nama_mapel_terpilih,
        user=guru 
    )
                

@bp_guru.route('/profil_guru', methods=['GET', 'POST'])
def profil_guru():
    if 'user' not in session or session['user']['role'] != 'guru':
        return redirect(url_for('login'))
    user = session['user']
    conn = get_connection()
    if request.method == 'POST':
        nama_baru = request.form['nama']
        password_baru = request.form['password']
        konfirmasi_password = request.form['konfirmasi_password']
        try:
            conn.execute("UPDATE user SET nama = ? WHERE user_id = ?", (nama_baru, user['user_id']))
            if password_baru:
                if password_baru == konfirmasi_password:
                    hashed_pw = hash_password(password_baru)
                    conn.execute("UPDATE user SET password = ? WHERE user_id = ?", (hashed_pw, user['user_id']))
                else:
                    flash("Password dan konfirmasi tidak cocok", "danger")
                    conn.close()
                    return redirect(url_for('guru.profil_guru'))
            conn.commit()
            user['nama'] = nama_baru
            flash("Profil berhasil diperbarui", "success")
            conn.close()
            return redirect(url_for('guru.dashboard_guru_view'))  # kembali ke dashboard
        except Exception as e:
            conn.rollback()
            flash(f"Gagal memperbarui profil: {e}", "danger")
            conn.close()
            return redirect(url_for('guru.profil_guru'))

    user_data = conn.execute(
        """
        SELECT u.nama, u.email, g.mapel_id, m.nama_mapel 
        FROM user u 
        JOIN guru g ON u.user_id = g.user_id 
        JOIN mapel m ON g.mapel_id = m.mapel_id 
        WHERE u.user_id = ?
        """, 
        (user['user_id'],)
    ).fetchone()
    conn.close()
    return render_template('profil_guru.html', user=user_data)
