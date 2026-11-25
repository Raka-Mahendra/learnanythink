"""Offline fixtures used when no Token Harbor key is configured.

The sample topic is the Big Bounce, so every screen can be exercised without
spending a token. Real providers replace these functions through ``services``.
"""

from __future__ import annotations

import time
from typing import Iterator

from models import Topic

SAMPLE_TITLE = "Big Bounce"
SAMPLE_GOAL = "Memahami teori Big Bounce dan posisinya dalam kosmologi modern"

MC_POOL: list[dict] = [
    {
        "text": "Apa yang terjadi pada titik pantulan menurut teori Big Bounce?",
        "options": [
            "Alam semesta berhenti berkembang selamanya",
            "Alam semesta berbalik dari menyusut menjadi mengembang",
            "Bintang pertama terbentuk",
            "Waktu berhenti",
        ],
        "answer": 1,
        "explanation": "Big Bang dipandang sebagai titik pantulan, bukan awal mutlak.",
    },
    {
        "text": "Siapa yang memulai gagasan alam semesta berosilasi pada 1930-an?",
        "options": ["Hubble", "Hawking", "Tolman", "Penrose"],
        "answer": 2,
        "explanation": "Gagasan osilasi dimulai dari Tolman pada 1930-an.",
    },
    {
        "text": "Penemuan apa pada 1998 yang membuat Big Crunch kurang mungkin?",
        "options": ["Gelombang gravitasi", "Energi gelap", "Radiasi CMB", "Lubang hitam"],
        "answer": 1,
        "explanation": "Energi gelap mempercepat pengembangan alam semesta.",
    },
    {
        "text": "Apa peran Loop Quantum Cosmology pada model pantulan?",
        "options": [
            "Membuat gravitasi menarik lebih kuat pada kepadatan ekstrem",
            "Membuat gravitasi menolak pada kepadatan ekstrem",
            "Menghapus kebutuhan akan inflasi",
            "Menjelaskan pembentukan lubang hitam",
        ],
        "answer": 1,
        "explanation": "Pada skala Planck efek kuantum membuat gravitasi menolak.",
    },
    {
        "text": "Apa yang dimaksud dengan model siklik atau ekpirotik?",
        "options": [
            "Tabrakan berulang antar-brane yang memicu Big Bang baru",
            "Alam semesta yang mengembang tanpa henti",
            "Dua alam semesta yang tidak pernah bersentuhan",
            "Ledakan tunggal yang tidak berulang",
        ],
        "answer": 0,
        "explanation": "Pantulan dihasilkan oleh tabrakan antar-brane yang berulang.",
    },
    {
        "text": "Apa yang dicegah oleh torsi Einstein-Cartan dalam model ini?",
        "options": ["Inflasi", "Singularitas", "Energi gelap", "Radiasi latar"],
        "answer": 1,
        "explanation": "Spin partikel mencegah singularitas dan memicu pantulan.",
    },
    {
        "text": "Mengapa model Big Crunch melemah setelah 1998?",
        "options": [
            "Karena pengembangan alam semesta justru makin cepat",
            "Karena gravitasi terbukti tidak ada",
            "Karena CMB tidak terdeteksi",
            "Karena materi gelap habis",
        ],
        "answer": 0,
        "explanation": "Energi gelap membuat penyusutan ulang sulit terjadi.",
    },
    {
        "text": "Jejak apa yang dicari peneliti untuk menguji gagasan ini?",
        "options": [
            "Pola pada CMB atau gelombang gravitasi primordial",
            "Warna bintang di galaksi terdekat",
            "Kecepatan rotasi Bima Sakti",
            "Umur batuan di Bumi",
        ],
        "answer": 0,
        "explanation": "Pola CMB dan gelombang gravitasi primordial adalah bidikan utamanya.",
    },
    {
        "text": "Apa kelebihan utama model Big Bounce?",
        "options": [
            "Menghindari singularitas dan tidak memerlukan awal dari ketiadaan",
            "Menjelaskan asal materi gelap",
            "Membuktikan inflasi salah",
            "Menghapus kebutuhan akan gravitasi kuantum",
        ],
        "answer": 0,
        "explanation": "Model ini tidak membutuhkan titik awal yang tak terhingga padat.",
    },
    {
        "text": "Masalah apa yang belum tuntas pada model siklik?",
        "options": ["Masalah entropi", "Masalah warna", "Masalah horizon", "Masalah flatness"],
        "answer": 0,
        "explanation": "Entropi menumpuk pada setiap siklus yang berulang.",
    },
    {
        "text": "Bagaimana Big Bang dipandang dalam kerangka Big Bounce?",
        "options": [
            "Sebagai titik pantulan, bukan awal mutlak",
            "Sebagai akhir dari seluruh siklus",
            "Sebagai ilusi pengamatan",
            "Sebagai peristiwa lokal di satu galaksi",
        ],
        "answer": 0,
        "explanation": "Big Bang menjadi satu peristiwa pantulan di antara banyak siklus.",
    },
    {
        "text": "Mengapa inflasi masih lebih diterima dibanding model pantulan?",
        "options": [
            "Karena lebih cocok dengan data CMB",
            "Karena lebih tua usianya",
            "Karena lebih sederhana secara matematis",
            "Karena sudah dibuktikan di laboratorium",
        ],
        "answer": 0,
        "explanation": "Data CMB sejauh ini lebih cocok dengan skenario inflasi.",
    },
]

