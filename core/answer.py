#core/answer.py
import sqlite3
from db.conn import get_connection
import core.auth

def submit_answer(question_id, answer_text):
    if not core.auth.current_user or core.auth.current_user['role'] != 'siswa':
        print("Hanya siswa yang bisa menjawab soal")
        return

    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM answer WHERE question_id = ? AND student_id = ?",
            (question_id, core.auth.current_user['id'])
        ).fetchone()
        
        if existing:
            print("Anda sudah menjawab soal ini sebelumnya")
            return

        # Dapatkan kunci jawaban
        question = conn.execute(
            "SELECT correct_answer, max_score FROM question WHERE id = ?",
            (question_id,)
        ).fetchone()

        # Hitung skor
        score = question['max_score'] if answer_text.lower() == question['correct_answer'].lower() else 0

        conn.execute(
            "INSERT INTO answer (question_id, student_id, answer_text, score) "
            "VALUES (?, ?, ?, ?)",
            (question_id, core.auth.current_user['id'], answer_text, score)
        )
        conn.commit()
        print(f"Jawaban tersimpan! Skor Anda: {score}/{question['max_score']}")
    except sqlite3.Error as e:
        print(f"Gagal menyimpan jawaban: {e}")
    finally:
        conn.close()