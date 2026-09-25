"""
test_inference_engine.py
========================

Pengujian otomatis untuk inference_engine.py (Tahap 2).
Jalankan dari folder project:

    python -m unittest -v test_inference_engine

Tidak memerlukan library tambahan (unittest bawaan Python).
"""

import ast
import copy
import os
import unittest

import knowledge_base as kb
from inference_engine import forward_chain, explain


ENGINE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inference_engine.py")


def read_engine_source():
    with open(ENGINE_FILE, encoding="utf-8") as f:
        return f.read()


def fired_ids(result):
    """Daftar ID rule yang terpicu, sesuai urutan."""
    return [step["rule_id"] for step in result["trace"]]


def rec_ids(result):
    """Daftar ID rule rekomendasi, sesuai urutan tampil."""
    return [rec["rule_id"] for rec in result["recommendations"]]


class TestSkenarioPerDomain(unittest.TestCase):
    """Satu atau dua skenario untuk setiap domain masalah."""

    def test_tidak_menyala_charger_belum_terpasang(self):
        result = forward_chain({"no_power", "charger_not_connected"})
        self.assertEqual(fired_ids(result), ["R01"])

    def test_tidak_menyala_masih_bermasalah_setelah_dasar(self):
        result = forward_chain({"no_power", "charger_connected", "persists_after_basic"})
        self.assertEqual(rec_ids(result), ["R02", "R03"])

    def test_tidak_menyala_sampai_eskalasi(self):
        result = forward_chain(
            {"no_power", "charger_connected", "persists_after_basic", "persists_after_advanced"}
        )
        self.assertEqual(fired_ids(result), ["R02", "R03", "R04", "R30"])

    def test_pengisian_lambat_dengan_charger_bukan_bawaan(self):
        result = forward_chain({"charging_slow", "charger_or_cable_not_original"})
        self.assertEqual(fired_ids(result), ["R05", "R07", "R08"])
        self.assertIn("charging_issue", result["derived_facts"])

    def test_baterai_berhenti_di_batas_dan_urutan_prioritas(self):
        # Audit: R31 ditampilkan sebelum R09/R10, dan R09 sebelum R10.
        result = forward_chain(
            {"battery_not_charging", "charge_stops_at_limit", "persists_after_basic"}
        )
        recs = rec_ids(result)
        self.assertEqual(recs, ["R31", "R07", "R09", "R10"])
        self.assertLess(recs.index("R31"), recs.index("R09"))
        self.assertLess(recs.index("R09"), recs.index("R10"))

    def test_layar_gelap_dasar(self):
        result = forward_chain({"blank_screen", "external_monitor_connected", "cursor_visible"})
        self.assertEqual(rec_ids(result), ["R11", "R12", "R13"])

    def test_layar_gelap_rantai_safe_mode_ke_rollback(self):
        # R15 hanya bisa terpicu SETELAH R14 menghasilkan rec_enter_safe_mode.
        result = forward_chain(
            {"blank_screen", "problem_started_after_update", "persists_after_basic"}
        )
        ids = fired_ids(result)
        self.assertIn("R14", ids)
        self.assertIn("R15", ids)
        self.assertLess(ids.index("R14"), ids.index("R15"))

    def test_layar_gelap_tanpa_update_tidak_rollback(self):
        result = forward_chain({"blank_screen", "persists_after_basic"})
        self.assertIn("R14", fired_ids(result))
        self.assertNotIn("R15", fired_ids(result))

    def test_kipas_kencang_tanpa_aplikasi_berat(self):
        result = forward_chain({"fan_loud", "no_heavy_app_running", "vents_blocked"})
        self.assertEqual(fired_ids(result), ["R18", "R19", "R21"])

    def test_kipas_kencang_dengan_aplikasi_berat_tidak_ke_pendinginan(self):
        # Tanpa no_heavy_app_running, R18 tidak terpicu -> tidak ada cooling_check_needed.
        result = forward_chain({"fan_loud", "vents_blocked"})
        self.assertEqual(fired_ids(result), ["R19"])
        self.assertNotIn("cooling_check_needed", result["facts"])

    def test_kipas_berbunyi_abnormal_langsung_eskalasi(self):
        result = forward_chain({"fan_abnormal_noise"})
        self.assertEqual(fired_ids(result), ["R24", "R30"])

    def test_lambat_dan_panas_lintas_domain(self):
        # Skenario bagian 6 dokumen audit.
        result = forward_chain({"laptop_slow", "many_apps_running", "laptop_hot", "soft_surface"})
        self.assertEqual(fired_ids(result), ["R17", "R20", "R25", "R26"])