ESSAY_POOL: list[dict] = [
    {
        "text": "Jelaskan ide utama teori Big Bounce dengan kata-katamu sendiri.",
        "key_points": [
            "Alam semesta tidak bermula dari singularitas",
            "Fase menyusut lalu berbalik mengembang",
            "Big Bang adalah titik pantulan",
        ],
        "model_answer": (
            "Teori Big Bounce menyatakan alam semesta tidak dimulai dari titik tak "
            "terhingga padat. Alam semesta sebelumnya menyusut, lalu berbalik mengembang "
            "pada kepadatan ekstrem; peristiwa pantulan itulah yang kita sebut Big Bang."
        ),
    },
    {
        "text": "Bandingkan model Big Bang standar dan Big Bounce dari sisi titik awal alam semesta.",
        "key_points": [
            "Big Bang standar bermula dari singularitas",
            "Big Bounce tidak memiliki singularitas awal",
            "Big Bounce menempatkan siklus sebelum siklus sekarang",
        ],
        "model_answer": (
            "Model Big Bang standar menganggap alam semesta bermula dari singularitas. "
            "Big Bounce menolak titik awal tunggal dan menempatkan pantulan sebagai "
            "peristiwa yang bisa berulang, sehingga tidak ada awal dari ketiadaan."
        ),
    },
    {
        "text": "Mengapa penemuan energi gelap pada 1998 melemahkan model Big Crunch?",
        "key_points": [
            "Energi gelap mempercepat pengembangan",
            "Penyusutan ulang menjadi sulit terjadi",
            "Siklus osilasi kehilangan salah satu syaratnya",
        ],
        "model_answer": (
            "Energi gelap membuat pengembangan alam semesta makin cepat, bukan melambat. "
            "Tanpa perlambatan, alam semesta sulit menyusut kembali, sehingga gagasan "
            "osilasi sederhana kehilangan salah satu syarat utamanya."
        ),
    },
    {
        "text": "Jelaskan bagaimana Loop Quantum Cosmology menjelaskan pantulan alam semesta.",
        "key_points": [
            "Efek kuantum bekerja pada skala Planck",
            "Gravitasi berubah menjadi menolak",
            "Kepadatan ekstrem memicu pembalikan arah",
        ],
        "model_answer": (
            "Pada skala Planck, efek kuantum membuat gravitasi menolak alih-alih menarik. "
            "Ketika alam semesta menyusut sampai kepadatan ekstrem, gaya tolak itu "
            "membalikkan arah penyusutan menjadi pengembangan."
        ),
    },
    {
        "text": "Apa keterbatasan bukti observasi teori ini dan bagaimana peneliti mencarinya?",
        "key_points": [
            "Belum ada bukti observasi langsung",
            "Peneliti mencari pola pada CMB",
            "Gelombang gravitasi primordial menjadi bidikan lain",
        ],
        "model_answer": (
            "Sejauh ini belum ada bukti observasi langsung. Peneliti mencari jejak siklus "
            "sebelumnya pada pola radiasi latar mikrowave dan pada gelombang gravitasi "
            "primordial yang mungkin masih tersisa."
        ),
    },
    {
        "text": "Mengapa masalah entropi menjadi ganjalan utama model siklik?",
        "key_points": [
            "Entropi cenderung bertambah setiap siklus",
            "Siklus berulang menumpuk ketidakteraturan",
            "Model perlu mekanisme pengosongan entropi",
        ],
        "model_answer": (
            "Entropi cenderung bertambah, sehingga setiap siklus akan mewarisi "
            "ketidakteraturan dari siklus sebelumnya. Tanpa mekanisme yang mengosongkan "
            "entropi, siklus tidak bisa berulang secara identik."
        ),
    },
    {
        "text": "Bagaimana torsi Einstein-Cartan bekerja dalam model pantulan?",
        "key_points": [
            "Spin partikel memberi torsi pada ruang-waktu",
            "Torsi mencegah singularitas",
            "Pantulan terjadi sebelum kepadatan tak terhingga",
        ],
        "model_answer": (
            "Spin partikel memberi torsi pada ruang-waktu. Torsi itu bekerja seperti "
            "tekanan yang mencegah kepadatan mencapai nilai tak terhingga, sehingga "
            "penyusutan berbalik menjadi pengembangan sebelum singularitas tercapai."
        ),
    },
    {
        "text": "Menurutmu, apa langkah berikutnya yang paling masuk akal untuk menguji teori ini?",
        "key_points": [
            "Menguji prediksi pola CMB",
            "Menyiapkan deteksi gelombang gravitasi primordial",
            "Membandingkan model dengan data inflasi",
        ],
        "model_answer": (
            "Langkah paling masuk akal adalah membuat prediksi yang bisa dibedakan dari "
            "inflasi, lalu mengujinya pada data CMB berpresisi tinggi dan pada pencarian "
            "gelombang gravitasi primordial."
        ),
    },
]

