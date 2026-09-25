"""
inference_engine.py
===================

TAHAP 2 — Inference engine dengan metode FORWARD CHAINING.

File ini TIDAK berisi pengetahuan troubleshooting. Semua pengetahuan ada di
knowledge_base.py (31 rule). Engine di sini hanya algoritma umum yang:

  1. menerima fakta awal dari pengguna (working memory awal),
  2. MATCH    : mencari semua rule yang seluruh conditions-nya ada di working memory
                dan belum pernah terpicu  -> disebut "conflict set",
  3. SELECT   : memilih SATU rule dari conflict set (conflict resolution),
  4. FIRE     : menambahkan fakta THEN rule itu ke working memory,
  5. mengulang langkah 2–4 sampai conflict set kosong (tidak ada fakta baru).

Engine tidak pernah menyebut nama gejala tertentu (tidak ada `if laptop_slow:`).
Satu-satunya hal yang menyebut ID rule adalah tabel SALIENCE di bawah, yang
mencatat keputusan prioritas dari dokumen audit.

Belum ada chatbot, UI, atau input() — itu untuk tahap berikutnya.
"""

from knowledge_base import RULES, INITIAL_FACTS, DERIVED_FACTS, RECOMMENDATIONS


# ============================================================
# KONFIGURASI CONFLICT RESOLUTION
# ------------------------------------------------------------
# Jika lebih dari satu rule siap terpicu, engine memilih berdasarkan urutan:
#   1. TAHAP   : tahap dasar dulu, lalu lanjutan, lalu akhir.
#   2. JENIS   : rule "derived" dulu, agar fakta perantara cepat tersedia.
#   3. SALIENCE: angka lebih besar didahulukan (default 0).
#   4. URUTAN  : urutan rule di knowledge base (R01, R02, ...).
# ============================================================

# Tahap sebuah fakta awal. Fakta awal lain bertahap 0 (dasar).
STAGE_OF_INITIAL_FACT = {
    "persists_after_basic": 1,     # masalah masih ada setelah langkah dasar
    "persists_after_advanced": 2,  # masalah masih ada setelah langkah lanjutan
}
STAGE_NAMES = {0: "dasar", 1: "lanjutan", 2: "akhir"}

TYPE_RANK = {"derived": 0, "recommendation": 1}

# Keputusan prioritas dari dokumen audit (v3):
#   - R31 (batas pengisian) ditampilkan lebih dulu daripada R09/R10.
#   - R09 (power reset) ditampilkan sebelum R10 (diagnostik baterai).
SALIENCE = {
    "R31": 2,
    "R09": 1,
}

RULE_ORDER = {rule["id"]: index for index, rule in enumerate(RULES)}


# ============================================================
# 1. PEMERIKSAAN FAKTA AWAL
# ============================================================
def check_initial_facts(initial_facts):
    """
    Fakta awal hanya boleh berasal dari INITIAL_FACTS.
    Fakta turunan dan rekomendasi tidak boleh dimasukkan pengguna,
    karena keduanya harus DIHASILKAN oleh inferensi.
    """
    unknown = []
    not_allowed = []
    for fact in initial_facts:
        if fact in INITIAL_FACTS:
            continue
        if fact in DERIVED_FACTS or fact in RECOMMENDATIONS:
            not_allowed.append(fact)
        else:
            unknown.append(fact)
    if unknown:
        raise ValueError(f"Fakta tidak dikenal (cek ejaan): {sorted(unknown)}")
    if not_allowed:
        raise ValueError(
            f"Fakta ini hanya boleh dihasilkan oleh rule, bukan dari pengguna: {sorted(not_allowed)}"
        )


# ============================================================
# 2. MATCH — membentuk conflict set
# ============================================================
def match(rules, working_memory, fired_rule_ids):
    """
    Kembalikan semua rule yang:
      - seluruh conditions-nya ada di working memory, dan
      - belum pernah terpicu (REFRACTION: satu rule hanya terpicu sekali).
    """
    conflict_set = []
    for rule in rules:
        if rule["id"] in fired_rule_ids:
            continue
        if all(condition in working_memory for condition in rule["conditions"]):
            conflict_set.append(rule)
    return conflict_set


# ============================================================
# 3. SELECT — conflict resolution
# ============================================================
def rule_stage(rule, fact_stage):
    """Tahap sebuah rule = tahap tertinggi dari fakta-fakta pemicunya."""
    return max(fact_stage[condition] for condition in rule["conditions"])


def priority_key(rule, fact_stage):
    """Kunci pengurutan; nilai yang lebih kecil dipilih lebih dulu."""
    return (
        rule_stage(rule, fact_stage),
        TYPE_RANK[rule["type"]],
        -SALIENCE.get(rule["id"], 0),
        RULE_ORDER.get(rule["id"], len(RULE_ORDER)),
    )


def select(conflict_set, fact_stage):
    """Pilih satu rule dari conflict set berdasarkan priority_key."""
    return min(conflict_set, key=lambda rule: priority_key(rule, fact_stage))


