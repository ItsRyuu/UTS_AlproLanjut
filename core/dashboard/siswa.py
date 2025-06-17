#core/dashboard/siswa.py
from db.conn import get_connection
from flask import Blueprint, render_template, session, redirect, url_for, request, flash

bp_siswa = Blueprint('siswa', __name__, template_folder='../../templates')

def get_detail_jawaban(siswa_id, mapel_id):
    conn = get_connection()
    try:
        cursor = conn.execute("""
            SELECT 
                s.soal_id,
                s.pertanyaan,
                s.jawaban AS jawaban_benar,
                j.jawaban AS jawaban_siswa,
                n.skor
            FROM jawaban j
            JOIN soal s ON j.soal_id = s.soal_id
            LEFT JOIN nilai n ON j.jawab_id = n.jawab_id
            WHERE j.siswa_id = ? AND j.mapel_id = ?
        """, (siswa_id, mapel_id))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error getting jawaban: {str(e)}")
        return None
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
        query = """
        SELECT m.mapel_id, m.nama_mapel, ma.materi_id, ma.judul AS nama_materi, n.skor AS nilai_akhir
        FROM nilai n
        JOIN mapel m ON n.mapel_id = m.mapel_id
        JOIN materi ma ON ma.mapel_id = m.mapel_id
        WHERE n.siswa_id = ?
        ORDER BY m.nama_mapel, ma.judul
        """
        rows = conn.execute(query, (siswa_id,)).fetchall()
        grouped = {}
        for row in rows:
            mapel_id = row['mapel_id']
            if mapel_id not in grouped:
                grouped[mapel_id] = {
                    'nama_mapel': row['nama_mapel'],
                    'materi': []
                }
            grouped[mapel_id]['materi'].append({
                'materi_id': row['materi_id'],
                'nama_materi': row['nama_materi'],
                'nilai_akhir': row['nilai_akhir']
            })
        return grouped, None
    except Exception as e:
        return None, f"Gagal menampilkan nilai: {e}"
    finally:
        conn.close()
                
def get_nilai_mapel(siswa_id, mapel_id):
    conn = get_connection()
    try:
        cursor = conn.execute("""
            SELECT 
                j.soal_id,
                s.pertanyaan,
                j.jawaban AS jawaban_siswa,
                s.jawaban AS jawaban_benar,
                s.skor AS skor_maks
            FROM jawaban j
            JOIN soal s ON j.soal_id = s.soal_id
            WHERE j.siswa_id = ? AND s.mapel_id = ?
            GROUP BY j.soal_id
        """, (siswa_id, mapel_id))
        
        results = cursor.fetchall()
        
        if not results:
            return None, "Belum ada nilai untuk mapel ini"
        
        total_skor = 0
        total_maksimal = 0
        
        for row in results:
            if row['jawaban_siswa'] == row['jawaban_benar']:
                total_skor += row['skor_maks'] or 0
            total_maksimal += row['skor_maks'] or 0
        
        return results, total_skor, total_maksimal
        
    except Exception as e:
        return None, f"Error: {e}"
    finally:
        conn.close()
                
from db.conn import get_connection

#locked and unlocked materi
def is_materi_unlocked(user_id, materi_id):
    if materi_id == 1:
        return True
    db = get_connection()
    prev_materi_id = materi_id - 1
    selesai = db.execute(
        "SELECT 1 FROM progress WHERE user_id = ? AND materi_id = ? AND status = 'selesai'",
        (user_id, prev_materi_id)
    ).fetchone()
    return selesai is not None

def unlock_materi(siswa_id, materi_id):
    if materi_id is None:
        return
    conn = get_connection()
    try:
        # Cek apakah sudah pernah unlock sebelumnya
        exists = conn.execute("""
            SELECT 1 FROM progress WHERE user_id = ? AND materi_id = ?
        """, (siswa_id, materi_id)).fetchone()
        if not exists:
            conn.execute("""
                INSERT INTO progress (user_id, materi_id, status) VALUES (?, ?, 'unlock')
            """, (siswa_id, materi_id))
            conn.commit()
    except Exception as e:
        print(f"Error unlocking materi: {e}")
    finally:
        conn.close()
        
def get_materi_id_from_soal(soal_id):
    conn = get_connection()
    try:
        result = conn.execute("SELECT materi_id FROM soal WHERE soal_id = ?", (soal_id,)).fetchone()
        return result['materi_id'] if result else None
    finally:
        conn.close()

def count_soal_in_materi(materi_id):
    conn = get_connection()
    try:
        result = conn.execute("SELECT COUNT(*) AS total FROM soal WHERE materi_id = ?", (materi_id,)).fetchone()
        return result['total'] if result else 0
    finally:
        conn.close()

