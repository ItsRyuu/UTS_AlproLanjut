-- Tabel user lama
CREATE TABLE IF NOT EXISTS user(
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN('guru', 'siswa'))
);

-- Tabel guru
CREATE TABLE IF NOT EXISTS guru(
    guru_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    nip TEXT NOT NULL UNIQUE,
    mapel_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE,
    FOREIGN KEY (mapel_id) REFERENCES mapel(mapel_id) ON DELETE CASCADE
);

-- Tabel siswa
CREATE TABLE IF NOT EXISTS siswa(
    siswa_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    nis TEXT NOT NULL UNIQUE,
    kelas TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
);

-- Tabel enrollment
CREATE TABLE IF NOT EXISTS enrollment(
    enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mapel_id INTEGER,
    siswa_id INTEGER,
    FOREIGN KEY (mapel_id) REFERENCES mapel(mapel_id) ON DELETE CASCADE,
    FOREIGN KEY (siswa_id) REFERENCES siswa(siswa_id) ON DELETE CASCADE
);

-- Tabel mata pelajaran
CREATE TABLE IF NOT EXISTS mapel(
    mapel_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama_mapel TEXT NOT NULL UNIQUE
);

-- Insert data mapel default
INSERT OR IGNORE INTO mapel (nama_mapel) VALUES
    ('MATEMATIKA'),
    ('BAHASA INDONESIA'),
    ('IPA'),
    ('IPS'),
    ('PENDIDIKAN AGAMA ISLAM'),
    ('BAHASA SUNDA'),
    ('BAHASA INGGRIS');

-- Tabel soal
CREATE TABLE IF NOT EXISTS soal(
    soal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mapel_id INTEGER,
    guru_id INTEGER,
    pertanyaan TEXT NOT NULL,
    opsi_a TEXT NOT NULL,
    opsi_b TEXT NOT NULL,
    opsi_c TEXT NOT NULL,
    opsi_d TEXT NOT NULL,
    skor INTEGER NOT NULL DEFAULT 10,
    jawaban TEXT NOT NULL CHECK (jawaban IN ('A','B','C','D')),
    FOREIGN KEY (mapel_id) REFERENCES mapel(mapel_id) ON DELETE CASCADE,
    FOREIGN KEY (guru_id) REFERENCES guru(guru_id) ON DELETE CASCADE
);

-- Tabel jawaban siswa
CREATE TABLE IF NOT EXISTS jawaban(
    jawab_id INTEGER PRIMARY KEY AUTOINCREMENT,
    soal_id INTEGER NOT NULL,
    siswa_id INTEGER NOT NULL,
    jawaban TEXT NOT NULL,
    mapel_id INTEGER NOT NULL,
    koreksi INTEGER,
    submit DATETIME DEFAULT CURRENT_TIMESTAMP, 
    UNIQUE(soal_id, siswa_id),
    FOREIGN KEY(soal_id) REFERENCES soal(soal_id) ON DELETE CASCADE,
    FOREIGN KEY(siswa_id) REFERENCES siswa(siswa_id) ON DELETE CASCADE
);

-- Tabel nilai akhir siswa
CREATE TABLE IF NOT EXISTS nilai(
    nilai_id INTEGER PRIMARY KEY AUTOINCREMENT,
    siswa_id INTEGER,
    mapel_id INTEGER,
    materi_id INTEGER, -- Ditambahkan untuk skor per materi
    -- jawab_id INTEGER, -- Bisa dipertimbangkan untuk dihapus jika agregat per materi
    skor INTEGER NOT NULL,
    indeks TEXT NOT NULL,
    FOREIGN KEY(siswa_id) REFERENCES siswa(siswa_id) ON DELETE CASCADE,
    FOREIGN KEY(mapel_id) REFERENCES mapel(mapel_id) ON DELETE CASCADE,
    FOREIGN KEY(materi_id) REFERENCES materi(materi_id) ON DELETE CASCADE -- Constraint baru
);

-- Tabel log aktivitas
CREATE TABLE IF NOT EXISTS log_aktivitas(
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    aktivitas TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE 
);

-- Tabel pertanyaan siswa
CREATE TABLE IF NOT EXISTS pertanyaan_siswa(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    siswa_id INTEGER,
    text TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (siswa_id) REFERENCES siswa(siswa_id) ON DELETE CASCADE
);

-- Tabel jawaban guru
CREATE TABLE IF NOT EXISTS jawaban_guru(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guru_id INTEGER,
    pertanyaan_id INTEGER,
    text TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (guru_id) REFERENCES guru(guru_id) ON DELETE CASCADE,
    FOREIGN KEY (pertanyaan_id) REFERENCES pertanyaan_siswa(id) ON DELETE CASCADE
);

-- Ganti nama table user menjadi user_lama
ALTER TABLE user RENAME TO user_lama;

-- Buat tabel user baru
CREATE TABLE user (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN('admin', 'guru', 'siswa'))
);

-- Salin data dari tabel user lama ke user
INSERT INTO user (user_id, nama, email, password, role)
SELECT user_id, nama, email, password, role FROM user_lama;

-- hapus tabel user
DROP TABLE user_lama;

-- Insert akun admin
INSERT OR IGNORE INTO user (nama, email, password, role) VALUES ('admin', 'admin@gmail.com', 'admin', 'admin');

-- tabel materi
CREATE TABLE IF NOT EXISTS materi(
    materi_id INTEGER PRIMARY KEY AUTOINCREMENT,
    judul TEXT NOT NULL,
    deskripsi TEXT,
    mapel_id INTEGER,
    video_url TEXT,
    is_locked INTEGER DEFAULT 0 NOT NULL,
    FOREIGN KEY (mapel_id) REFERENCES mapel(mapel_id)
);

-- tambahkan kolom materi_id ke tabel soal
ALTER TABLE soal ADD COLUMN materi_id INTEGER REFERENCES materi(materi_id);

-- agar log aktivitas siswa muncul di dashboard guru
SELECT la.aktivitas, la.timestamp, u.nama AS nama_siswa
FROM log_aktivitas la
JOIN user u ON la.user_id = u.user_id
JOIN siswa s ON s.user_id = u.user_id
JOIN enrollment e ON e.siswa_id = s.siswa_id
JOIN guru g ON g.mapel_id = e.mapel_id
WHERE g.guru_id = ?
ORDER BY la.timestamp DESC