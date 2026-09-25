"""
test_app.py
===========

TAHAP 4 — Tes otomatis untuk aplikasi web (app.py) memakai AppTest dari Streamlit.
Tes ini "mengklik" tombol seperti pengguna, tanpa membuka browser.

Jalankan dari folder project:

    python -m unittest test_app -v

Tes paling penting: saran yang tampil di WEB harus SAMA PERSIS dengan saran dari
question_flow.py (yang juga dipakai chatbot terminal). Jadi tampilan web tidak
mengubah hasil penalaran.

Tes semua jalur jawaban (460 jalur, sekitar 7 menit) dilewati secara bawaan.
Untuk menjalankannya (Windows PowerShell):

    $env:NALARA_SEMUA_JALUR="1"; python -m unittest test_app -v
"""

import ast
import logging
import os
import re
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest



def quiet_streamlit_logs():
    """Sembunyikan peringatan Streamlit yang wajar muncul saat mode tes."""
    for name in list(logging.root.manager.loggerDict):
        if name.startswith("streamlit"):
            logging.getLogger(name).setLevel(logging.ERROR)


quiet_streamlit_logs()

import app  # noqa: E402
from chatbot_cli import DISCLAIMER
from knowledge_base import RECOMMENDATIONS, RULES
from question_flow import COMPLAINTS, QUESTIONS, Session  # noqa: E402

HERE = Path(__file__).parent
APP_FILE = str(HERE / "app.py")
CODE_PATTERN = re.compile(r"kode: (R\d\d)")


# ------------------------------------------------------------
# Bantuan: menjalankan aplikasi dan membaca layar
# ------------------------------------------------------------
def new_app():
    quiet_streamlit_logs()
    at = AppTest.from_file(APP_FILE, default_timeout=30)
    at.run()
    return at


def markdown_text(at):
    return [m.value for m in at.markdown]


def shown_codes(at):
    """Kode rule pada kartu saran yang sedang tampil di layar (berurutan)."""
    return [code for text in markdown_text(at) for code in CODE_PATTERN.findall(text)]


def expander_labels(at):
    # AppTest membaca expander yang memakai ikon sebagai elemen "status".
    return [e.label for e in at.expander] + [e.label for e in at.status]


def answer_buttons(at):
    """Tombol jawaban yang sedang tampil: [(question_id, index, tombol)]."""
    result = []
    for button in at.button:
        if button.key and button.key.startswith("ans_"):
            question_id, index = button.key[4:].rsplit("_", 1)
            result.append((question_id, int(index), button))
    return result


def play(complaint, choose):
    """
    Mainkan satu sesi di aplikasi web.
    choose(question_id, jumlah_pilihan, langkah_ke) -> indeks jawaban.
    Mengembalikan (at, daftar jawaban, blok saran yang tampil di web).
    """
    at = new_app()
    at.button(key=f"complaint_{complaint}").click().run()
    answers, blocks, step = [], [], 0
    codes = shown_codes(at)
    if codes:
        blocks.append(codes)
    while True:
        buttons = answer_buttons(at)
        if not buttons:
            return at, answers, blocks
        question_id = buttons[0][0]
        index = choose(question_id, len(buttons), step)
        answers.append((question_id, index))
        next(b for q, i, b in buttons if i == index).click().run()
        assert not at.exception, at.exception
        step += 1
        codes = shown_codes(at)
        if codes:
            blocks.append(codes)


def reference_blocks(complaint, answers):
    """Blok saran menurut question_flow.Session untuk jawaban yang sama."""
    session = Session()
    session.choose_complaint(complaint)
    blocks, remaining = [], list(answers)
    while True:
        action = session.next_action()
        if action["type"] == "recommendations":
            blocks.append([item["rule_id"] for item in action["items"]])
        elif action["type"] == "question":
            question_id, index = remaining.pop(0)
            assert question_id == action["question"]["id"], (question_id, action["question"]["id"])
            session.answer(question_id, index)
        else:
            assert not remaining
            return blocks, session


def first_option(question_id, count, step):
    return 0


def last_option(question_id, count, step):
    return count - 1


def alternate(question_id, count, step):
    return step % count


def prefer(label):
    """Pilih jawaban dengan label tertentu jika ada (mis. 'Tidak'), selain itu pilihan pertama."""
    def choose(question_id, count, step):
        labels = [option for option, _ in QUESTIONS[question_id]["options"]]
        return labels.index(label) if label in labels else 0
    return choose