def count_jawaban_siswa_di_materi(siswa_id, materi_id):
    conn = get_connection()
    try:
        result = conn.execute("""
            SELECT COUNT(DISTINCT j.soal_id) AS total_jawaban
            FROM jawaban j
            JOIN soal s ON j.soal_id = s.soal_id
            WHERE j.siswa_id = ? AND s.materi_id = ?
        """, (siswa_id, materi_id)).fetchone()
        return result['total_jawaban'] if result else 0
    finally:
        conn.close()

def hitung_nilai_quiz(siswa_id, materi_id):
    conn = get_connection()
    try:
        # Hitung jumlah soal dan jawaban benar di materi
        total_skor = 0
        total_maks = 0
        rows = conn.execute("""
            SELECT s.skor, j.jawaban, s.jawaban AS jawaban_benar
            FROM soal s
            LEFT JOIN jawaban j ON s.soal_id = j.soal_id AND j.siswa_id = ?
            WHERE s.materi_id = ?
        """, (siswa_id, materi_id)).fetchall()
        
        for row in rows:
            total_maks += row['skor'] or 0
            if row['jawaban'] == row['jawaban_benar']:
                total_skor += row['skor'] or 0

        if total_maks == 0:
            return 0
        nilai_persen = (total_skor / total_maks) * 100
        return nilai_persen
    finally:
        conn.close()

def get_next_materi(current_materi_id):
    conn = get_connection()
    try:
        # Misal materi diurutkan berdasarkan materi_id, dapat diubah sesuai kebutuhan
        next_materi = conn.execute("""
            SELECT materi_id FROM materi WHERE materi_id > ? ORDER BY materi_id ASC LIMIT 1
        """, (current_materi_id,)).fetchone()
        return next_materi['materi_id'] if next_materi else None
    finally:
        conn.close()



#Kerjakan soal
def kerjakan_soal(user):
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT siswa_id FROM siswa WHERE siswa_id = ?", (user['siswa_id'],))
        if not cursor.fetchone():
            raise ValueError("Data siswa tidak valid")

        # Daftar mapel yang di-enroll
        cursor = conn.execute("""
            SELECT m.mapel_id, m.nama_mapel
            FROM enrollment e
            JOIN mapel m ON e.mapel_id = m.mapel_id
            WHERE e.siswa_id = ?
        """, (user['siswa_id'],))
        mapel_list = cursor.fetchall()
        
        if not mapel_list:
            raise ValueError("Belum enroll mata pelajaran")
        
        return mapel_list 

    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        conn.close()

