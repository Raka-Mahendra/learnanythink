# LearnAnythink — Desain Loop Belajar AI (2026-11-25)

Status: disetujui. Implementasi mengikuti dokumen ini.

> Revisi implementasi: tema gelap Ink, pengaturan AI hanya lewat secrets/environment,
> istilah "ruang belajar", dan seluruh ikon emoji diganti teks atau Material Symbols.

## Tujuan

Mengubah LearnAnythink dari alur linear (topik → ringkasan → artikel → kuis)
menjadi workspace belajar yang meniru inti DeepTutor: peta penguasaan, materi,
latihan, bank soal, ulangan terjadwal, tutor adaptif, dan progres.

## Keputusan yang sudah disetujui

| Topik | Keputusan |
| --- | --- |
| Cakupan | Loop belajar lengkap, tanpa RAG dokumen |
| Tampilan | Widget default Streamlit, dark theme |
| Warna | Latar Ink `#14122B`, permukaan `#1E1B38`, teks Mist `#F6F4FF`, tombol `#2E7D5B`, aksen hijau logo `#4ADD82` |
| AI | Token Harbor, endpoint OpenAI-compatible `https://tokenharbor.ai/v1` |
| Konfigurasi | Secrets / environment saja; pengaturan AI tidak ditampilkan di UI |
| Gaya tutor | Adaptif (menjelaskan lalu menawarkan cek pemahaman) |
| Penyimpanan | SQLite `.data/learning.db`, satu pengguna |
| Arsitektur | Modular monolith: `app.py` router, `views/`, `services/`, `db.py` |
| Dibersihkan | `design/`, `ui/styles.css`, `ui/components.py`, `services/images.py`, `services/papers.py` |

## Alur pengguna

1. Buat workspace: tujuan, level, judul opsional.
2. AI menyusun 5–7 topik (objectives + ringkasan).
3. Buka topik → AI menulis materi terstruktur.
4. Tandai materi selesai → buat kuis PG/esai.
5. Jawaban dinilai, penjelasan disimpan, soal masuk bank soal.
6. Soal salah masuk jadwal ulangan SM-2 ringan.
7. Tutor chat membawa konteks workspace, topik, materi, dan kesalahan terakhir.
8. Progres menampilkan mastery, skor, topik lemah, streak, dan jurnal.

## Navigasi

`Beranda · Tutor · Peta Belajar · Materi · Latihan · Bank Soal · Progres · Pengaturan`

Pemilih workspace dan tombol workspace baru ada di sidebar.

## Data (SQLite)

Tabel: `meta`, `workspaces`, `topics`, `lessons`, `chats`, `messages`,
`questions`, `quiz_sessions`, `attempts`, `reviews`, `journal`.

- `topics.objectives` dan `lessons.body` disimpan sebagai JSON.
- `quiz_sessions.question_ids` menyimpan urutan soal satu sesi.
- `reviews` menyimpan `due_at`, `interval_days`, `ease`, `reps`, `lapses`.
- Semua akses SQL lewat `db.py`; view tidak menulis SQL.

## Lapisan AI

- SDK `openai`, base URL Token Harbor.
- Urutan konfigurasi: override sesi → `st.secrets` → environment.
- Key tidak pernah ditulis ke disk/log; model pilihan boleh disimpan sebagai preferensi.
- `stream_chat`, `json_call` (pydantic + satu retry), `list_models`, `health`.
- Error dipetakan ke pesan Indonesia yang bisa ditindaklanjuti.
- Konteks tutor dibatasi jumlah karakter; tidak ada vektor/RAG.

## Mesin belajar

- Peta: 5–7 topik, bersih dari duplikat.
- Materi: tujuan, 3–6 bagian, istilah kunci, contoh, rangkuman.
- Kuis: PG 4 opsi satu benar; esai dengan key points + model answer.
- Mastery: `20% materi selesai + 50% skor terbaik + 30% rata-rata 3 sesi terakhir`.
  Status `Paham` bila mastery ≥ 80 dan materi selesai.
- SM-2 ringan: kualitas < 3 → ulang besok; selain itu interval 1 → 3 → `interval × ease`.

## Pengalaman kosong/gagal

- Tanpa key → mode demo dengan banner, seluruh loop tetap jalan.
- Workspace/peta/materi/bank/ulangan kosong → empty state dengan satu aksi.
- Error API → `st.error` yang menyebut penyebab dan tombol coba lagi.
- Generasi panjang → `st.status` dengan tahap yang jelas.

## Struktur berkas

```
app.py                 router, page config, sidebar workspace
db.py                  koneksi, migrasi, repository
models.py              dataclass domain
state.py               session state
services/llm.py        Token Harbor
services/prompts.py    prompt
services/schemas.py    skema pydantic
services/attachments.py lampiran PDF/teks
services/tutor.py      konteks + balasan tutor
services/learning.py   peta, materi, mastery
services/quiz.py       kuis, penilaian, SM-2
services/demo.py       fixture mode demo
views/                 delapan halaman
routes/                pembungkus tipis untuk st.navigation
ui/layout.py           helper native
tests/                 unit + AppTest
```

## Pengujian

- Unit: SM-2, mastery, repository, parsing JSON, prioritas konfigurasi.
- AppTest: mode demo, buat workspace → peta → materi → kuis → bank soal → ulangan → progres.
- Tidak ada tes yang memanggil API berbayar.
