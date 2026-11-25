# LearnAnythink — Panduan Logo (1 halaman)

**Konsep:** Tile Flow. Empat potongan seperempat lingkaran dari satu ubin, arahnya diputar. Celah di tengah membentuk kilau empat arah. Satu warna saja, tanpa warna sekunder. Ubin yang sama bisa diputar menjadi pola latar.

## Warna
| Nama | HEX | Pemakaian |
|---|---|---|
| Green (primer) | #4ADD82 | seluruh simbol; terbaik di atas Ink (10.4:1) |
| Ink (netral) | #14122B | teks wordmark, latar gelap, simbol pada versi latar terang |
| Mist (netral) | #F6F4FF | latar terang |
Ink dan Mist hanya warna netral untuk teks dan latar, bukan warna merek kedua.

**Penting soal kontras:** hijau #4ADD82 di atas putih hanya 1,8:1 (di bawah batas 3:1 untuk logo). Karena itu:
- Latar gelap (Ink): pakai `lockup-horizontal-dark` / `lockup-stacked-dark` (versi utama).
- Latar terang: pakai `*-light-safe` (seluruh simbol Ink) atau versi hitam.
- Versi hijau di atas putih (`lockup-horizontal`, `symbol-color`) tetap disediakan, tetapi hindari untuk ukuran kecil atau cetak penting.

## Huruf
Wordmark: Poppins Medium ("Learn") + Poppins Bold ("Anythink"), sudah diubah jadi outline di SVG. Poppins berlisensi SIL OFL, boleh untuk logo.

## Versi file
- Simbol: `symbol-color`, `symbol-on-dark`, `symbol-light-safe`, `symbol-black`, `symbol-white`, `symbol-small` (celah lebih lebar untuk di bawah 32 px)
- Lockup: `lockup-horizontal` (+ dark, light-safe, black, white), `lockup-stacked` (+ dark)
- `app-icon` dan `favicon-source` (hijau di atas Ink), serta folder `icons/` (favicon.ico, 16/32/48, 180, 192, 512, site.webmanifest, head-snippet.html)

## Ruang aman dan ukuran minimum
- Ruang kosong di sekeliling logo: minimal selebar satu ubin (±1/2 tinggi simbol).
- Simbol: minimal 24 px; di bawah itu pakai `symbol-small`. Lockup horizontal: minimal 120 px lebar.

## Jangan
- Jangan menambahkan warna lain ke ubin, bayangan, atau gradasi.
- Jangan menyempitkan celah antar ubin dan jangan memutar simbol utuh.
- Jangan mengetik ulang wordmark dengan font lain.

## Catatan
Belum ada pemeriksaan merek dagang. Cek dulu ke database merek (misalnya PDKI) dan pencarian gambar terbalik sebelum dipakai resmi.
