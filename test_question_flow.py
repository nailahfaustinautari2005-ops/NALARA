"""
test_question_flow.py
=====================

Pengujian otomatis Tahap 3: question_flow.py dan chatbot_cli.py.
Jalankan dari folder project:

    python -m unittest -v test_question_flow

Semua jawaban pengguna disimulasikan, jadi tidak perlu mengetik apa pun.
"""

import ast
import os
import unittest

import knowledge_base as kb
import chatbot_cli
from question_flow import COMPLAINTS, QUESTIONS, Session, check_question_coverage

HERE = os.path.dirname(os.path.abspath(__file__))


def play(complaint, answers):
    """
    Jalankan satu percakapan dengan jawaban yang sudah ditentukan.
    answers: dict id_pertanyaan -> label jawaban (mis. "Ya").
    Kembalikan (daftar kejadian, session).
    """
    session = Session()
    session.choose_complaint(complaint)
    events = []
    for _ in range(100):  # pengaman agar tidak berputar tanpa akhir
        action = session.next_action()
        if action["type"] == "question":
            question = action["question"]
            label = answers[question["id"]]  # KeyError = pertanyaan tak terduga
            session.answer(question["id"], question["options"].index(label))
            events.append(("Q", question["id"]))
        elif action["type"] == "recommendations":
            events.append(("REC", [item["rule_id"] for item in action["items"]]))
        else:
            events.append(("END", action["reason"]))
            return events, session
    raise AssertionError("Percakapan tidak berakhir")


def asked(events):
    return [value for kind, value in events if kind == "Q"]


def shown(events):
    return [rule_id for kind, value in events if kind == "REC" for rule_id in value]


class TestKelengkapanPertanyaan(unittest.TestCase):

    def test_setiap_fakta_awal_bisa_diperoleh(self):
        self.assertEqual(check_question_coverage(), [])

    def test_keluhan_adalah_fakta_gejala_di_knowledge_base(self):
        for complaint in COMPLAINTS:
            self.assertEqual(kb.INITIAL_FACTS[complaint["fact"]]["group"], "gejala")

    def test_setiap_pertanyaan_punya_minimal_dua_pilihan(self):
        for question_id, question in QUESTIONS.items():
            self.assertGreaterEqual(len(question["options"]), 2, question_id)


class TestAlurPercakapan(unittest.TestCase):

    def test_tidak_menyala_hanya_menanyakan_charger(self):
        events, _ = play("no_power", {"q_charger": "Tidak", "q_persists_basic": "Tidak"})
        self.assertEqual(asked(events), ["q_charger", "q_persists_basic"])
        self.assertEqual(shown(events), ["R01"])
        self.assertEqual(events[-1], ("END", "resolved"))

    def test_tidak_menyala_sampai_eskalasi(self):
        events, _ = play("no_power", {"q_charger": "Ya", "q_persists_basic": "Ya",
                                      "q_persists_advanced": "Ya"})
        self.assertEqual(shown(events), ["R02", "R03", "R30"])

    def test_lambat_dan_panas_lintas_domain(self):
        answers = {"q_laptop_hot": "Ya", "q_soft_surface": "Ya", "q_vents_blocked": "Tidak",
                   "q_many_apps": "Ya", "q_disk_low": "Tidak",
                   "q_persists_basic": "Ya", "q_persists_advanced": "Ya"}
        events, _ = play("laptop_slow", answers)
        # Pertanyaan penghubung "panas?" ditanyakan pertama, lalu pertanyaan
        # pendinginan muncul karena R17 menghasilkan cooling_check_needed.
        self.assertEqual(asked(events)[0], "q_laptop_hot")
        self.assertIn("q_soft_surface", asked(events))
        self.assertEqual(shown(events), ["R20", "R25", "R26", "R22", "R28", "R29", "R30"])

    def test_lambat_tanpa_panas_tidak_menanyakan_pendinginan(self):
        answers = {"q_laptop_hot": "Tidak", "q_many_apps": "Tidak", "q_disk_low": "Ya",
                   "q_persists_basic": "Tidak"}
        events, _ = play("laptop_slow", answers)
        self.assertNotIn("q_soft_surface", asked(events))
        self.assertEqual(shown(events), ["R26", "R27"])

    def test_layar_gelap_rollback_hanya_ditanya_setelah_safe_mode(self):
        answers = {"q_external_monitor": "Tidak", "q_cursor": "Tidak",
                   "q_persists_basic": "Ya", "q_after_update": "Ya",
                   "q_persists_advanced": "Tidak"}
        events, _ = play("blank_screen", answers)
        order = asked(events)
        self.assertLess(order.index("q_persists_basic"), order.index("q_after_update"))
        self.assertEqual(shown(events), ["R11", "R14", "R15"])

    def test_baterai_berhenti_di_batas(self):
        events, _ = play("battery_not_charging", {"q_charge_limit": "Ya",
                                                  "q_persists_basic": "Ya"})
        self.assertEqual(shown(events), ["R31", "R07", "R09", "R10"])

    def test_pengisian_lambat_tidak_yakin_charger(self):
        events, _ = play("charging_slow", {"q_charger_original": "Tidak yakin",
                                           "q_persists_basic": "Tidak"})
        self.assertEqual(shown(events), ["R07", "R08"])
        self.assertNotIn("q_charge_limit", asked(events))

    def test_kipas_abnormal_langsung_eskalasi(self):
        answers = {"q_laptop_hot": "Tidak", "q_fan_abnormal": "Ya", "q_heavy_app": "Ya",
                   "q_persists_basic": "Tidak"}
        events, _ = play("fan_loud", answers)
        self.assertEqual(shown(events), ["R19", "R30"])

    def test_panas_tanpa_langkah_dasar_memberi_catatan(self):
        # Temuan: keluhan panas tanpa permukaan lunak / ventilasi tertutup
        # tidak punya rekomendasi tahap dasar di knowledge base.
        session = Session()
        session.choose_complaint("laptop_hot")
        for question_id, label in [("q_fan_loud", "Tidak"), ("q_fan_abnormal", "Tidak"),
                                   ("q_soft_surface", "Tidak"), ("q_vents_blocked", "Tidak")]:
            action = session.next_action()
            self.assertEqual(action["question"]["id"], question_id)
            session.answer(question_id, action["question"]["options"].index(label))
        action = session.next_action()
        self.assertEqual(action["question"]["id"], "q_persists_basic")
        self.assertIsNotNone(action["question"]["note"])

    def test_tidak_ada_pertanyaan_ganda(self):
        answers = {"q_laptop_hot": "Ya", "q_soft_surface": "Ya", "q_vents_blocked": "Ya",
                   "q_many_apps": "Ya", "q_disk_low": "Ya",
                   "q_persists_basic": "Ya", "q_persists_advanced": "Ya"}
        events, _ = play("laptop_slow", answers)
        self.assertEqual(len(asked(events)), len(set(asked(events))))

    def test_rekomendasi_tidak_ditampilkan_dua_kali(self):
        answers = {"q_charger": "Ya", "q_persists_basic": "Ya", "q_persists_advanced": "Ya"}
        events, _ = play("no_power", answers)
        self.assertEqual(len(shown(events)), len(set(shown(events))))