TOPICS = [
    {
        "title": "Gagasan dasar Big Bounce",
        "summary": "Alam semesta menyusut lalu memantul, bukan bermula dari singularitas.",
        "objectives": [
            "Menjelaskan perbedaan Big Bang standar dan Big Bounce",
            "Menyebutkan peran titik pantulan",
            "Mengenali asumsi utama model",
        ],
    },
    {
        "title": "Bukti dan latar observasi",
        "summary": "Data CMB dan energi gelap membentuk batas pengujian model.",
        "objectives": [
            "Menjelaskan apa yang diukur dari CMB",
            "Menghubungkan energi gelap dengan sulitnya Big Crunch",
            "Menilai kekuatan bukti yang tersedia",
        ],
    },
    {
        "title": "Loop Quantum Cosmology",
        "summary": "Efek kuantum pada skala Planck dapat membalik arah penyusutan.",
        "objectives": [
            "Menjelaskan mengapa gravitasi dapat menolak pada kepadatan ekstrem",
            "Mengaitkan skala Planck dengan titik pantulan",
            "Membedakan klaim model dari bukti langsung",
        ],
    },
    {
        "title": "Model siklik dan torsi Einstein-Cartan",
        "summary": "Siklus berulang dan spin partikel menawarkan mekanisme pantulan.",
        "objectives": [
            "Menjelaskan model ekpirotik secara ringkas",
            "Menyebutkan fungsi torsi Einstein-Cartan",
            "Membandingkan dua mekanisme pantulan",
        ],
    },
    {
        "title": "Kritik, entropi, dan status riset",
        "summary": "Masalah entropi dan data inflasi masih menjadi tantangan utama.",
        "objectives": [
            "Menjelaskan masalah entropi pada model siklik",
            "Membandingkan prediksi dengan inflasi",
            "Merumuskan uji observasi yang mungkin",
        ],
    },
]

