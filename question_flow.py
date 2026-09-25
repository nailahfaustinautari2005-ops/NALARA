"""
question_flow.py
================

TAHAP 3 — Logika percakapan (tanpa tampilan).

File ini menghubungkan PENGGUNA dengan INFERENCE ENGINE:

    jawaban pengguna  ->  fakta awal  ->  forward_chain()  ->  rekomendasi

Isi file:
  1. COMPLAINTS       : 7 pilihan keluhan utama (masing-masing = satu fakta gejala)
  2. QUESTIONS        : kalimat pertanyaan untuk setiap fakta awal (dari tabel
                        mapping di dokumen audit, bagian 5)
  3. RELATED_SYMPTOMS : pertanyaan penghubung antar-gejala (juga dari audit)
  4. Session          : mengatur jalannya satu percakapan:
                        - memilih pertanyaan berikutnya SECARA OTOMATIS dari
                          knowledge base (bukan daftar pertanyaan per keluhan),
                        - memanggil forward_chain() setiap ada jawaban baru,
                        - menampilkan rekomendasi bertahap (dasar -> lanjutan -> akhir),
                        - menjelaskan "mengapa" sebuah rekomendasi muncul.

File ini TIDAK memakai input() atau print(). Tampilan diurus oleh
chatbot_cli.py (terminal) sekarang, dan oleh Streamlit pada tahap berikutnya.
knowledge_base.py dan inference_engine.py tidak diubah.
"""

from knowledge_base import RULES, INITIAL_FACTS
from inference_engine import forward_chain, explain as explain_fact


# ============================================================
# 1. KELUHAN UTAMA
# ------------------------------------------------------------
# Setiap keluhan menambahkan satu fakta gejala ke working memory.
# ============================================================
COMPLAINTS = [
    {"fact": "no_power",
     "label": "Laptop tidak menyala sama sekali",
     "detail": "Tidak ada lampu, suara kipas, atau gambar saat tombol power ditekan."},
    {"fact": "blank_screen",
     "label": "Layar hitam padahal laptop menyala",
     "detail": "Ada lampu atau suara kipas, tetapi layar hitam/kosong."},
    {"fact": "charging_slow",
     "label": "Pengisian lambat / baterai turun saat dicas",
     "detail": "Windows menampilkan 'charging slowly' atau persentase baterai turun walau charger terpasang."},
    {"fact": "battery_not_charging",
     "label": "Baterai tidak bertambah saat dicas",
     "detail": "Charger terpasang, tetapi persentase tidak bertambah atau selalu berhenti di angka tertentu."},
    {"fact": "laptop_hot",
     "label": "Laptop terasa sangat panas",
     "detail": "Badan laptop terasa jauh lebih panas dari biasanya."},
    {"fact": "fan_loud",
     "label": "Kipas kencang / berisik terus",
     "detail": "Kipas terdengar kencang atau berputar terus-menerus."},
    {"fact": "laptop_slow",
     "label": "Laptop lambat",
     "detail": "Laptop lambat atau sering tersendat."},
]


# ============================================================
# 2. PERTANYAAN
# ------------------------------------------------------------
# Setiap pertanyaan punya beberapa pilihan jawaban. Setiap pilihan
# menambahkan satu fakta, atau tidak menambahkan apa-apa (None).
# Kalimat pertanyaan diambil dari tabel mapping dokumen audit (bagian 5).
# ============================================================
YES, NO, DONT_KNOW, NOT_SURE = "Ya", "Tidak", "Tidak tahu", "Tidak yakin"