class TestSemuaRuleTercapaiLewatPercakapan(unittest.TestCase):
    """Telusuri semua kemungkinan jawaban; ke-31 rule harus bisa muncul."""

    def explore(self, complaint):
        fired = set()

        def walk(answer_path):
            session = Session()
            session.choose_complaint(complaint)
            for question_id, index in answer_path:
                action = session.next_action()
                while action["type"] == "recommendations":
                    action = session.next_action()
                session.answer(question_id, index)
            while True:
                action = session.next_action()
                if action["type"] == "recommendations":
                    continue
                if action["type"] == "finished":
                    fired.update(step["rule_id"] for step in session.trace())
                    return
                question = action["question"]
                for index in range(len(question["options"])):
                    walk(answer_path + [(question["id"], index)])
                return

        walk([])
        return fired

    def test_ke_31_rule_dapat_dicapai(self):
        reachable = set()
        for complaint in COMPLAINTS:
            reachable |= self.explore(complaint["fact"])
        self.assertEqual(sorted(reachable), sorted(rule["id"] for rule in kb.RULES))


class TestExplain(unittest.TestCase):

    def test_alasan_hanya_untuk_rekomendasi_yang_sudah_tampil(self):
        events, session = play("no_power", {"q_charger": "Tidak", "q_persists_basic": "Tidak"})
        self.assertIsNotNone(session.explain("R01"))
        self.assertIsNone(session.explain("R03"))  # tidak pernah tampil


class TestPenjelasanBahasaAwam(unittest.TestCase):

    def test_penjelasan_menyebut_jawaban_lewat_fakta_turunan(self):
        # R20 dipicu oleh cooling_check_needed (turunan dari laptop_hot) + soft_surface.
        answers = {"q_laptop_hot": "Ya", "q_soft_surface": "Ya", "q_vents_blocked": "Tidak",
                   "q_many_apps": "Tidak", "q_disk_low": "Tidak", "q_persists_basic": "Tidak"}
        _, session = play("laptop_slow", answers)
        text = "\n".join(session.explain_plain("R20"))
        self.assertIn("panas", text)
        self.assertIn("kasur", text)
        self.assertNotIn("cooling_check_needed", text)  # tanpa istilah teknis

    def test_penjelasan_keluhan_utama(self):
        _, session = play("no_power", {"q_charger": "Tidak", "q_persists_basic": "Tidak"})
        self.assertIn("Keluhan Anda: Laptop tidak menyala sama sekali",
                      session.explain_plain("R01"))