class TestPerilakuEngine(unittest.TestCase):
    """Sifat-sifat umum forward chaining."""

    def test_tanpa_fakta_tidak_ada_rule_terpicu(self):
        result = forward_chain(set())
        self.assertEqual(result["trace"], [])
        self.assertEqual(result["recommendations"], [])

    def test_refraction_setiap_rule_paling_banyak_sekali(self):
        all_initial = set(kb.INITIAL_FACTS)
        result = forward_chain(all_initial)
        ids = fired_ids(result)
        self.assertEqual(len(ids), len(set(ids)))

    def test_semua_fakta_awal_memicu_semua_rule(self):
        # Jika semua fakta awal benar, ke-31 rule harus terpicu.
        result = forward_chain(set(kb.INITIAL_FACTS))
        self.assertEqual(sorted(fired_ids(result)), sorted(r["id"] for r in kb.RULES))

    def test_satu_rule_per_siklus_dan_conflict_set_tercatat(self):
        result = forward_chain({"laptop_slow", "many_apps_running", "laptop_hot", "soft_surface"})
        for step in result["trace"]:
            self.assertIn(step["rule_id"], step["conflict_set"])
        cycles = [step["cycle"] for step in result["trace"]]
        self.assertEqual(cycles, list(range(1, len(cycles) + 1)))

    def test_rule_derived_didahulukan_dalam_tahap_yang_sama(self):
        result = forward_chain({"laptop_slow", "laptop_hot"})
        self.assertEqual(fired_ids(result)[0], "R17")

    def test_tahap_dasar_sebelum_lanjutan_sebelum_akhir(self):
        result = forward_chain(set(kb.INITIAL_FACTS))
        order = {"dasar": 0, "lanjutan": 1, "akhir": 2}
        stages = [order[step["stage"]] for step in result["trace"]]
        self.assertEqual(stages, sorted(stages))

    def test_hasil_deterministik(self):
        facts = {"battery_not_charging", "charge_stops_at_limit", "persists_after_basic"}
        self.assertEqual(forward_chain(facts), forward_chain(facts))

    def test_engine_tidak_mengubah_knowledge_base(self):
        before = copy.deepcopy(kb.RULES)
        forward_chain(set(kb.INITIAL_FACTS))
        self.assertEqual(kb.RULES, before)

    def test_rekomendasi_berisi_output_dari_knowledge_base(self):
        result = forward_chain({"no_power", "charger_not_connected"})
        r01 = next(rule for rule in kb.RULES if rule["id"] == "R01")
        self.assertEqual(result["recommendations"][0]["output"], r01["output"])


class TestInputTidakValid(unittest.TestCase):

    def test_fakta_typo_ditolak(self):
        with self.assertRaises(ValueError):
            forward_chain({"laptop_is_hot"})

    def test_fakta_turunan_tidak_boleh_dari_pengguna(self):
        with self.assertRaises(ValueError):
            forward_chain({"cooling_check_needed"})

    def test_rekomendasi_tidak_boleh_dari_pengguna(self):
        with self.assertRaises(ValueError):
            forward_chain({"rec_enter_safe_mode", "problem_started_after_update"})


class TestCakupanSemuaRule(unittest.TestCase):
    """Setiap rule harus bisa dicapai dari fakta awal yang minimal."""

    def minimal_initial_facts(self, fact, seen=None):
        """Uraikan fakta turunan/rekomendasi menjadi fakta awal (khusus untuk uji ini)."""
        seen = seen or set()
        if fact in kb.INITIAL_FACTS:
            return {fact}
        producer = next(r for r in kb.RULES if r["then"] == fact and r["id"] not in seen)
        facts = set()
        for condition in producer["conditions"]:
            facts |= self.minimal_initial_facts(condition, seen | {producer["id"]})
        return facts

    def test_setiap_rule_dapat_terpicu(self):
        for rule in kb.RULES:
            with self.subTest(rule=rule["id"]):
                initial = set()
                for condition in rule["conditions"]:
                    initial |= self.minimal_initial_facts(condition)
                result = forward_chain(initial)
                self.assertIn(rule["id"], fired_ids(result))


class TestExplain(unittest.TestCase):

    def test_penjelasan_menelusuri_rantai(self):
        result = forward_chain({"fan_abnormal_noise"})
        text = "\n".join(explain(result, "rec_hardware_diagnostic_or_service"))
        self.assertIn("R30", text)
        self.assertIn("R24", text)
        self.assertIn("fan_abnormal_noise: fakta dari pengguna", text)


class TestTidakAdaIfElseDomain(unittest.TestCase):
    """Engine tidak boleh berisi if/elif yang menguji nama fakta secara langsung."""

    def test_tidak_ada_if_yang_menyebut_nama_fakta(self):
        source = read_engine_source()
        tree = ast.parse(source)
        all_facts = set(kb.INITIAL_FACTS) | set(kb.DERIVED_FACTS) | set(kb.RECOMMENDATIONS)
        offending = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.IfExp, ast.While)):
                for sub in ast.walk(node.test):
                    if isinstance(sub, ast.Constant) and sub.value in all_facts:
                        offending.append((node.lineno, sub.value))
                    if isinstance(sub, ast.Name) and sub.id in all_facts:
                        offending.append((node.lineno, sub.id))
        self.assertEqual(offending, [])

    def test_tidak_ada_input_pengguna(self):
        source = read_engine_source()
        tree = ast.parse(source)
        calls = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertNotIn("input", calls)


if __name__ == "__main__":
    unittest.main(verbosity=2)