# ============================================================
# 1. Teks tampilan lengkap & konsisten dengan knowledge base
# ============================================================
class TestDisplayTexts(unittest.TestCase):
    def test_every_complaint_has_icon(self):
        self.assertEqual(set(app.COMPLAINT_ICONS), {c["fact"] for c in COMPLAINTS})

    def test_every_question_has_short_label(self):
        self.assertEqual(set(app.SHORT_LABELS), set(QUESTIONS))

    def test_stage_labels_match_stage_options(self):
        for question in QUESTIONS.values():
            if question.get("stage"):
                labels = [label for label, _ in question["options"]]
                self.assertEqual(set(labels), set(app.STAGE_OPTION_LABELS))

    def test_escalation_facts_exist_in_knowledge_base(self):
        self.assertTrue(app.ESCALATION_FACTS <= set(RECOMMENDATIONS))

    def test_mascot_files_exist(self):
        for name in ("menyapa", "berpikir", "ide", "hore", "peduli"):
            self.assertTrue((HERE / "assets" / f"lara_{name}.svg").exists(), name)
            self.assertTrue((HERE / "assets" / f"lara_{name}.png").exists(), name)

    def test_theme_file_exists(self):
        config = (HERE / ".streamlit" / "config.toml").read_text(encoding="utf-8")
        self.assertIn('primaryColor = "#2F6FC9"', config)
        self.assertIn('base = "light"', config)


# ============================================================
# 2. Pemisahan logika & tampilan
# ============================================================
class TestSeparation(unittest.TestCase):
    def test_app_uses_logic_only_through_question_flow(self):
        tree = ast.parse((HERE / "app.py").read_text(encoding="utf-8"))
        modules = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        modules |= {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
                    for alias in node.names}
        self.assertNotIn("knowledge_base", modules)
        self.assertNotIn("inference_engine", modules)
        self.assertIn("question_flow", modules)

    def test_app_does_not_mention_rule_ids(self):
        """app.py tidak boleh memuat logika per rule (mis. if rule_id == 'R20')."""
        source = (HERE / "app.py").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"['\"]R\d\d['\"]", source), [])


# ============================================================
# 3. Layar-layar
# ============================================================
class TestScreens(unittest.TestCase):
    def test_home_screen(self):
        at = new_app()
        self.assertFalse(at.exception)
        labels = [b.label for b in at.button if b.key and b.key.startswith("complaint_")]
        self.assertEqual(labels, [c["label"] for c in COMPLAINTS])
        self.assertEqual(at.info[0].value, DISCLAIMER.removeprefix("Catatan: "))
        self.assertTrue(any("NALARA" in text for text in markdown_text(at)))

    def test_question_screen(self):
        at = new_app()
        at.button(key="complaint_laptop_slow").click().run()
        self.assertTrue(any("Pertanyaan 1" in text for text in markdown_text(at)))
        self.assertTrue(any(QUESTIONS["q_laptop_hot"]["text"] in text for text in markdown_text(at)))
        self.assertEqual([b.label for _, _, b in answer_buttons(at)], ["Ya", "Tidak", "Tidak tahu"])
        self.assertEqual(len(at.get("progress")), 1)

    def test_previous_answers_are_listed(self):
        at = new_app()
        at.button(key="complaint_laptop_slow").click().run()
        at.button(key="ans_q_laptop_hot_0").click().run()
        self.assertTrue(any("Badan laptop terasa sangat panas" in text and "<b>Ya</b>" in text
                            for text in markdown_text(at)))
        # tombol pertanyaan yang sudah dijawab tidak tampil lagi
        self.assertNotIn("q_laptop_hot", {q for q, _, _ in answer_buttons(at)})

    def test_recommendation_screen_basic(self):
        at, _, blocks = play("laptop_slow", first_option)
        self.assertEqual(blocks[0], ["R20", "R21", "R25", "R26", "R27"])

    def test_recommendation_screen_shows_stage_question(self):
        at = new_app()
        at.button(key="complaint_no_power").click().run()
        at.button(key="ans_q_charger_0").click().run()
        self.assertEqual(shown_codes(at), ["R02"])
        self.assertTrue(any("TAHAP DASAR" in text for text in markdown_text(at)))
        self.assertEqual([b.label for _, _, b in answer_buttons(at)], ["Ya, masih", "Tidak, sudah teratasi"])
        labels = expander_labels(at)
        self.assertIn("Mengapa saran ini?", labels)
        self.assertTrue(any("forward chaining" in label for label in labels))

    def test_why_explanation_uses_user_answers(self):
        at = new_app()
        at.button(key="complaint_no_power").click().run()
        at.button(key="ans_q_charger_0").click().run()
        why = [text for text in markdown_text(at) if "Saran ini muncul karena jawaban Anda" in text]
        self.assertEqual(len(why), 1)
        self.assertIn("Keluhan Anda: Laptop tidak menyala sama sekali", why[0])
        self.assertIn("Jawaban Anda: Ya", why[0])

    def test_final_stage_escalation_screen(self):
        at = new_app()
        at.button(key="complaint_no_power").click().run()
        at.button(key="ans_q_charger_0").click().run()
        at.button(key="ans_q_persists_basic_0").click().run()
        self.assertTrue(any("TAHAP LANJUTAN" in text for text in markdown_text(at)))
        at.button(key="ans_q_persists_advanced_0").click().run()
        self.assertEqual(shown_codes(at), ["R30"])
        texts = markdown_text(at)
        self.assertTrue(any("TAHAP AKHIR" in text for text in texts))
        self.assertTrue(any("Sepertinya perlu dicek ahlinya" in text for text in texts))
        self.assertEqual(len(at.get("download_button")), 1)
        self.assertEqual(answer_buttons(at), [])

    def test_resolved_screen(self):
        at = new_app()
        at.button(key="complaint_no_power").click().run()
        at.button(key="ans_q_charger_0").click().run()
        at.button(key="ans_q_persists_basic_1").click().run()   # Tidak, sudah teratasi
        texts = markdown_text(at)
        self.assertTrue(any("Hore, masalahnya teratasi!" in text for text in texts))
        self.assertTrue(any("Langkah yang sudah dicoba" in text and "Periksa sambungan charger" in text
                            for text in texts))

    def test_note_when_no_basic_recommendation(self):
        """Keterbatasan yang terdokumentasi (audit v4): panas tanpa kasur/ventilasi tertutup."""
        note = "Belum ada langkah tahap dasar yang cocok dengan jawaban Anda sejauh ini."
        at = new_app()
        at.button(key="complaint_laptop_hot").click().run()
        while True:
            question_id = answer_buttons(at)[0][0]
            if QUESTIONS[question_id].get("stage"):
                break
            labels = [option for option, _ in QUESTIONS[question_id]["options"]]
            at.button(key=f"ans_{question_id}_{labels.index('Tidak')}").click().run()
        self.assertIn(note, [info.value for info in at.info])

    def test_restart_returns_home(self):
        at = new_app()
        at.button(key="complaint_laptop_slow").click().run()
        at.button(key="restart_q").click().run()
        self.assertEqual(len([b for b in at.button if b.key and b.key.startswith("complaint_")]), 7)

    def test_new_complaint_after_finish(self):
        at = new_app()
        at.button(key="complaint_no_power").click().run()
        at.button(key="ans_q_charger_0").click().run()
        at.button(key="ans_q_persists_basic_1").click().run()
        at.button(key="restart_done").click().run()
        self.assertEqual(len([b for b in at.button if b.key and b.key.startswith("complaint_")]), 7)

    def test_summary_text(self):
        session = Session()
        session.choose_complaint("no_power")
        session.next_action()
        session.answer("q_charger", 0)
        session.next_action()
        summary = app.build_summary(session)
        self.assertIn("Keluhan utama: Laptop tidak menyala sama sekali", summary)
        self.assertIn("-> Ya", summary)
        self.assertIn("(kode: R02)", summary)
        self.assertIn(DISCLAIMER, summary)