class TestInputTidakValid(unittest.TestCase):

    def test_keluhan_tidak_dikenal(self):
        with self.assertRaises(ValueError):
            Session().choose_complaint("laptop_meledak")

    def test_pilihan_jawaban_di_luar_rentang(self):
        session = Session()
        session.choose_complaint("no_power")
        with self.assertRaises(ValueError):
            session.answer("q_charger", 5)

    def test_pertanyaan_tidak_boleh_dijawab_dua_kali(self):
        session = Session()
        session.choose_complaint("no_power")
        session.answer("q_charger", 0)
        with self.assertRaises(ValueError):
            session.answer("q_charger", 1)


class TestChatbotTerminal(unittest.TestCase):
    """Menjalankan chatbot_cli.run() dengan ketikan pengguna yang disimulasikan."""

    def run_cli(self, typed):
        inputs = iter(typed)
        lines = []

        def fake_input(prompt):
            try:
                return next(inputs)
            except StopIteration:
                raise EOFError  # sama seperti input() saat masukan habis

        session = chatbot_cli.run(read=fake_input, write=lines.append)
        return "\n".join(lines), session

    def test_sesi_lengkap_dengan_alasan_dan_proses(self):
        typed = ["6",   # keluhan: kipas
                 "1",   # panas? Ya
                 "1",   # kipas abnormal? Ya
                 "1",   # aplikasi berat? Ya
                 "2",   # permukaan lunak? Tidak
                 "2",   # ventilasi tertutup? Tidak
                 "2",   # alasan untuk saran nomor 2 (R30)
                 "proses", "",
                 "2"]   # masih bermasalah? Tidak
        output, session = self.run_cli(typed)
        self.assertIn("1. Kipas lebih kencang", output)   # saran bernomor
        self.assertIn("(kode: R19)", output)
        self.assertIn("(kode: R30)", output)
        self.assertIn("Saran ini muncul karena jawaban Anda", output)
        self.assertIn("Jejak forward chaining", output)
        self.assertIn("teratasi", output)
        self.assertEqual(session.finished_reason, "resolved")

    def test_alasan_bisa_dengan_kode_rule(self):
        typed = ["1", "2", "R01", "", "2"]   # tidak menyala, charger tidak terpasang
        output, _ = self.run_cli(typed)
        self.assertIn("Saran ini muncul karena jawaban Anda", output)

    def test_nomor_saran_di_luar_rentang(self):
        typed = ["1", "2", "5", "", "2"]
        output, _ = self.run_cli(typed)
        self.assertIn("Ketik angka 1 sampai 1", output)

    def test_masukan_salah_diminta_ulang(self):
        typed = ["9", "abc", "1",  # keluhan: dua kali salah, lalu "tidak menyala"
                 "2", "", "2"]
        output, _ = self.run_cli(typed)
        self.assertIn("Masukkan angka 1 sampai 7", output)
        self.assertIn("(kode: R01)", output)

    def test_masukan_habis_tidak_error(self):
        output, _ = self.run_cli(["7"])  # input berhenti di tengah sesi
        self.assertIn("Sesi diakhiri", output)

    def test_ada_kalimat_pembuka_dan_nomor_pertanyaan(self):
        output, _ = self.run_cli(["1", "2", "", "1", "", "2"])
        self.assertIn("biasanya 2–7", output)
        self.assertIn("Pertanyaan 1:", output)
        self.assertIn("Pertanyaan 2:", output)

    def test_teks_r30_netral(self):
        # Audit v4: R30 tidak lagi mengklaim langkah mandiri "sudah dicoba".
        output, _ = self.run_cli(["6", "2", "1", "1", "2"])  # kipas berbunyi kasar -> R24 -> R30
        self.assertIn("Kondisi ini perlu pemeriksaan perangkat keras", output)
        self.assertNotIn("sudah dicoba", output)

    def test_keluar_kapan_saja(self):
        output, _ = self.run_cli(["7", "keluar"])
        self.assertIn("Sesi diakhiri", output)


class TestPemisahanLapisan(unittest.TestCase):

    def read(self, name):
        with open(os.path.join(HERE, name), encoding="utf-8") as f:
            return ast.parse(f.read())

    def test_question_flow_tanpa_input_dan_print(self):
        tree = self.read("question_flow.py")
        calls = {n.func.id for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertNotIn("input", calls)
        self.assertNotIn("print", calls)

    def test_tidak_ada_if_yang_menyebut_nama_keluhan(self):
        all_facts = set(kb.INITIAL_FACTS) | set(kb.DERIVED_FACTS) | set(kb.RECOMMENDATIONS)
        for name in ("question_flow.py", "chatbot_cli.py"):
            tree = self.read(name)
            offending = [
                (name, node.lineno)
                for node in ast.walk(tree) if isinstance(node, (ast.If, ast.IfExp, ast.While))
                for sub in ast.walk(node.test)
                if isinstance(sub, ast.Constant) and sub.value in all_facts
            ]
            self.assertEqual(offending, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
