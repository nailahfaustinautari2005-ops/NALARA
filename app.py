"""
app.py
======

TAHAP 4 — Aplikasi web NALARA (Streamlit).

File ini HANYA mengurus tampilan web. Semua logika tetap di file lama:
  - question_flow.py   : memilih pertanyaan & mengatur tahap (Session)
  - inference_engine.py: forward chaining
  - knowledge_base.py  : 31 rule
Ketiga file itu TIDAK diubah untuk tahap ini.

Jalankan dari folder project:

    python -m streamlit run app.py

Lalu buka alamat yang muncul (biasanya http://localhost:8501).
Untuk membuka dari HP/tablet, sambungkan ke Wi-Fi yang sama lalu buka
"Network URL" yang muncul di terminal.

Alur layar (sesuai mockup desain):
  1. Halaman awal     : pilih keluhan utama
  2. Pertanyaan       : satu pertanyaan per layar
  3. Rekomendasi      : saran bernomor + "Mengapa saran ini?" + pertanyaan tahap
  4. Tahap akhir      : saran pemeriksaan perangkat keras / service center
  5. Masalah teratasi : ringkasan langkah yang dicoba
"""

import base64
import html
from datetime import datetime
from pathlib import Path

import streamlit as st

from chatbot_cli import DISCLAIMER, FINISH_MESSAGES
from question_flow import COMPLAINTS, QUESTIONS, Session

BASE_DIR = Path(__file__).parent
ASSETS = BASE_DIR / "assets"

# ============================================================
# 1. TEKS & IKON TAMPILAN (bukan logika — hanya kata-kata di layar)
# ============================================================

# Ikon Material untuk setiap keluhan (kunci = fakta keluhan di question_flow.py).
COMPLAINT_ICONS = {
    "no_power": ":material/power_settings_new:",
    "blank_screen": ":material/desktop_access_disabled:",
    "charging_slow": ":material/battery_charging_20:",
    "battery_not_charging": ":material/battery_alert:",
    "laptop_hot": ":material/device_thermostat:",
    "fan_loud": ":material/mode_fan:",
    "laptop_slow": ":material/hourglass_bottom:",
}

# Label pendek untuk ringkasan "jawaban sebelumnya" (kunci = id pertanyaan).
SHORT_LABELS = {
    "q_laptop_hot": "Badan laptop terasa sangat panas",
    "q_fan_loud": "Kipas kencang / berputar terus",
    "q_charger": "Charger terpasang",
    "q_charger_original": "Charger & kabel bawaan/rekomendasi produsen",
    "q_external_monitor": "Tersambung ke monitor eksternal/proyektor",
    "q_cursor": "Kursor mouse terlihat di layar gelap",
    "q_after_update": "Mulai terjadi setelah update Windows/driver",
    "q_heavy_app": "Menjalankan aplikasi berat",
    "q_soft_surface": "Dipakai di kasur, sofa, atau pangkuan",
    "q_vents_blocked": "Ada benda yang menutupi ventilasi",
    "q_fan_abnormal": "Kipas berbunyi kasar / tidak berputar",
    "q_many_apps": "Banyak aplikasi/tab terbuka",
    "q_disk_low": "Drive C hampir penuh",
    "q_charge_limit": "Baterai selalu berhenti di angka yang sama",
    "q_persists_basic": "Masih bermasalah setelah langkah dasar",
    "q_persists_advanced": "Masih bermasalah setelah langkah lanjutan",
}

# Pada pertanyaan tahap, jawaban "Ya"/"Tidak" ditampilkan lebih jelas.
# (Nilai yang dikirim ke Session tetap nomor pilihan yang sama.)
STAGE_OPTION_LABELS = {"Ya": "Ya, masih", "Tidak": "Tidak, sudah teratasi"}

STAGE_BADGES = {
    "dasar": ("TAHAP DASAR", "nl-b-dasar"),
    "lanjutan": ("TAHAP LANJUTAN", "nl-b-lanjut"),
    "akhir": ("TAHAP AKHIR", "nl-b-akhir"),
}
STAGE_TITLES = {"dasar": "Tahap dasar", "lanjutan": "Tahap lanjutan", "akhir": "Tahap akhir"}

