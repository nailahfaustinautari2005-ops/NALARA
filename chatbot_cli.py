"""
chatbot_cli.py
==============

TAHAP 3 — Chatbot sederhana di terminal (nama aplikasi: NALARA).

File ini HANYA mengurus tampilan (print) dan masukan (input).
Semua logika ada di:
  - question_flow.py   : memilih pertanyaan & mengatur tahap
  - inference_engine.py: forward chaining
  - knowledge_base.py  : 31 rule

Jalankan dari folder project:

    python chatbot_cli.py

Semua pertanyaan dijawab dengan angka (1, 2, 3).

Perintah saat rekomendasi tampil:
  - Enter        : lanjut
  - 1, 2, 3 ...  : lihat mengapa saran bernomor itu muncul
  - proses       : lihat jejak forward chaining (untuk penjelasan teknis/dosen)
  - keluar       : mengakhiri sesi
  (Kode rule seperti R20 juga masih diterima.)
"""

import textwrap

from question_flow import COMPLAINTS, Session

WIDTH = 78
INTRO = (
    "Anda akan diberi beberapa pertanyaan singkat (biasanya 2–7). "
    "Jawab dengan mengetik angka pilihan, lalu tekan Enter. "
    "Ketik 'keluar' kapan saja untuk berhenti."
)
DISCLAIMER = (
    "Catatan: NALARA membantu Anda menelusuri kemungkinan penyebab masalah "
    "laptop melalui langkah-langkah pemeriksaan dari panduan resmi, tetapi "
    "hasilnya bukan kepastian kerusakan. Untuk pemeriksaan lebih lanjut, "
    "silakan bawa laptop ke service center resmi."
)
FINISH_MESSAGES = {
    "resolved": "Senang masalahnya teratasi. Sesi selesai.",
    "exhausted": ("Semua rekomendasi yang relevan di knowledge base sudah ditampilkan. "
                  "Jika masalah masih ada, hubungi service center resmi."),
    "quit": "Sesi diakhiri.",
}
STAGE_TITLES = {"dasar": "Langkah dasar", "lanjutan": "Langkah lanjutan", "akhir": "Langkah akhir"}


class QuitSession(Exception):
    """Dilempar ketika pengguna mengetik 'keluar'."""


def wrap(text, indent=""):
    return textwrap.fill(text, width=WIDTH, initial_indent=indent, subsequent_indent=indent)


def ask_choice(prompt, options, read, write):
    """Tampilkan pilihan bernomor dan kembalikan indeks (0-based) yang dipilih."""
    for number, option in enumerate(options, start=1):
        write(f"  {number}. {option}")
    while True:
        raw = read(f"{prompt} (1-{len(options)}): ").strip().lower()
        if raw in ("keluar", "exit", "q"):
            raise QuitSession
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        write(f"  Masukkan angka 1 sampai {len(options)}, atau ketik 'keluar'.")


def show_recommendations(session, items, read, write):
    stage = items[0]["stage"]
    write("")
    write("-" * WIDTH)
    write(f"REKOMENDASI — {STAGE_TITLES.get(stage, stage)}")
    write("-" * WIDTH)
    # Saran diberi nomor 1, 2, 3 ... agar mudah bagi pengguna awam.
    # Kode rule (R20, dst.) tetap ditampilkan kecil di akhir, untuk keperluan
    # penjelasan teknis/presentasi.
    for number, item in enumerate(items, start=1):
        label = f"{number}. "
        text = f"{item['output']} (kode: {item['rule_id']})"
        write(textwrap.fill(text, width=WIDTH,
                            initial_indent=label, subsequent_indent=" " * len(label)))
        write("")
    if len(items) == 1:
        hint = "Ketik 1 untuk melihat mengapa saran ini muncul"
    else:
        hint = f"Ketik nomor saran (1-{len(items)}) untuk melihat mengapa saran itu muncul"
    write(wrap(hint + ", atau tekan Enter untuk lanjut."))
    while True:
        raw = read("> ").strip()
        command = raw.lower()
        if command == "":
            return
        if command in ("keluar", "exit", "q"):
            raise QuitSession
        if command == "proses":
            show_trace(session, write)
            continue
        if command.isdigit() and 1 <= int(command) <= len(items):
            rule_id = items[int(command) - 1]["rule_id"]
        else:
            rule_id = raw.upper()  # kode rule juga diterima, mis. "R20"
        plain = session.explain_plain(rule_id)
        if plain:
            write("Saran ini muncul karena jawaban Anda:")
            for line in plain:
                write(textwrap.fill(line, width=WIDTH, initial_indent="  - ",
                                    subsequent_indent="    "))
            write("  (Ketik 'proses' untuk melihat proses penalaran lengkap.)")
        else:
            write(f"  Ketik angka 1 sampai {len(items)}, atau tekan Enter untuk lanjut.")


def show_trace(session, write):
    write("Jejak forward chaining:")
    for step in session.trace():
        conditions = " AND ".join(step["conditions"])
        write(f"  Siklus {step['cycle']:>2}: conflict set {step['conflict_set']}")
        write(f"            terpicu {step['rule_id']} ({step['type']}): "
              f"IF {conditions} THEN {step['then']}")


def run(read=input, write=print):
    """Jalankan satu sesi chatbot. read/write bisa diganti saat pengujian."""
    def safe_read(prompt):
        try:
            return read(prompt)
        except (EOFError, KeyboardInterrupt):  # Ctrl+C / Ctrl+Z = keluar
            raise QuitSession

    session = Session()
    read_input = safe_read
    write("=" * WIDTH)
    write("NALARA — Troubleshooting Laptop Berbasis Knowledge-Based System")
    write("dengan Metode Forward Chaining")
    write("=" * WIDTH)
    write(wrap(DISCLAIMER))
    write("")
    write(wrap(INTRO))
    write("")
    try:
        write("Apa keluhan utama laptop Anda?")
        choice = ask_choice("Pilih keluhan", [c["label"] for c in COMPLAINTS], read_input, write)
        session.choose_complaint(COMPLAINTS[choice]["fact"])

        while True:
            action = session.next_action()
            if action["type"] == "question":
                question = action["question"]
                write("")
                if question["note"]:
                    write(wrap(question["note"]))
                write(f"Pertanyaan {question['number']}:")
                write(wrap(question["text"]))
                index = ask_choice("Jawaban", question["options"], read_input, write)
                session.answer(question["id"], index)
            elif action["type"] == "recommendations":
                show_recommendations(session, action["items"], read_input, write)
            else:
                write("")
                write(wrap(FINISH_MESSAGES[action["reason"]]))
                return session
    except QuitSession:
        write("")
        write(FINISH_MESSAGES["quit"])
        return session


if __name__ == "__main__":
    run()