QUESTIONS = {
    # --- gejala (dipakai sebagai pertanyaan penghubung) ---
    "q_laptop_hot": {
        "text": "Apakah badan laptop terasa jauh lebih panas dari biasanya?",
        "options": [(YES, "laptop_hot"), (NO, None), (DONT_KNOW, None)],
    },
    "q_fan_loud": {
        "text": "Apakah kipas terdengar kencang atau berputar terus-menerus?",
        "options": [(YES, "fan_loud"), (NO, None)],
    },
    # --- kondisi ---
    "q_charger": {
        "text": "Apakah charger saat ini terpasang ke laptop dan ke stopkontak?",
        "options": [(YES, "charger_connected"), (NO, "charger_not_connected")],
    },
    "q_charger_original": {
        "text": ("Apakah charger DAN kabel yang Anda pakai adalah bawaan laptop "
                 "atau yang direkomendasikan produsennya?"),
        # Audit: "Tidak yakin" juga menambah fakta, karena rekomendasinya tidak berisiko.
        "options": [(YES, None), (NO, "charger_or_cable_not_original"),
                    (NOT_SURE, "charger_or_cable_not_original")],
    },
    "q_external_monitor": {
        "text": "Apakah laptop sedang tersambung ke monitor eksternal atau proyektor?",
        "options": [(YES, "external_monitor_connected"), (NO, None)],
    },
    "q_cursor": {
        "text": "Di layar yang gelap, apakah terlihat panah kursor mouse yang bisa digerakkan?",
        "options": [(YES, "cursor_visible"), (NO, None), (DONT_KNOW, None)],
    },
    "q_after_update": {
        "text": "Apakah layar gelap mulai terjadi setelah Windows atau driver di-update?",
        "options": [(YES, "problem_started_after_update"), (NO, None), (DONT_KNOW, None)],
    },
    "q_heavy_app": {
        "text": "Apakah Anda sedang menjalankan aplikasi berat seperti game, edit video, atau render?",
        "options": [(YES, None), (NO, "no_heavy_app_running")],
    },
    "q_soft_surface": {
        "text": "Apakah laptop sedang dipakai di atas kasur, bantal, sofa, atau pangkuan?",
        "options": [(YES, "soft_surface"), (NO, None)],
    },
    "q_vents_blocked": {
        "text": ("Apakah ada benda yang menutupi lubang ventilasi laptop "
                 "(biasanya di sisi samping, belakang/engsel, atau bawah)?"),
        "options": [(YES, "vents_blocked"), (NO, None), (DONT_KNOW, None)],
    },
    "q_fan_abnormal": {
        "text": ("Apakah kipas berbunyi kasar (menggeram/berderak), atau tidak berputar "
                 "sama sekali padahal laptop panas?"),
        "options": [(YES, "fan_abnormal_noise"), (NO, None)],
    },
    "q_many_apps": {
        "text": "Apakah saat ini banyak aplikasi atau tab browser yang terbuka?",
        "options": [(YES, "many_apps_running"), (NO, None)],
    },
    "q_disk_low": {
        "text": "Buka Settings › System › Storage. Apakah drive C hampir penuh?",
        "options": [(YES, "disk_space_low"), (NO, None), (DONT_KNOW, None)],
    },
    "q_charge_limit": {
        "text": ("Apakah baterai selalu berhenti mengisi di angka yang sama, "
                 "misalnya sekitar 55–60% atau 80%?"),
        "options": [(YES, "charge_stops_at_limit"), (NO, None), (DONT_KNOW, None)],
    },
    # --- tahap ---
    "q_persists_basic": {
        "text": "Setelah mencoba langkah-langkah tadi, apakah masalahnya masih terjadi?",
        "options": [(YES, "persists_after_basic"), (NO, None)],
        "stage": True,
    },
    "q_persists_advanced": {
        "text": "Setelah mencoba langkah lanjutan tadi, apakah masalahnya masih terjadi?",
        "options": [(YES, "persists_after_advanced"), (NO, None)],
        "stage": True,
    },
}

# Fakta -> pertanyaan yang dapat menghasilkannya (dibentuk otomatis dari QUESTIONS).
QUESTION_FOR_FACT = {
    fact: question_id
    for question_id, question in QUESTIONS.items()
    for _, fact in question["options"]
    if fact is not None
}

STAGE_FACTS = ["persists_after_basic", "persists_after_advanced"]

# Pertanyaan penghubung antar-gejala (dokumen audit, bagian 5):
#   laptop_hot  : "keluhan utama, ATAU pertanyaan penghubung di alur lambat/kipas"
#   fan_loud    : "keluhan utama, atau pertanyaan di alur panas"
#   fan_abnormal_noise : "ditanyakan di alur panas/kipas"
# Hanya berlaku untuk keluhan utama (tidak berantai).
RELATED_SYMPTOMS = {
    "laptop_slow": ["laptop_hot"],
    "fan_loud": ["laptop_hot", "fan_abnormal_noise"],
    "laptop_hot": ["fan_loud", "fan_abnormal_noise"],
}

RULE_ORDER = {rule["id"]: index for index, rule in enumerate(RULES)}