# Rekomendasi yang berarti "perlu bantuan ahli" -> Lara berwajah peduli.
# (Hanya memengaruhi gambar & judul layar, tidak memengaruhi penalaran.)
ESCALATION_FACTS = {"rec_hardware_diagnostic_or_service", "rec_consult_support"}

TYPICAL_MAX_QUESTIONS = 7          # dari chatbot: "biasanya 2–7 pertanyaan"
DISCLAIMER_TEXT = DISCLAIMER.removeprefix("Catatan: ")   # satu sumber kalimat dengan terminal

# ============================================================
# 2. WARNA (palet Biru Langit) & GAYA TAMPILAN
# ============================================================
CSS = """
<style>
:root{
  --nl-primary:#2F6FC9; --nl-primary-soft:#E1ECFB; --nl-primary-ink:#265EB0;
  --nl-accent:#FFB86B; --nl-accent-soft:#FFF1E2; --nl-accent-ink:#8A5A00;
  --nl-card:#FFFFFF; --nl-line:#DCE6F4; --nl-ink:#1B2433; --nl-ink-2:#4A5568; --nl-ink-3:#667085;
  --nl-ok:#147A3A; --nl-ok-soft:#E6F6EC; --nl-warn:#B45309; --nl-warn-soft:#FEF3E2;
  --nl-end:#C0392B; --nl-end-soft:#FDECE8;
}
.block-container{padding-top:2.2rem; padding-bottom:3rem; max-width:760px}

/* merek di halaman awal */
.nl-brand{display:flex; align-items:center; gap:14px; margin-bottom:.4rem}
.nl-brand img{width:112px; height:112px; flex:none}
.nl-title{font-size:2rem; font-weight:800; letter-spacing:.04em; line-height:1; color:var(--nl-ink)}
.nl-sub{margin:.3rem 0 0 !important; font-size:.98rem !important; color:var(--nl-ink-2)}
.nl-hello{margin:.35rem 0 0 !important; font-size:.92rem !important; color:var(--nl-ink-3)}
.nl-hello b{color:var(--nl-primary-ink)}
.nl-chips{display:flex; flex-wrap:wrap; gap:6px; margin:.2rem 0 .3rem}
.nl-chip{display:inline-flex; align-items:center; font-size:.78rem; font-weight:600; border-radius:999px;
  padding:3px 10px; background:var(--nl-primary-soft); color:var(--nl-primary-ink)}
.nl-chip.acc{background:var(--nl-accent-soft); color:var(--nl-accent-ink)}
.nl-lead{font-size:1.25rem !important; font-weight:700; margin:.5rem 0 .1rem !important; color:var(--nl-ink)}
.nl-foot{font-size:.82rem !important; color:var(--nl-ink-3); text-align:center; margin-top:.3rem !important}

/* tombol keluhan: besar, rata kiri, tinggi sama */
[class*="st-key-complaint_"] button{min-height:60px; justify-content:flex-start; text-align:left;
  background:var(--nl-card); font-weight:600}
[class*="st-key-complaint_"] button > div, [class*="st-key-complaint_"] button > div > span{justify-content:flex-start; width:100%; text-align:left}
[class*="st-key-complaint_"] button p{font-weight:600; font-size:.98rem; text-align:left}
[class*="st-key-complaint_"] span[data-testid="stTooltipHoverTarget"]{width:100%}
[class*="st-key-complaint_"] button span[data-testid="stIconMaterial"]{color:var(--nl-primary)}

/* Lara + gelembung ucapan */
.nl-lara-row{display:flex; align-items:center; gap:10px; margin:.2rem 0 .4rem}
.nl-lara-row img{width:64px; height:64px; flex:none}
.nl-bubble{position:relative; background:var(--nl-card); border:1px solid var(--nl-line); border-radius:12px;
  padding:8px 12px; font-size:.9rem; color:var(--nl-ink-2)}
.nl-bubble::before{content:""; position:absolute; left:-7px; top:50%; margin-top:-6px; width:12px; height:12px;
  background:var(--nl-card); border-left:1px solid var(--nl-line); border-bottom:1px solid var(--nl-line); transform:rotate(45deg)}
.nl-head h2{margin:.25rem 0 0 !important; padding:0 !important; font-size:1.25rem !important; color:var(--nl-ink)}

/* label tahap (warna tetap: hijau dasar, oranye lanjutan, merah akhir) */
.nl-badge{display:inline-block; font-size:.72rem; font-weight:700; border-radius:999px; padding:2px 10px; letter-spacing:.03em}
.nl-b-dasar{background:var(--nl-ok-soft); color:var(--nl-ok)}
.nl-b-lanjut{background:var(--nl-warn-soft); color:var(--nl-warn)}
.nl-b-akhir{background:var(--nl-end-soft); color:var(--nl-end)}

/* keluhan yang sedang dibahas + progress */
.nl-topic{display:inline-flex; font-size:.8rem; font-weight:600; border-radius:999px; padding:3px 12px;
  background:var(--nl-primary-soft); color:var(--nl-primary-ink); margin-bottom:.4rem}
.nl-progress{display:flex; justify-content:space-between; font-size:.85rem; color:var(--nl-ink-2); margin-bottom:-.6rem}

/* tombol jawaban sedikit lebih tinggi agar mudah diklik/diketuk */
[class*="st-key-ans_"] button{min-height:48px}
[class*="st-key-ans_"] button p{font-weight:600; font-size:1rem}

/* kartu pertanyaan, kartu saran, kotak pertanyaan tahap */
.st-key-qcard, [class*="st-key-rec_"]{background:var(--nl-card)}
[class*="st-key-recend_"]{background:#FFFBFA; border-color:#F5C2B8 !important}
.st-key-persist{background:var(--nl-card); border:1.5px dashed var(--nl-primary) !important}
.nl-q{font-size:1.3rem !important; font-weight:700; line-height:1.4; margin:.2rem 0 .5rem !important; color:var(--nl-ink)}
.nl-rec{display:grid; grid-template-columns:30px 1fr; gap:4px 10px; align-items:start}
.nl-num{width:28px; height:28px; border-radius:50%; background:var(--nl-primary-soft); color:var(--nl-primary-ink);
  font-weight:800; display:grid; place-items:center; font-size:.9rem}
[class*="st-key-recend_"] .nl-num{background:var(--nl-end-soft); color:var(--nl-end)}
.nl-rec p{margin:0 !important; font-size:.98rem !important; line-height:1.55; color:var(--nl-ink)}
.nl-code{grid-column:2; text-align:right; font-family:"Source Code Pro",monospace; font-size:.72rem; color:var(--nl-ink-3)}
.nl-why{background:var(--nl-accent-soft); border-radius:8px; padding:9px 12px; font-size:.88rem; color:var(--nl-ink)}
.nl-why ul{margin:.3rem 0 0; padding-left:1.1rem}
.nl-persist-q{font-weight:700; font-size:1.05rem !important; margin:0 0 .4rem !important; color:var(--nl-ink)}

/* riwayat jawaban */
.nl-history{font-size:.88rem; color:var(--nl-ink-2); display:flex; flex-direction:column; gap:3px; margin-top:.2rem}
.nl-history b{color:var(--nl-ink)}
.nl-history .ok{color:var(--nl-ok); font-weight:700; margin-right:6px}

/* layar selesai */
.nl-done{text-align:center; display:flex; flex-direction:column; align-items:center; gap:8px}
.nl-done img{width:150px; height:150px}
.nl-done h2{margin:0 !important; padding:0 !important; font-size:1.45rem !important}
.nl-done p{margin:0 !important; color:var(--nl-ink-2); max-width:40ch}
.nl-summary{margin-top:.6rem; background:var(--nl-card); border:1px solid var(--nl-line); border-radius:12px; padding:12px 14px;
  font-size:.9rem; color:var(--nl-ink-2)}
.nl-summary ol{margin:.3rem 0 0; padding-left:1.2rem}
.nl-summary li{margin-bottom:4px}
.nl-trace{font-family:"Source Code Pro",monospace; font-size:.75rem; color:var(--nl-ink-2)}
.nl-trace div{margin-bottom:6px; overflow-wrap:anywhere}
.nl-trace b{color:var(--nl-primary-ink); font-weight:600}
</style>
"""


