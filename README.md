# LearnAnythink

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://learnanythink.streamlit.app/)

LearnAnythink adalah aplikasi belajar berbasis Streamlit yang mengubah satu tujuan belajar menjadi peta topik, materi, latihan soal, dan jadwal ulangan. Semua isinya ditulis model AI dalam bahasa Indonesia.

Kamu menulis apa yang ingin dikuasai, misalnya "dasar fotografi dengan ponsel", lalu memilih level. AI menyusun sekitar 5 sampai 7 topik. Tiap topik punya materi, kuis pilihan ganda atau esai, dan skor yang dipakai untuk menghitung penguasaan. Tutor chat membaca peta topik, materi aktif, dan kesalahan terakhirmu, jadi jawabannya mengikuti posisimu di peta.

Coba langsung di [learnanythink.streamlit.app](https://learnanythink.streamlit.app/).

## Halaman

Navigasi ada di sidebar, bersama pemilih ruang belajar. Satu ruang belajar adalah satu tujuan beserta seluruh topik, materi, soal, dan riwayatnya.

| Halaman | Isinya |
| --- | --- |
| Beranda | Membuat ruang belajar baru, ringkasan (topik dikuasai, rata-rata skor, soal jatuh tempo), dan tombol untuk melanjutkan topik aktif. |
| Tutor | Chat dengan tutor adaptif. Konteksnya bisa seluruh ruang belajar atau satu topik. Tutor menjelaskan dulu, lalu mengajukan satu pertanyaan pemahaman, dan berhenti bertanya kalau kamu minta penjelasan langsung. Bisa melampirkan sampai 4 berkas. |
| Peta Belajar | Daftar topik beserta status dan penguasaannya. Judul, ringkasan, dan tujuan tiap topik bisa diedit, urutannya digeser, topiknya dihapus, atau topik baru ditambah manual. Peta juga bisa disusun ulang oleh AI. |
| Materi | Materi per topik: tujuan, beberapa bagian bacaan, istilah kunci, contoh, dan rangkuman. Materi bisa ditandai selesai atau ditulis ulang. |
| Latihan | Kuis pilihan ganda (4 opsi) atau esai, untuk satu topik atau seluruh ruang belajar. Tingkat kesulitan mudah, sedang, atau sulit, dengan 3 sampai 10 soal. Esai dinilai AI terhadap poin kunci. Ulangan terjadwal juga dikerjakan di sini. |
| Bank Soal | Semua soal yang pernah dibuat, bisa disaring menurut topik, jenis, dan kata kunci. Tiap soal menampilkan jadwal ulangannya dan bisa dihapus. |
| Progres | Penguasaan, rata-rata skor, rentetan hari, soal jatuh tempo, grafik penguasaan per topik, topik di bawah 60%, kesalahan terakhir, riwayat latihan, dan jurnal. |
| Pengaturan | Mengubah nama, tujuan, dan level ruang belajar. Menghapus satu ruang belajar atau seluruh data. |

Lampiran di Tutor bisa berupa gambar (png, jpg, jpeg, webp, gif) atau berkas teks (txt, md, csv, json, py, pdf). Dari PDF, 20 halaman pertama dibaca. Gambar dikirim ke model sebagai blok `image_url`, jadi model yang dipilih perlu mendukung input gambar.

## Menjalankan di komputer sendiri

Membutuhkan Python 3.11 atau lebih baru dan satu API key untuk endpoint yang kompatibel dengan OpenAI. Bawaannya [Token Harbor](https://tokenharbor.ai).

```bash
git clone https://github.com/Raka-Mahendra/learnanythink.git
cd learnanythink
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # lalu isi TH_API_KEY di berkas .env
streamlit run streamlit_app.py
```

Aplikasi terbuka di `http://localhost:8501`. Basis data SQLite dibuat otomatis di `.data/learning.db`.

Tanpa API key, aplikasi tetap terbuka, tetapi setiap fitur yang memanggil AI (menyusun peta, menulis materi, membuat soal, menilai esai, tutor) menampilkan pesan "Layanan AI belum siap".

## Konfigurasi

Pengaturan AI hanya dibaca dari `st.secrets` (`.streamlit/secrets.toml`) dan dari environment atau berkas `.env`. Tidak ada halaman pengaturan AI di antarmuka. Nilai di secrets dibaca lebih dulu, dan boleh diletakkan di tingkat atas atau di bagian `[tokenharbor]` atau `[llm]`. Contoh isinya ada di [`.env.example`](.env.example) dan [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example).

| Variabel | Bawaan | Alias yang juga dibaca |
| --- | --- | --- |
| `TH_API_KEY` | kosong | `TOKEN_HARBOR_API_KEY`, `LA_API_KEY` |
| `TH_BASE_URL` | `https://tokenharbor.ai/v1` | `TOKEN_HARBOR_BASE_URL`, `LA_BASE_URL` |
| `TH_MODEL` | `deepseek-v4.1-flash:free` | `TOKEN_HARBOR_MODEL`, `LA_MODEL` |
| `LA_DB_PATH` | `.data/learning.db` | tidak ada |

Endpoint lain yang kompatibel dengan OpenAI bisa dipakai dengan mengubah `TH_BASE_URL` dan `TH_MODEL`. Hal itu belum diuji. Model juga perlu bisa membalas dengan JSON, karena peta, materi, soal, dan nilai esai diminta dalam format JSON yang divalidasi dengan Pydantic dan diulang satu kali bila tidak sesuai.

Catatan: `.env.example` dan `secrets.toml.example` masih menyebut `LA_DEMO`. Mode demo sudah dihapus dari kode, jadi variabel itu tidak berpengaruh.

## Cara penguasaan dan ulangan dihitung

Penguasaan tiap topik bernilai 0 sampai 100:

```
penguasaan = 20 (jika materi selesai) + 0,5 x skor terbaik + 0,3 x rata-rata 3 sesi terakhir
```

Topik berstatus Paham bila penguasaannya 80 atau lebih dan materinya sudah ditandai selesai. Selain itu statusnya Sedang belajar (bila materi selesai atau sudah ada sesi latihan) atau Belum mulai.

Setiap soal yang dijawab masuk ke jadwal ulangan dengan algoritma mirip SM-2. Kualitas jawaban dinilai 2 sampai 5: benar atau nilai 85 ke atas bernilai 5, nilai 70 sampai 84 bernilai 4, 50 sampai 69 bernilai 3, sisanya 2. Kualitas di bawah 3 mengembalikan soal ke jadwal besok. Dari kualitas 3 ke atas, interval berjalan 1 hari, 3 hari, lalu interval sebelumnya dikali faktor kemudahan (mulai 2,5, dibatasi antara 1,3 dan 2,8).

## Struktur proyek

```
streamlit_app.py   router, konfigurasi halaman, pemilih ruang belajar di sidebar
pages.py           daftar halaman, rute, dan ikon
routes/            pembungkus tipis per halaman untuk st.navigation
views/             isi tiap halaman
services/          llm, prompts, schemas, learning, quiz, tutor, attachments
db.py              skema SQLite dan seluruh query
models.py          dataclass domain
state.py           session state dan helper navigasi
ui/layout.py       helper tampilan dari komponen bawaan Streamlit
tests/             unit test dan AppTest
docs/specs/        dokumen desain
Logo Kit/          logo dan panduan pemakaiannya
```

Semua SQL ada di `db.py`, dan view tidak menulis SQL. Antarmukanya memakai widget bawaan Streamlit tanpa CSS kustom, dengan tema gelap yang diatur di `.streamlit/config.toml`. Warnanya mengikuti [panduan logo](Logo%20Kit/PANDUAN-LOGO.md). Keputusan desain awal tercatat di [`docs/specs`](docs/specs/2026-11-25-learnanythink-deeptutor-design.md).

## Pengujian

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Tes mencakup perhitungan penguasaan, jadwal ulangan, repository SQLite, parsing JSON, prioritas konfigurasi, daftar halaman, dan satu alur AppTest yang membuat ruang belajar. Tes berjalan tanpa API key dan tanpa memanggil layanan AI.

## Deploy ke Streamlit Community Cloud

1. Hubungkan repositori ini, pilih branch `main`, dan isi *Main file path* dengan `streamlit_app.py`.
2. Di pengaturan aplikasi, buka Secrets dan tempel isi `.streamlit/secrets.toml.example` dengan nilai asli.

## Batasan

- Aplikasi dirancang untuk satu pengguna. Tidak ada login, dan semua ruang belajar tersimpan di satu basis data. Di instance publik, semua pengunjung melihat dan mengubah data yang sama.
- Data disimpan di berkas SQLite lokal. Di hosting yang sistem berkasnya bersifat sementara, data bisa hilang ketika aplikasi dimulai ulang.
- Materi, soal, dan nilai esai dibuat model AI dan bisa keliru. Periksa lagi untuk topik yang penting.
- Lampiran hanya dipakai dalam satu percakapan tutor. Lampiran tidak diindeks dan tidak dipakai untuk menyusun materi.

## Lisensi

Kode di repositori ini dilisensikan di bawah [MIT License](LICENSE). Folder `Logo Kit/` tidak termasuk dalam lisensi ini.