# ============================================================
# 4. Web == question_flow (hasil penalaran tidak berubah)
# ============================================================
class TestWebMatchesQuestionFlow(unittest.TestCase):
    def test_representative_paths(self):
        for complaint in [c["fact"] for c in COMPLAINTS]:
            for policy in (first_option, last_option, alternate, prefer("Tidak")):
                with self.subTest(complaint=complaint, policy=getattr(policy, "__name__", "prefer")):
                    _, answers, web_blocks = play(complaint, policy)
                    expected, _ = reference_blocks(complaint, answers)
                    self.assertEqual(web_blocks, expected)

    @unittest.skipUnless(os.environ.get("NALARA_SEMUA_JALUR") == "1",
                         "tes semua jalur dilewati (set NALARA_SEMUA_JALUR=1 untuk menjalankan)")
    def test_all_paths(self):
        seen_rules, path_count = set(), 0

        def explore(complaint, prefix):
            nonlocal path_count

            def choose(question_id, count, step):
                if step < len(prefix):
                    return prefix[step]
                raise _Branch(count)

            try:
                _, answers, web_blocks = play(complaint, choose)
            except _Branch as branch:
                for index in range(branch.count):
                    explore(complaint, prefix + [index])
                return
            expected, session = reference_blocks(complaint, answers)
            self.assertEqual(web_blocks, expected, (complaint, answers))
            seen_rules.update(step["rule_id"] for step in session.trace())
            path_count += 1

        for complaint in [c["fact"] for c in COMPLAINTS]:
            explore(complaint, [])
        self.assertEqual(path_count, 460)
        self.assertEqual(seen_rules, {rule["id"] for rule in RULES})


class _Branch(Exception):
    def __init__(self, count):
        super().__init__(count)
        self.count = count


if __name__ == "__main__":
    unittest.main()