# ============================================================
# 3. FUNGSI BANTU TAMPILAN
# ============================================================
@st.cache_data
def lara_src(name):
    """Gambar Lara (SVG) sebagai data URI, supaya bisa diletakkan di dalam HTML."""
    svg = (ASSETS / f"lara_{name}.svg").read_bytes()
    return "data:image/svg+xml;base64," + base64.b64encode(svg).decode()


def lara_img(name, alt):
    return f'<img src="{lara_src(name)}" alt="{html.escape(alt)}">'


def esc(text):
    return html.escape(str(text))


def html_block(markup):
    """Tulis potongan HTML (tanpa baris kosong agar tidak diubah oleh Markdown)."""
    st.markdown(" ".join(markup.split("\n")), unsafe_allow_html=True)


def option_labels(question):
    if question["is_stage"]:
        return [STAGE_OPTION_LABELS.get(label, label) for label in question["options"]]
    return list(question["options"])


def complaint_label(fact):
    return next(c["label"] for c in COMPLAINTS if c["fact"] == fact)


def build_summary(session):
    """Ringkasan teks yang bisa diunduh dan ditunjukkan ke teknisi."""
    lines = [
        "NALARA — Ringkasan troubleshooting laptop",
        f"Tanggal: {datetime.now():%d-%m-%Y %H:%M}",
        "",
        f"Keluhan utama: {complaint_label(session.complaint)}",
        "",
        "Jawaban Anda:",
    ]
    for question_id in session.asked:
        lines.append(f"- {QUESTIONS[question_id]['text']} -> {session.answers[question_id]}")
    lines += ["", "Saran yang sudah ditampilkan:"]
    for number, item in enumerate(session.recommendations_shown(), start=1):
        lines.append(f"{number}. [{STAGE_TITLES[item['stage']]}] {item['output']} (kode: {item['rule_id']})")
    lines += ["", DISCLAIMER]
    return "\n".join(lines)