LESSON_SECTIONS = [
    [
        (
            "Dari singularitas ke pantulan",
            "Model Big Bang standar membayangkan alam semesta bermula dari keadaan yang "
            "sangat padat lalu mengembang. Big Bounce mempertahankan gagasan pengembangan "
            "itu, tetapi mengganti titik awal mutlak dengan peristiwa pantulan. Sebelum "
            "pantulan, alam semesta dianggap menyusut.",
        ),
        (
            "Apa yang dimaksud pantulan",
            "Pantulan adalah pembalikan arah skala alam semesta: dari menyusut menjadi "
            "mengembang. Peristiwa ini terjadi pada kepadatan yang sangat tinggi, tetapi "
            "tidak harus tak terhingga. Karena itu, model ini berusaha menghindari "
            "singularitas awal.",
        ),
        (
            "Mengapa gagasan ini menarik",
            "Jika pantulan mungkin, pertanyaan \"apa sebelum Big Bang\" berubah bentuk. "
            "Tidak ada awal dari ketiadaan yang perlu dijelaskan; yang ada adalah fase "
            "sebelumnya dari sejarah alam semesta.",
        ),
        (
            "Batas klaimnya",
            "Big Bounce masih merupakan keluarga model, bukan satu teori tunggal. Berbagai "
            "versi memakai mekanisme berbeda, dan belum ada bukti observasi yang "
            "memutuskannya. Materi ini karena itu melatih kita memisahkan gagasan, "
            "mekanisme, dan bukti.",
        ),
    ],
    [
        (
            "Membaca data CMB",
            "Radiasi latar mikrowave adalah sisa panas awal alam semesta. Polanya memberi "
            "petunjuk tentang kondisi awal, komposisi materi, dan riak kecil yang kemudian "
            "tumbuh menjadi galaksi. Model kosmologi harus bisa menjelaskan pola itu.",
        ),
        (
            "Peran energi gelap",
            "Pengamatan pada 1998 menunjukkan pengembangan alam semesta makin cepat. "
            "Energi gelap dipakai untuk menjelaskan percepatan ini. Akibatnya, skenario "
            "yang mengandalkan penyusutan ulang menjadi lebih sulit dipertahankan.",
        ),
        (
            "Apa yang dicari peneliti",
            "Peneliti mencari jejak fase sebelum pantulan, misalnya pola khusus pada CMB "
            "atau gelombang gravitasi primordial. Jejak semacam itu harus bisa dibedakan "
            "dari prediksi inflasi agar benar-benar menjadi uji.",
        ),
        (
            "Menilai bukti",
            "Saat ini data lebih cocok dengan inflasi. Itu bukan berarti Big Bounce gugur "
            "selamanya, tetapi klaimnya belum punya dukungan observasi yang cukup. Sikap "
            "yang tepat adalah menandai statusnya sebagai hipotesis yang sedang diuji.",
        ),
    ],
    [
        (
            "Skala Planck",
            "Pada skala Planck, panjang dan waktu menjadi sangat kecil sehingga efek "
            "kuantum tidak bisa diabaikan. Di wilayah ini, gambaran ruang-waktu yang mulus "
            "mulai gagal. Model klasik perlu diganti dengan pendekatan kuantum.",
        ),
        (
            "Gravitasi yang berubah tanda",
            "Dalam Loop Quantum Cosmology, efek kuantum dapat membuat gravitasi efektif "
            "menolak pada kepadatan ekstrem. Gaya tolak ini bekerja seperti rem yang "
            "menghentikan penyusutan sebelum kepadatan menjadi tak terhingga.",
        ),
        (
            "Mekanisme pantulan",
            "Ketika penyusutan berhenti, arah evolusi berbalik menjadi pengembangan. "
            "Pantulan karena itu bukan ledakan dari ketiadaan, melainkan perubahan rezim "
            "fisika pada kepadatan tinggi.",
        ),
        (
            "Apa yang belum diketahui",
            "Loop Quantum Cosmology adalah kerangka yang masih dikembangkan. Hubungannya "
            "dengan gravitasi kuantum penuh dan cara mengujinya secara observasi belum "
            "tuntas. Model ini memberi bahasa untuk pantulan, bukan bukti akhir.",
        ),
    ],
    [
        (
            "Ide model siklik",
            "Model siklik membayangkan alam semesta melewati siklus penyusutan dan "
            "pengembangan berulang. Dalam versi ekpirotik, tabrakan antar-brane menjadi "
            "pemicu fase pengembangan baru. Big Bang bukan peristiwa tunggal, melainkan "
            "salah satu titik dalam rangkaian.",
        ),
        (
            "Torsi Einstein-Cartan",
            "Dalam kerangka Einstein-Cartan, spin partikel memberi torsi pada ruang-waktu. "
            "Torsi ini dapat menghasilkan efek tolak yang mencegah kepadatan mencapai nilai "
            "tak terhingga. Dengan begitu, penyusutan berbalik sebelum singularitas.",
        ),
        (
            "Membandingkan mekanisme",
            "Loop Quantum Cosmology menekankan efek kuantum pada geometri. Model ekpirotik "
            "menekankan dinamika bran. Torsi Einstein-Cartan menekankan spin dan geometri. "
            "Ketiganya berbagi tujuan menghindari singularitas, tetapi berbeda pada tingkat "
            "fisika yang dipakai.",
        ),
        (
            "Konsekuensi",
            "Jika salah satu mekanisme benar, sejarah alam semesta lebih panjang dari yang "
            "biasa kita bayangkan. Namun, setiap mekanisme harus menghasilkan prediksi yang "
            "bisa diuji, bukan hanya cerita yang terdengar rapi.",
        ),
    ],
    [
        (
            "Masalah entropi",
            "Entropi cenderung bertambah. Pada model siklik, setiap siklus mewarisi "
            "ketidakteraturan dari siklus sebelumnya. Tanpa mekanisme yang mengosongkan "
            "entropi, siklus tidak bisa berulang secara identik.",
        ),
        (
            "Perbandingan dengan inflasi",
            "Inflasi menjelaskan beberapa ciri alam semesta dengan satu periode "
            "pengembangan cepat. Data CMB sejauh ini lebih cocok dengan skenario itu. "
            "Big Bounce perlu menunjukkan pola yang berbeda dan terukur agar bisa bersaing.",
        ),
        (
            "Uji yang mungkin",
            "Uji yang masuk akal melibatkan pola CMB berpresisi tinggi, gelombang gravitasi "
            "primordial, dan perbandingan prediksi dengan model inflasi. Uji harus "
            "dirancang agar kedua model memberi jawaban berbeda.",
        ),
        (
            "Status riset",
            "Big Bounce tetap penting sebagai alternatif konseptual. Nilainya bukan hanya "
            "pada jawaban yang diberikan, tetapi pada pertanyaan yang dipaksa diajukan: "
            "apakah singularitas benar-benar awal, atau hanya batas teori kita?",
        ),
    ],
]


