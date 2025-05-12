--Tabel user
CREATE TABLE IF NOT EXISTS user(
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN('siswa', 'guru'))
);

--Tabel guru
CREATE TABLE IF NOT EXISTS guru(
    guru_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    mapel_id INTEGER,
    nip TEXT NOT NULL UNIQUE,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE,
    FOREIGN KEY (mapel_id) REFERENCES mapel(mapel_id) ON DELETE CASCADE
);

--Tabel siswa
CREATE TABLE IF NOT EXISTS siswa(
    siswa_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    nis TEXT NOT NULL UNIQUE,
    kelas TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
);

--Tabel enrollment
CREATE TABLE IF NOT EXISTS enrollment(
    enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mapel_id INTEGER,
    siswa_id INTEGER,
    FOREIGN KEY (mapel_id) REFERENCES mapel(mapel_id) ON DELETE CASCADE,
    FOREIGN KEY (siswa_id) REFERENCES siswa(siswa_id) ON DELETE CASCADE
);

--Tabel mata pelajaran
CREATE TABLE IF NOT EXISTS mapel(
    mapel_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama_mapel TEXT NOT NULL UNIQUE
);

-- Insert data mapel default
INSERT OR IGNORE INTO mapel (nama_mapel) VALUES
    ('MATEMATIK'),
    ('BAHASA INDONESIA'),
    ('IPA'),
    ('IPS'),
    ('PENDIDIKAN AGAMA ISLAM'),
    ('BAHASA SUNDA'),
    ('BAHASA INGGRIS');

--Tabel soal
CREATE TABLE IF NOT EXISTS soal(
    soal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mapel_id INTEGER,
    guru_id INTEGER,
    pertanyaan TEXT NOT NULL,
    opsi_a TEXT NOT NULL,
    opsi_b TEXT NOT NULL,
    opsi_c TEXT NOT NULL,
    opsi_d TEXT NOT NULL,
    skor INTEGER NOT  NULL DEFAULT 10,
    jawaban TEXT NOT NULL CHECK (jawaban IN ('A','B','C','D')),
    FOREIGN KEY (mapel_id) REFERENCES mapel(mapel_id) ON DELETE CASCADE,
    FOREIGN KEY (guru_id) REFERENCES guru(guru_id) ON DELETE CASCADE
);

--Tabel nilai akhir siswa
CREATE TABLE IF NOT EXISTS nilai(
    nilai_id INTEGER PRIMARY KEY AUTOINCREMENT,
    siswa_id INTEGER,
    mapel_id INTEGER,
    jawab_id INTEGER,
    skor INTEGER NOT NULL,
    indeks TEXT NOT NULL,
    FOREIGN KEY(siswa_id) REFERENCES siswa(siswa_id) ON DELETE CASCADE,
    FOREIGN KEY(mapel_id) REFERENCES mapel(mapel_id) ON DELETE CASCADE,
    FOREIGN KEY (jawab_id) REFERENCES jawaban(jawab_id) ON DELETE CASCADE
);

--Tabel jawaban siswa
CREATE TABLE IF NOT EXISTS jawaban(
    jawab_id INTEGER PRIMARY KEY AUTOINCREMENT,
    soal_id INTEGER NOT NULL,
    siswa_id INTEGER NOT NULL,
    jawaban TEXT NOT NULL,
    mapel_id INTEGER NOT NULL,
    koreksi INTEGER,
    submit DATETIME DEFAULT CURRENT_TIMESTAMP, UNIQUE(soal_id, siswa_id),
    FOREIGN KEY(soal_id) REFERENCES soal(soal_id) ON DELETE CASCADE,
    FOREIGN KEY(siswa_id) REFERENCES siswa(siswa_id) ON DELETE CASCADE
);

--Tabel log aktivitas
CREATE TABLE IF NOT EXISTS log_aktivitas(
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    aktivitas TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE 
);