# ============================================================
# 4. STATE & AKSI (dipanggil saat tombol diklik)
# ------------------------------------------------------------
# st.session_state menyimpan:
#   session : objek Session dari question_flow.py
#   action  : langkah yang sedang menunggu (pertanyaan / selesai)
#   recs    : rekomendasi yang sedang ditampilkan di layar
# ============================================================
def advance():
    """Minta langkah berikutnya ke Session (logika sepenuhnya di question_flow.py)."""
    session = st.session_state.session
    action = session.next_action()
    if action["type"] == "recommendations":
        st.session_state.recs = action["items"]
        action = session.next_action()   # pertanyaan tahap / selesai, ditampilkan di bawah saran
    st.session_state.action = action


def start(fact):
    session = Session()
    session.choose_complaint(fact)
    st.session_state.session = session
    st.session_state.recs = []
    advance()


def answer(question_id, option_index):
    session = st.session_state.session
    action = st.session_state.get("action", {})
    pending = action.get("question", {}).get("id") if action.get("type") == "question" else None
    if question_id != pending or question_id in session.answers:
        return   # klik ganda / tombol lama: abaikan
    session.answer(question_id, option_index)
    st.session_state.recs = []
    advance()


def restart():
    for key in ("session", "action", "recs"):
        st.session_state.pop(key, None)


def restart_link(key):
    st.button("Mulai ulang", icon=":material/restart_alt:", type="tertiary", key=key, on_click=restart)


# ============================================================
# 5. LAYAR-LAYAR
# ============================================================
def screen_home():
    html_block(f"""
    <div class="nl-brand">{lara_img("menyapa", "Lara, maskot NALARA, melambaikan tangan")}
      <div><div class="nl-title">NALARA</div>
        <p class="nl-sub">Nalar pakar untuk laptop Anda</p>
        <p class="nl-hello">Halo, aku <b>Lara</b>! Ceritakan masalah laptopmu.</p></div></div>
    <div class="nl-chips"><span class="nl-chip">Knowledge-Based System</span>
      <span class="nl-chip acc">Forward Chaining</span><span class="nl-chip">31 rule</span></div>
    """)
    st.info(DISCLAIMER_TEXT, icon=":material/info:")
    html_block('<p class="nl-lead">Apa keluhan utama laptop Anda?</p>')

    main, last = COMPLAINTS[:-1], COMPLAINTS[-1]
    for i in range(0, len(main), 2):
        columns = st.columns(2)
        for column, complaint in zip(columns, main[i:i + 2]):
            with column:
                complaint_button(complaint)
    complaint_button(last)
    html_block(f'<p class="nl-foot">Biasanya 2–{TYPICAL_MAX_QUESTIONS} pertanyaan singkat · jawab dengan satu klik</p>')