# ============================================================
# 3. SESSION — satu percakapan
# ============================================================
class Session:
    """
    Cara pakai (oleh terminal atau Streamlit):

        session = Session()
        session.choose_complaint("laptop_slow")
        while True:
            action = session.next_action()
            if action["type"] == "question":
                ...tampilkan action["question"], lalu:
                session.answer(action["question"]["id"], nomor_pilihan)
            elif action["type"] == "recommendations":
                ...tampilkan action["items"]
            else:  # "finished"
                break
    """

    def __init__(self):
        self.complaint = None
        self.user_facts = set()          # fakta dari jawaban pengguna
        self.asked = []                  # id pertanyaan yang sudah dijawab (berurutan)
        self.answers = {}                # id pertanyaan -> label jawaban
        self.shown_rule_ids = []         # rekomendasi yang sudah ditampilkan
        self.finished_reason = None
        self.result = forward_chain(set())

    # ---------- langkah 1: keluhan ----------
    def choose_complaint(self, fact):
        if self.complaint is not None:
            raise ValueError("Keluhan utama sudah dipilih untuk sesi ini.")
        if fact not in {c["fact"] for c in COMPLAINTS}:
            raise ValueError(f"Keluhan tidak dikenal: {fact!r}")
        self.complaint = fact
        self._add_fact(fact)

    # ---------- langkah 2: jawaban ----------
    def answer(self, question_id, option_index):
        if question_id not in QUESTIONS:
            raise ValueError(f"Pertanyaan tidak dikenal: {question_id!r}")
        if question_id in self.answers:
            raise ValueError(f"Pertanyaan {question_id} sudah dijawab.")
        options = QUESTIONS[question_id]["options"]
        if not 0 <= option_index < len(options):
            raise ValueError(f"Pilihan jawaban tidak valid: {option_index}")
        label, fact = options[option_index]
        self.asked.append(question_id)
        self.answers[question_id] = label
        if fact is not None:
            self._add_fact(fact)
        elif QUESTIONS[question_id].get("stage"):
            # Menjawab "Tidak" pada pertanyaan tahap = masalah sudah teratasi.
            self.finished_reason = "resolved"

    def _add_fact(self, fact):
        self.user_facts.add(fact)
        self.result = forward_chain(self.user_facts)  # jalankan ulang inferensi

    # ---------- langkah 3: apa berikutnya? ----------
    def next_action(self):
        """
        Urutan keputusan:
          1. sesi sudah selesai?             -> finished
          2. ada pertanyaan kondisi?         -> question
          3. ada rekomendasi baru?           -> recommendations
          4. ada tahap berikutnya?           -> question (tahap)
          5. tidak ada lagi                  -> finished
        """
        if self.complaint is None:
            raise ValueError("Pilih keluhan utama terlebih dahulu.")
        if self.finished_reason:
            return {"type": "finished", "reason": self.finished_reason}

        question_id = self._next_condition_question()
        if question_id:
            return {"type": "question", "question": self._question_payload(question_id)}

        new_items = self._unshown_recommendations()
        if new_items:
            self.shown_rule_ids.extend(item["rule_id"] for item in new_items)
            return {"type": "recommendations", "items": new_items}

        question_id = self._next_stage_question()
        if question_id:
            return {"type": "question", "question": self._question_payload(question_id)}

        self.finished_reason = "exhausted"
        return {"type": "finished", "reason": self.finished_reason}

    # ---------- pemilihan pertanyaan kondisi ----------
    def _is_askable(self, fact):
        """Fakta awal (bukan tahap) yang punya pertanyaan dan belum ditanyakan."""
        question_id = QUESTION_FOR_FACT.get(fact)
        return (
            fact in INITIAL_FACTS
            and fact not in STAGE_FACTS
            and question_id is not None
            and question_id not in self.answers
        )

    def _next_condition_question(self):
        facts = set(self.result["facts"])

        # a) pertanyaan penghubung untuk keluhan utama
        for fact in RELATED_SYMPTOMS.get(self.complaint, []):
            if fact not in facts and self._is_askable(fact):
                return QUESTION_FOR_FACT[fact]

        # b) pertanyaan yang diturunkan dari rule:
        #    rule belum terpicu, minimal satu condition sudah ada di working memory,
        #    dan SEMUA condition yang kurang bisa ditanyakan ke pengguna.
        fired = {step["rule_id"] for step in self.result["trace"]}
        for rule in sorted(RULES, key=lambda r: RULE_ORDER[r["id"]]):
            if rule["id"] in fired:
                continue
            present = [c for c in rule["conditions"] if c in facts]
            missing = [c for c in rule["conditions"] if c not in facts]
            if present and missing and all(self._is_askable(c) for c in missing):
                return QUESTION_FOR_FACT[missing[0]]
        return None

    # ---------- pertanyaan tahap ----------
    def _next_stage_question(self):
        """
        Tanyakan "masih bermasalah?" hanya jika ada rule yang MENUNGGU fakta tahap
        tersebut dan semua condition lainnya sudah terpenuhi.
        """
        facts = set(self.result["facts"])
        for stage_fact in STAGE_FACTS:
            if stage_fact in facts:
                continue
            question_id = QUESTION_FOR_FACT[stage_fact]
            if question_id in self.answers:
                return None
            for rule in RULES:
                if stage_fact in rule["conditions"]:
                    others = [c for c in rule["conditions"] if c != stage_fact]
                    if all(c in facts for c in others):
                        return question_id
            return None
        return None

    # ---------- rekomendasi ----------
    def _unshown_recommendations(self):
        return [rec for rec in self.result["recommendations"]
                if rec["rule_id"] not in self.shown_rule_ids]

    def recommendations_shown(self):
        return [rec for rec in self.result["recommendations"]
                if rec["rule_id"] in self.shown_rule_ids]

    # ---------- penjelasan ----------
    def explain(self, rule_id):
        """Penjelasan untuk rekomendasi yang sudah ditampilkan (berdasarkan trace)."""
        step = next((s for s in self.result["trace"] if s["rule_id"] == rule_id), None)
        if step is None or rule_id not in self.shown_rule_ids:
            return None
        return explain_fact(self.result, step["then"])

    def explain_plain(self, rule_id):
        """
        Penjelasan dalam bahasa sehari-hari: jawaban pengguna mana saja yang
        membuat rekomendasi ini muncul (ditelusuri dari trace, termasuk lewat
        fakta turunan).
        """
        if self.explain(rule_id) is None:
            return None
        user_facts = []

        def collect(fact):
            if fact in self.user_facts:
                if fact not in user_facts:
                    user_facts.append(fact)
                return
            producer = next((s for s in self.result["trace"]
                             if s["then"] == fact and s["new_fact"]), None)
            if producer:
                for condition in producer["conditions"]:
                    collect(condition)

        step = next(s for s in self.result["trace"] if s["rule_id"] == rule_id)
        for condition in step["conditions"]:
            collect(condition)

        complaint_labels = {c["fact"]: c["label"] for c in COMPLAINTS}
        lines = []
        for fact in user_facts:
            if fact in complaint_labels and fact == self.complaint:
                lines.append(f"Keluhan Anda: {complaint_labels[fact]}")
            else:
                question_id = QUESTION_FOR_FACT[fact]
                lines.append(f"\"{QUESTIONS[question_id]['text']}\" Jawaban Anda: {self.answers[question_id]}")
        return lines

    def trace(self):
        return self.result["trace"]

    # ---------- bantu ----------
    def _question_payload(self, question_id):
        question = QUESTIONS[question_id]
        note = None
        if question.get("stage") and not self.shown_rule_ids:
            note = "Belum ada langkah tahap dasar yang cocok dengan jawaban Anda sejauh ini."
        return {
            "id": question_id,
            "text": question["text"],
            "options": [label for label, _ in question["options"]],
            "is_stage": bool(question.get("stage")),
            "note": note,
            "number": len(self.asked) + 1,   # nomor urut pertanyaan (penunjuk kemajuan)
        }


# ============================================================
# 4. PEMERIKSAAN KELENGKAPAN (dipakai oleh tes)
# ============================================================
def check_question_coverage():
    """
    Setiap fakta awal yang muncul di conditions rule harus bisa diperoleh,
    baik dari pilihan keluhan maupun dari sebuah pertanyaan.
    """
    complaint_facts = {c["fact"] for c in COMPLAINTS}
    problems = []
    for fact in INITIAL_FACTS:
        if fact not in complaint_facts and fact not in QUESTION_FOR_FACT:
            problems.append(f"Fakta awal {fact!r} tidak punya pertanyaan maupun pilihan keluhan.")
    for fact in QUESTION_FOR_FACT:
        if fact not in INITIAL_FACTS:
            problems.append(f"Pertanyaan menghasilkan fakta yang tidak ada di knowledge base: {fact!r}")
    return problems