def path(goal: str) -> list[dict]:
    return [dict(item) for item in TOPICS]


def lesson(topic: Topic) -> dict:
    index = topic.position % len(LESSON_SECTIONS)
    sections = [
        {"heading": heading, "body": body}
        for heading, body in LESSON_SECTIONS[index]
    ]
    return {
        "title": topic.title,
        "objective": (
            topic.objectives[0]
            if topic.objectives
            else f"Memahami inti topik {topic.title}."
        ),
        "sections": sections,
        "key_terms": [
            {"term": "Pantulan", "definition": "Pembalikan dari fase menyusut ke mengembang."},
            {"term": "Singularitas", "definition": "Keadaan dengan kepadatan dan kelengkungan tak terhingga."},
            {"term": "CMB", "definition": "Radiasi latar mikrowave yang menyimpan jejak awal alam semesta."},
        ],
        "example": (
            "Bayangkan pegas yang ditekan lalu dilepas. Selama ditekan, panjangnya "
            "menyusut; pada titik tertentu arah gerak berbalik dan pegas mengembang. "
            "Big Bounce memakai intuisi serupa untuk skala alam semesta, dengan fisika "
            "yang jauh lebih rumit."
        ),
        "recap": (
            f"{topic.title} menghubungkan gagasan pantulan dengan bukti dan batas model. "
            "Yang perlu diingat: mekanisme berbeda bisa berbagi tujuan yang sama, dan "
            "status ilmiah ditentukan oleh uji observasi, bukan oleh kerapian cerita."
        ),
    }