def complaint_button(complaint):
    st.button(complaint["label"], icon=COMPLAINT_ICONS[complaint["fact"]], help=complaint["detail"],
              key=f"complaint_{complaint['fact']}", width="stretch",
              on_click=start, args=(complaint["fact"],))


def topic_chip(session):
    html_block(f'<span class="nl-topic">{esc(complaint_label(session.complaint))}</span>')


def history_block(session):
    if not session.asked:
        return
    rows = "".join(
        f'<div><span class="ok">✓</span>{esc(SHORT_LABELS[qid])}: <b>{esc(session.answers[qid])}</b></div>'
        for qid in session.asked)
    html_block(f'<div class="nl-history" aria-label="Jawaban sebelumnya">{rows}</div>')


def screen_question(session, question):
    topic_chip(session)
    number = question["number"]
    html_block(f'<div class="nl-progress"><span>Pertanyaan {number}</span>'
               f'<span>biasanya 2–{TYPICAL_MAX_QUESTIONS} pertanyaan</span></div>')
    st.progress(min(number / TYPICAL_MAX_QUESTIONS, 1.0))

    if question["is_stage"]:
        bubble = "Bagaimana hasilnya setelah dicoba?"
    elif number == 1:
        bubble = "Aku mulai dengan satu pertanyaan, ya."
    else:
        bubble = "Hmm, aku perlu tahu satu hal lagi…"
    html_block(f'<div class="nl-lara-row">{lara_img("berpikir", "Lara sedang berpikir")}'
               f'<div class="nl-bubble">{esc(bubble)}</div></div>')

    if question["note"]:
        st.info(question["note"], icon=":material/lightbulb:")

    with st.container(border=True, key="qcard"):
        html_block(f'<p class="nl-q">{esc(question["text"])}</p>')
        labels = option_labels(question)
        columns = st.columns(len(labels))
        for index, (column, label) in enumerate(zip(columns, labels)):
            with column:
                st.button(label, key=f"ans_{question['id']}_{index}", width="stretch",
                          on_click=answer, args=(question["id"], index))

    history_block(session)
    restart_link("restart_q")


def recommendation_card(session, number, item, is_end):
    key_prefix = "recend" if is_end else "rec"
    with st.container(border=True, key=f"{key_prefix}_{item['rule_id']}"):
        html_block(f'<div class="nl-rec"><span class="nl-num">{number}</span>'
                   f'<p>{esc(item["output"])}</p>'
                   f'<span class="nl-code">kode: {esc(item["rule_id"])}</span></div>')
        with st.expander("Mengapa saran ini?", icon=":material/help:"):
            lines = session.explain_plain(item["rule_id"]) or []
            bullets = "".join(f"<li>{esc(line)}</li>" for line in lines)
            html_block(f'<div class="nl-why"><b>Saran ini muncul karena jawaban Anda:</b><ul>{bullets}</ul></div>')


def trace_expander(session):
    with st.expander("Lihat proses penalaran (forward chaining)", icon=":material/account_tree:"):
        st.caption("Untuk penjelasan teknis: setiap siklus memilih satu rule dari conflict set, "
                   "lalu menambahkan fakta barunya ke working memory.")
        rows = "".join(
            f'<div>Siklus {step["cycle"]} · conflict set [{esc(", ".join(step["conflict_set"]))}] → '
            f'<b>{esc(step["rule_id"])}</b>: {esc(" ∧ ".join(step["conditions"]))} ⇒ {esc(step["then"])}</div>'
            for step in session.trace())
        html_block(f'<div class="nl-trace">{rows}</div>')