# ============================================================
# 4. FORWARD CHAINING — siklus match -> select -> fire
# ============================================================
def forward_chain(initial_facts, rules=RULES):
    """
    Jalankan forward chaining dari fakta awal.

    Parameter
    ---------
    initial_facts : kumpulan nama fakta dari pengguna, misalnya
                    {"laptop_slow", "many_apps_running"}
    rules         : daftar rule (default: 31 rule dari knowledge_base.py)

    Hasil (dictionary)
    ------------------
    initial_facts   : fakta awal (terurut)
    facts           : seluruh working memory akhir (terurut)
    trace           : langkah-langkah inferensi, satu entri per rule yang terpicu
    derived_facts   : fakta turunan yang dihasilkan
    recommendations : rekomendasi sesuai urutan terpicu (berisi output untuk pengguna)
    """
    initial_facts = set(initial_facts)
    check_initial_facts(initial_facts)

    working_memory = set(initial_facts)
    fact_stage = {fact: STAGE_OF_INITIAL_FACT.get(fact, 0) for fact in initial_facts}
    fired_rule_ids = set()
    trace = []

    max_cycles = len(rules)  # dengan refraction, tiap rule paling banyak terpicu sekali
    for cycle in range(1, max_cycles + 1):
        conflict_set = match(rules, working_memory, fired_rule_ids)
        if not conflict_set:
            break  # tidak ada rule yang bisa terpicu lagi -> inferensi selesai

        rule = select(conflict_set, fact_stage)
        stage = rule_stage(rule, fact_stage)

        # FIRE
        fired_rule_ids.add(rule["id"])
        is_new_fact = rule["then"] not in working_memory
        if is_new_fact:
            working_memory.add(rule["then"])
            fact_stage[rule["then"]] = stage

        trace.append({
            "cycle": cycle,
            "conflict_set": [r["id"] for r in conflict_set],
            "rule_id": rule["id"],
            "rule_name": rule["name"],
            "conditions": list(rule["conditions"]),
            "then": rule["then"],
            "type": rule["type"],
            "stage": STAGE_NAMES[stage],
            "new_fact": is_new_fact,
            "output": rule["output"],
        })

    recommendations = [
        {
            "rule_id": step["rule_id"],
            "fact": step["then"],
            "stage": step["stage"],
            "output": step["output"],
        }
        for step in trace
        if step["type"] == "recommendation"
    ]
    derived = [step["then"] for step in trace if step["type"] == "derived" and step["new_fact"]]

    return {
        "initial_facts": sorted(initial_facts),
        "facts": sorted(working_memory),
        "trace": trace,
        "derived_facts": derived,
        "recommendations": recommendations,
    }


# ============================================================
# 5. EXPLAIN — "Mengapa fakta ini muncul?"
# ============================================================
def explain(result, fact, _depth=0):
    """
    Telusuri balik (dari hasil trace) bagaimana sebuah fakta diperoleh.
    Ini hanya membaca catatan inferensi yang sudah terjadi, bukan melakukan
    penalaran baru.
    """
    indent = "  " * _depth
    if fact in result["initial_facts"]:
        return [f"{indent}- {fact}: fakta dari pengguna"]
    producer = next((step for step in result["trace"] if step["then"] == fact and step["new_fact"]), None)
    if producer is None:
        return [f"{indent}- {fact}: tidak ada di working memory"]
    lines = [
        f"{indent}- {fact}: dihasilkan oleh {producer['rule_id']} "
        f"({producer['rule_name']}) pada siklus {producer['cycle']}, karena:"
    ]
    for condition in producer["conditions"]:
        lines.extend(explain(result, condition, _depth + 1))
    return lines


# ============================================================
# DEMO (bukan chatbot): menjalankan satu skenario contoh dan
# menampilkan jejak inferensinya. Tidak meminta input pengguna.
# ============================================================
def print_result(title, result):
    print("=" * 72)
    print(title)
    print("Fakta awal:", ", ".join(result["initial_facts"]))
    print("-" * 72)
    for step in result["trace"]:
        conds = " AND ".join(step["conditions"])
        print(f"Siklus {step['cycle']:>2} | conflict set {step['conflict_set']}")
        print(f"          terpicu {step['rule_id']} [{step['type']}, tahap {step['stage']}]: "
              f"IF {conds} THEN {step['then']}")
    print("-" * 72)
    print("Fakta turunan :", ", ".join(result["derived_facts"]) or "-")
    print("Rekomendasi   :")
    for rec in result["recommendations"]:
        print(f"  [{rec['rule_id']}] ({rec['stage']}) {rec['output']}")
    print()


if __name__ == "__main__":
    # Skenario contoh dari dokumen audit (bagian 6): laptop lambat, panas,
    # dipakai di kasur, banyak aplikasi terbuka. Dijalankan tiga kali untuk
    # menunjukkan tahap dasar -> lanjutan -> akhir.
    base = {"laptop_slow", "many_apps_running", "laptop_hot", "soft_surface"}

    step1 = forward_chain(base)
    print_result("SKENARIO 1 — tahap dasar", step1)

    step2 = forward_chain(base | {"persists_after_basic"})
    print_result("SKENARIO 2 — masalah masih ada setelah langkah dasar", step2)

    step3 = forward_chain(base | {"persists_after_basic", "persists_after_advanced"})
    print_result("SKENARIO 3 — masalah masih ada setelah langkah lanjutan", step3)

    print("Penjelasan untuk rec_hardware_diagnostic_or_service:")
    for line in explain(step3, "rec_hardware_diagnostic_or_service"):
        print(line)