def submit_jawaban(soal_id, siswa_id, jawaban):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO jawaban (siswa_id, soal_id, jawaban)
            VALUES (?, ?, ?)
        """, (siswa_id, soal_id, jawaban))
        conn.commit()

        #Cek apakah semua soal untuk materi ini sudah dijawab oleh siswa
        materi_id = get_materi_id_from_soal(soal_id)
        total_soal = count_soal_in_materi(materi_id)
        total_jawaban = count_jawaban_siswa_di_materi(siswa_id, materi_id)

        if total_jawaban == total_soal:
            nilai = hitung_nilai_quiz(siswa_id, materi_id)
            passing_score = 60

            if nilai >= passing_score:
                next_materi_id = get_next_materi(materi_id)
                unlock_materi(siswa_id, next_materi_id)
            else:
                pass

    except Exception as e:
        print(f"Error submitting answer: {e}")
    finally:
        conn.close()

def hitung_nilai_akhir(siswa_id):
    conn = get_connection()
    try:
        cursor = conn.execute("""
            SELECT COUNT(*) FROM jawaban j
            JOIN soal s ON j.soal_id = s.soal_id
            WHERE j.siswa_id = ? AND j.jawaban = s.jawaban_benar
        """, (siswa_id,))
        nilai = cursor.fetchone()[0]
        print(f"Nilai akhir: {nilai}")
    except Exception as e:
        print(f"Error calculating score: {e}")
    finally:
        conn.close()

# Diskusi Siswa
@bp_siswa.route('/diskusi_siswa', methods=['GET', 'POST'])
def diskusi_siswa():
    if 'user' not in session or session['user'].get('role') != 'siswa':
        return redirect(url_for('login'))
    conn = get_connection()
    user = session['user']
    if request.method == 'POST':
        question_text = request.form.get('question')
        if question_text:
            conn.execute(
                "INSERT INTO pertanyaan_siswa (siswa_id, text) VALUES (?, ?)",
                (user['siswa_id'], question_text)
            )
            conn.commit()
            flash('Pertanyaan berhasil dikirim', 'success')
        else:
            flash('Pertanyaan tidak boleh kosong', 'danger')
        return redirect(url_for('siswa.diskusi_siswa'))
    # Fetch questions and their answers
    questions = conn.execute("""
        SELECT ps.id, ps.text, ps.timestamp, 
               IFNULL(jg.text, '') AS jawaban, jg.timestamp AS jawaban_timestamp,
               u_guru.nama AS nama_guru
        FROM pertanyaan_siswa ps
        LEFT JOIN jawaban_guru jg ON ps.id = jg.pertanyaan_id
        LEFT JOIN guru g ON jg.guru_id = g.guru_id
        LEFT JOIN user u_guru ON g.user_id = u_guru.user_id
        WHERE ps.siswa_id = ?
        ORDER BY ps.timestamp DESC
    """, (user['siswa_id'],)).fetchall()
    conn.close()
    return render_template('diskusi_siswa.html', user=user, questions=questions)

#Lihat Materi yang sudah di enroll
@bp_siswa.route('/materi_siswa')
def daftar_materi_siswa():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    siswa_id = session['user_id']
    daftar_mapel = lihat_materi_enroll(siswa_id)
    return render_template('materi_siswa.html', daftar_mapel=daftar_mapel)

#LIHAT DETAIL MATERI
@bp_siswa.route('/siswa/materi/<int:materi_id>')
def lihat_detail_materi(materi_id):
    if 'user' not in session or session['user']['role'] != 'siswa':
        return redirect(url_for('login'))
    conn = get_connection()
    materi = conn.execute("SELECT * FROM materi WHERE materi_id = ?", (materi_id,)).fetchone()
    conn.close()
    if not materi:
        flash("Materi tidak ditemukan", "danger")
        return redirect(url_for('dashboard_siswa'))
    # Convert full YouTube URL to embed URL if needed (handle youtu.be short links)
    video_url = materi['video_url']
    embed_url = video_url
    if video_url:
        if "watch?v=" in video_url:
            video_id = video_url.split("watch?v=")[-1].split("&")[0]
            embed_url = f"https://www.youtube.com/embed/{video_id}"
        elif "youtu.be/" in video_url:
            video_id = video_url.split("youtu.be/")[-1].split("?")[0]
            embed_url = f"https://www.youtube.com/embed/{video_id}"
    materi = dict(materi)
    materi['video_url'] = embed_url
    return render_template('lihat_detail_materi.html', materi=materi)
            
#Lihat Materi Enroll Helper
def lihat_materi_enroll(siswa_id):
    """
    Mengambil daftar materi/mata pelajaran yang sudah di-enroll oleh siswa.
    Mengembalikan list dictionary dengan mapel_id dan nama_mapel.
    """
    conn = get_connection()
    try:
        query = """
            SELECT m.mapel_id, m.nama_mapel
            FROM enrollment e
            JOIN mapel m ON e.mapel_id = m.mapel_id
            WHERE e.siswa_id = ?
            ORDER BY m.nama_mapel
        """
        cursor = conn.execute(query, (siswa_id,))
        mapel_list = cursor.fetchall()
        # Konversi hasil ke list dict agar mudah dipakai di template
        hasil = [{'mapel_id': row['mapel_id'], 'nama_mapel': row['nama_mapel']} for row in mapel_list]
        return hasil
    except Exception as e:
        print(f"Error melihat materi enroll: {e}")
        return []
    finally:
        conn.close()

@bp_siswa.route('/materi_per_mapel/<int:mapel_id>')
def materi_per_mapel(mapel_id):
    if 'user' not in session or session['user']['role'] != 'siswa':
        return redirect(url_for('login'))
    user_id = session['user']['user_id']
    conn = get_connection()
    materi_rows = conn.execute("SELECT * FROM materi WHERE mapel_id = ?", (mapel_id,)).fetchall()
    mapel_info = conn.execute("SELECT * FROM mapel WHERE mapel_id = ?", (mapel_id,)).fetchone()
    materi_list = []
    for materi in materi_rows:
        materi_dict = dict(materi)
        # Set unlocked based on is_locked status (unlocked if is_locked == 0)
        materi_dict['unlocked'] = (materi['is_locked'] == 0)
        materi_list.append(materi_dict)
    conn.close()
    return render_template('materi_per_mapel.html', materi_list=materi_list, mapel_info=mapel_info)
        
@bp_siswa.route('/materi_enroll')
def materi_enroll():
    if 'user' not in session or session['user']['role'] != 'siswa':
        return redirect(url_for('login'))
    siswa_id = session['user']['siswa_id']
    daftar_mapel = lihat_materi_enroll(siswa_id)
    return render_template('materi_siswa.html', daftar_materi=daftar_mapel)