def screen_recommendations(session, items, action):
    stage = items[0]["stage"]
    escalate = stage == "akhir" or any(item["fact"] in ESCALATION_FACTS for item in items)
    if escalate:
        picture, title = lara_img("peduli", "Lara menyarankan pemeriksaan ahli"), "Sepertinya perlu dicek ahlinya"
    else:
        picture = lara_img("ide", "Lara menemukan saran")
        title = ("Ini langkah lanjutan yang bisa dicoba" if stage == "lanjutan"
                 else "Aku menemukan satu saran!" if len(items) == 1
                 else "Aku menemukan beberapa saran!")
    badge_text, badge_class = STAGE_BADGES[stage]
    topic_chip(session)
    html_block(f'<div class="nl-lara-row nl-head">{picture}<div>'
               f'<span class="nl-badge {badge_class}">{badge_text}</span>'
               f'<h2>{esc(title)}</h2></div></div>')

    for number, item in enumerate(items, start=1):
        is_end = item["fact"] in ESCALATION_FACTS or item["stage"] == "akhir"
        recommendation_card(session, number, item, is_end)

    if action["type"] == "question":
        question = action["question"]
        with st.container(border=True, key="persist"):
            html_block(f'<p class="nl-persist-q">{esc(question["text"])}</p>')
            labels = option_labels(question)
            columns = st.columns(len(labels))
            for index, (column, label) in enumerate(zip(columns, labels)):
                with column:
                    st.button(label, key=f"ans_{question['id']}_{index}", width="stretch",
                              on_click=answer, args=(question["id"], index))
    else:
        st.info(FINISH_MESSAGES["exhausted"], icon=":material/verified_user:")
        finish_actions(session)

    trace_expander(session)
    if action["type"] == "question":
        restart_link("restart_r")


def finish_actions(session):
    st.download_button("Unduh ringkasan untuk teknisi", data=build_summary(session),
                       file_name="ringkasan_NALARA.txt", mime="text/plain",
                       icon=":material/download:", width="stretch")
    st.button("Mulai keluhan baru", icon=":material/restart_alt:", type="primary",
              width="stretch", key="restart_done", on_click=restart)


def screen_resolved(session):
    shown = session.recommendations_shown()
    html_block(f'<div class="nl-done">{lara_img("hore", "Lara bersorak karena masalah teratasi")}'
               f'<h2>Hore, masalahnya teratasi!</h2>'
               f'<p>Senang bisa membantu. Simpan langkah yang berhasil supaya bisa dicoba lagi '
               f'kalau masalahnya muncul kembali.</p></div>')
    if shown:
        steps = "".join(f"<li>{esc(item['output'])}</li>" for item in shown)
        html_block(f'<div class="nl-summary"><b>Langkah yang sudah dicoba:</b><ol>{steps}</ol></div>')
    st.write("")
    finish_actions(session)
    trace_expander(session)


def screen_finished_plain(session):
    """Selesai tanpa saran baru di layar (jarang terjadi)."""
    html_block(f'<div class="nl-lara-row nl-head">{lara_img("peduli", "Lara menyarankan pemeriksaan ahli")}'
               f'<div><h2>Sepertinya perlu dicek ahlinya</h2></div></div>')
    st.info(FINISH_MESSAGES["exhausted"], icon=":material/verified_user:")
    finish_actions(session)
    trace_expander(session)


# ============================================================
# 6. HALAMAN UTAMA
# ============================================================
def main():
    st.set_page_config(page_title="NALARA — Troubleshooting Laptop",
                       page_icon=str(ASSETS / "lara_menyapa.png"), layout="centered")
    st.markdown(CSS, unsafe_allow_html=True)

    if "session" not in st.session_state:
        screen_home()
        return

    session = st.session_state.session
    action = st.session_state.action
    recs = st.session_state.recs

    if recs:
        screen_recommendations(session, recs, action)
    elif action["type"] == "question":
        screen_question(session, action["question"])
    elif action["reason"] == "resolved":
        screen_resolved(session)
    else:
        screen_finished_plain(session)


if __name__ == "__main__":
    main()