def _fresh(pool: list[dict], count: int, exclude: list[str]) -> list[dict]:
    lowered = {" ".join(item.lower().split()) for item in exclude}
    fresh = [
        item for item in pool if " ".join(item["text"].lower().split()) not in lowered
    ]
    if not fresh:
        fresh = list(pool)
    return [dict(item) for item in fresh[: max(1, count)]]


def quiz(kind: str, count: int, exclude: list[str]) -> list[dict]:
    pool = MC_POOL if kind == "mc" else ESSAY_POOL
    return _fresh(pool, count, exclude)


def essay_grades(items: list[dict]) -> dict:
    grades = []
    for item in items:
        answer = str(item.get("answer_text", "")).strip()
        if not answer:
            points, verdict = 0, "salah"
            feedback = "Belum dijawab. Coba tuliskan inti jawabanmu lebih dulu."
        elif len(answer) < 60:
            points, verdict = 60, "sebagian"
            feedback = (
                "Arah jawabanmu sudah benar, tetapi belum menyentuh semua poin kunci. "
                "Tambahkan penjelasan pada bagian yang masih kosong."
            )
        elif len(answer) < 200:
            points, verdict = 80, "benar"
            feedback = (
                "Jawaban sudah memuat sebagian besar poin kunci. Perjelas hubungan "
                "sebab-akibat antar bagian agar lebih meyakinkan."
            )
        else:
            points, verdict = 95, "benar"
            feedback = (
                "Jawaban lengkap dan runut. Pertahankan kebiasaan menjelaskan alasan "
                "di balik setiap klaim."
            )
        grades.append(
            {
                "number": item["number"],
                "points": points,
                "verdict": verdict,
                "feedback": feedback,
            }
        )
    return {"grades": grades}


def tutor_reply(messages: list[dict], context: str) -> Iterator[str]:
    last = ""
    for message in reversed(messages):
        if message.get("role") == "user":
            content = message.get("content")
            if isinstance(content, list):
                last = " ".join(
                    str(part.get("text", ""))
                    for part in content
                    if isinstance(part, dict) and part.get("type") == "text"
                )
            else:
                last = str(content)
            break
    topic_line = ""
    for line in context.splitlines():
        if line.startswith("Topik aktif:"):
            topic_line = line.replace("Topik aktif:", "").strip()
            break

    text = (
        f"Kita bedah pertanyaanmu pelan-pelan: \"{last.strip()[:160]}\".\n\n"
        f"Dalam kerangka {topic_line or 'topik ini'}, ada tiga hal yang perlu dipisahkan: "
        "gagasan utama, mekanisme yang diusulkan, dan bukti yang mendukungnya. Gagasan "
        "utama menjawab \"apa yang ingin dijelaskan\". Mekanisme menjawab \"bagaimana hal "
        "itu terjadi\". Bukti menjawab \"mengapa kita percaya\". Ketika ketiganya dicampur, "
        "diskusi mudah berubah menjadi klaim yang terdengar meyakinkan tanpa dukungan.\n\n"
        "Contohnya, model pantulan memberi cerita yang rapi tentang asal alam semesta. "
        "Namun cerita itu baru bernilai ilmiah jika menghasilkan prediksi yang bisa "
        "dibedakan dari inflasi, misalnya pola pada CMB atau gelombang gravitasi "
        "primordial. Tanpa uji seperti itu, model tetap berada pada status hipotesis.\n\n"
        "Sekarang cek pemahamanmu: menurutmu, bukti seperti apa yang paling kuat untuk "
        "membedakan model pantulan dari inflasi? Jelaskan alasanmu dalam satu atau dua "
        "kalimat. Kalau kamu ingin penjelasan langsung tanpa pertanyaan, katakan saja."
    )
    for index in range(0, len(text), 20):
        time.sleep(0.004)
        yield text[index : index + 20]
