"""
knowledge_base.py
=================

Knowledge base untuk proyek:
"Pengembangan Asisten Troubleshooting Masalah Umum pada Laptop
 Berbasis Knowledge-Based System dengan Forward Chaining"

TAHAP 1 — hanya DATA.
File ini berisi 31 FINAL RULE hasil audit (versi 3) dalam bentuk struktur data
Python. File ini TIDAK melakukan penalaran (reasoning). Inference engine
(forward chaining) akan dibuat di file terpisah pada tahap berikutnya.

Isi file:
  1. SOURCES          : daftar sumber resmi yang dirujuk rule (kode S1–S14, T1–T3)
  2. INITIAL_FACTS    : fakta awal yang diperoleh dari jawaban pengguna
  3. DERIVED_FACTS    : fakta turunan yang hanya dihasilkan oleh rule
  4. RECOMMENDATIONS  : fakta rekomendasi (diawali "rec_") yang ditampilkan ke pengguna
  5. RULES            : 31 rule IF-THEN
  6. validate_knowledge_base() : pemeriksaan STRUKTUR data (bukan reasoning)

Riwayat perubahan:
  - Audit v3 (23 Sep 2026): 31 rule final.
  - Audit v4 (25 Sep 2026): hanya teks output R30 yang diubah. Kalimat pertama
    "Langkah mandiri yang aman sudah dicoba." diganti menjadi
    "Kondisi ini perlu pemeriksaan perangkat keras." karena R30 juga bisa
    muncul langsung dari R24 (kipas berbunyi kasar) sebelum ada langkah yang
    dicoba. Conditions, THEN, type, dan source tidak berubah.
"""

import re
from difflib import SequenceMatcher


# ============================================================
# 1. SOURCES
# ------------------------------------------------------------
# Kode sumber sama dengan dokumen audit.
# kind = "utama"    -> sumber dari daftar awal proyek (S1–S14)
# kind = "tambahan" -> halaman resmi vendor yang sama, sebagai pelengkap (T1–T3)
# ============================================================
SOURCES = {
    "S1": {
        "vendor": "Microsoft",
        "title": "PC is charging slowly or discharging while it’s plugged in",
        "url": "https://support.microsoft.com/en-us/windows/experience/power-battery/pc-is-charging-slowly-or-discharging-while-it-s-plugged-in",
        "kind": "utama",
    },
    "S2": {
        "vendor": "Microsoft",
        "title": "Troubleshooting blank screens in Windows",
        "url": "https://support.microsoft.com/en-us/windows/hardware/display-graphics/troubleshooting-blank-screens-in-windows",
        "kind": "utama",
    },
    "S3": {
        "vendor": "Microsoft",
        "title": "Tips to improve PC performance in Windows",
        "url": "https://support.microsoft.com/en-us/windows/experience/performance-optimization/tips-to-improve-pc-performance-in-windows",
        "kind": "utama",
    },
    "S4": {
        "vendor": "ASUS",
        "title": "[Windows 11/10] Troubleshooting - Overheating and Fan issues (FAQ 1015064)",
        "url": "https://www.asus.com/support/faq/1015064/",
        "kind": "utama",
    },
    "S5": {
        "vendor": "ASUS",
        "title": "Troubleshooting - Slow Charging / Battery Draining while Plugged in (FAQ 1043611)",
        "url": "https://www.asus.com/support/faq/1043611/",
        "kind": "utama",
    },
    "S6": {
        "vendor": "ASUS",
        "title": "Battery and Power Adapter (Charger) Specifications and Recommended Usage (FAQ 1015066)",
        "url": "https://www.asus.com/support/faq/1015066/",
        "kind": "utama",
    },
    "S7": {
        "vendor": "HP",
        "title": "HP Battery Check: Fix laptop battery not charging",
        "url": "https://support.hp.com/us-en/help/computer/battery-adapter-issues",
        "kind": "utama",
    },
    "S8": {
        "vendor": "HP",
        "title": "How to Fix HP Computer and Laptop Power On and Boot Up Problems",
        "url": "https://support.hp.com/bg-en/help/computer/power-boot-issues",
        "kind": "utama",
    },
    "S9": {
        "vendor": "HP",
        "title": "HP Notebook PCs - Fan is noisy and spins constantly (Windows)",
        "url": "https://support.hp.com/us-en/document/ish_3045299-2819686-16",
        "kind": "utama",
    },
    "S10": {
        "vendor": "HP",
        "title": "Reduce heat inside the laptop to prevent overheating in Windows",
        "url": "https://support.hp.com/si-en/document/ish_3894569-1692683-16",
        "kind": "utama",
    },
    "S11": {
        "vendor": "Lenovo",
        "title": "Troubleshooting battery issues - PC (HT080185)",
        "url": "https://support.lenovo.com/sg/en/solutions/ht080185-troubleshooting-battery-issues-thinkpad",
        "kind": "utama",
    },
    "S12": {
        "vendor": "Lenovo",
        "title": "Fan runs at a higher than expected speed - Windows (HT077046)",
        "url": "https://pcsupport.lenovo.com/us/en/solutions/ht077046",
        "kind": "utama",
    },
    "S13": {
        "vendor": "Lenovo",
        "title": "Freezing or slow performance issues - Windows 10, 11 (HT510168)",
        "url": "https://pcsupport.lenovo.com/us/en/solutions/ht510168",
        "kind": "utama",
    },
    "S14": {
        "vendor": "Lenovo",
        "title": "No power or system does not run on battery power - ThinkPad (HT080218)",
        "url": "https://pcsupport.lenovo.com/us/en/solutions/ht080218",
        "kind": "utama",
    },
    "T1": {
        "vendor": "ASUS",
        "title": "Troubleshooting - Device Boot Failure or No Display After Boot (Black Screen) (FAQ 1014276)",
        "url": "https://www.asus.com/support/faq/1014276/",
        "kind": "tambahan",
    },
    "T2": {
        "vendor": "ASUS",
        "title": "Troubleshooting - Battery not supplying power/charging… (FAQ 1012793)",
        "url": "https://www.asus.com/support/faq/1012793/",
        "kind": "tambahan",
    },
    "T3": {
        "vendor": "HP",
        "title": "HP PCs - How to power reset your computer",
        "url": "https://support.hp.com/us-en/document/ish_1997208-1551050-16",
        "kind": "tambahan",
    },
}


# ============================================================
# 2. INITIAL FACTS (fakta awal dari pengguna)
# ------------------------------------------------------------
# group:
#   "gejala"  -> keluhan/gejala yang dialami pengguna
#   "kondisi" -> keadaan tambahan yang ditanyakan untuk memperjelas gejala
#   "tahap"   -> jawaban "masalah masih terjadi?" setelah rekomendasi dicoba
# ============================================================
INITIAL_FACTS = {
    "no_power": {"group": "gejala", "description": (
            "Laptop sama sekali tidak menyala: tidak ada lampu, suara kipas, atau gambar "
            "saat tombol power ditekan."
        )},
    "blank_screen": {"group": "gejala", "description": (
            "Laptop tampak menyala (ada lampu atau suara kipas), tetapi layarnya "
            "hitam/kosong."
        )},
    "charging_slow": {"group": "gejala", "description": (
            "Saat charger terpasang, Windows menampilkan 'charging slowly' atau persentase "
            "baterai justru turun."
        )},
    "battery_not_charging": {"group": "gejala", "description": (
            "Charger terpasang, tetapi persentase baterai tidak bertambah atau selalu "
            "berhenti di angka tertentu."
        )},
    "laptop_hot": {"group": "gejala", "description": (
            "Badan laptop terasa jauh lebih panas dari biasanya (bisa keluhan utama atau "
            "jawaban di alur lambat/kipas)."
        )},
    "fan_loud": {"group": "gejala", "description": "Kipas terdengar kencang atau berputar terus-menerus."},
    "laptop_slow": {"group": "gejala", "description": "Laptop lambat atau sering tersendat."},
    "charger_not_connected": {"group": "kondisi", "description": "Charger tidak terpasang ke laptop dan/atau ke stopkontak."},
    "charger_connected": {"group": "kondisi", "description": "Charger terpasang ke laptop dan ke stopkontak."},
    "charger_or_cable_not_original": {"group": "kondisi", "description": (
            "Charger atau kabel bukan bawaan/rekomendasi produsen laptop (atau pengguna "
            "tidak yakin)."
        )},
    "external_monitor_connected": {"group": "kondisi", "description": "Laptop sedang tersambung ke monitor eksternal atau proyektor."},
    "cursor_visible": {"group": "kondisi", "description": "Di layar yang gelap terlihat panah kursor mouse yang bisa digerakkan."},
    "problem_started_after_update": {"group": "kondisi", "description": "Layar gelap mulai terjadi setelah Windows atau driver di-update."},
    "no_heavy_app_running": {"group": "kondisi", "description": "Tidak ada aplikasi berat (game, edit video, render) yang sedang berjalan."},
    "soft_surface": {"group": "kondisi", "description": "Laptop dipakai di atas kasur, bantal, sofa, atau pangkuan."},
    "vents_blocked": {"group": "kondisi", "description": "Ada benda yang menutupi lubang ventilasi laptop."},
    "fan_abnormal_noise": {"group": "kondisi", "description": (
            "Kipas berbunyi kasar (menggeram/berderak) atau tidak berputar sama sekali "
            "padahal laptop panas."
        )},
    "many_apps_running": {"group": "kondisi", "description": "Banyak aplikasi atau tab browser yang sedang terbuka."},
    "disk_space_low": {"group": "kondisi", "description": "Drive C hampir penuh."},
    "charge_stops_at_limit": {"group": "kondisi", "description": (
            "Baterai selalu berhenti mengisi di angka yang sama, misalnya sekitar 55–60% "
            "atau 80%."
        )},
    "persists_after_basic": {"group": "tahap", "description": "Masalah masih terjadi setelah pengguna mencoba rekomendasi tahap dasar."},
    "persists_after_advanced": {"group": "tahap", "description": "Masalah masih terjadi setelah pengguna mencoba rekomendasi tahap lanjutan."},
}


# ============================================================
# 3. DERIVED FACTS (fakta turunan)
# ------------------------------------------------------------
# Tidak pernah ditanyakan ke pengguna. Hanya muncul jika sebuah rule
# bertipe "derived" terpicu. Dipakai sebagai condition oleh rule lain.
# ============================================================
DERIVED_FACTS = {
    "charging_issue": (
        "Ada masalah pada jalur pengisian daya (pengisian lambat atau baterai tidak "
        "mengisi)."
    ),
    "cooling_check_needed": "Sistem pendinginan laptop perlu diperiksa.",
    "needs_hardware_check": "Langkah mandiri sudah habis; perlu diagnostik hardware atau service center.",
}


# ============================================================
# 4. RECOMMENDATIONS (fakta rekomendasi)
# ------------------------------------------------------------
# Selalu diawali "rec_". Dihasilkan oleh rule bertipe "recommendation".
# Teks yang ditampilkan ke pengguna ada di field "output" setiap rule,
# karena satu rekomendasi bisa dihasilkan lebih dari satu rule
# (contoh: rec_power_reset dari R03 dan R09 dengan teks berbeda).
#
# Catatan: rec_enter_safe_mode juga dipakai sebagai condition di R15
# (rantai R14 -> R15), sesuai final rule set.
# ============================================================
RECOMMENDATIONS = {
    "rec_connect_charger": "Charger belum terpasang",
    "rec_check_power_connection": "Periksa jalur daya",
    "rec_power_reset": "Lepas perangkat & power reset / Power reset untuk baterai tidak mengisi",
    "rec_check_charging_connection": "Periksa sambungan & port pengisian",
    "rec_use_designed_charger": "Gunakan charger & kabel yang dirancang untuk laptop",
    "rec_battery_diagnostic": "Diagnostik baterai",
    "rec_blank_screen_basic": "Langkah dasar layar gelap",
    "rec_check_external_monitor": "Periksa monitor eksternal",
    "rec_restart_explorer": "Restart Windows Explorer",
    "rec_enter_safe_mode": "Lepas perangkat & masuk Safe Mode",
    "rec_rollback_driver": "Rollback driver setelah update",
    "rec_check_task_manager_fan": "Periksa beban di Task Manager",
    "rec_move_to_hard_surface": "Pindah ke permukaan keras",
    "rec_clear_vents": "Bebaskan ventilasi",
    "rec_clean_vents_safely": "Bersihkan ventilasi secara aman",
    "rec_close_apps_restart": "Tutup aplikasi & restart",
    "rec_monitor_task_manager": "Pantau Task Manager",
    "rec_free_disk_space": "Kosongkan ruang penyimpanan",
    "rec_update_and_scan": "Update & malware scan",
    "rec_consult_support": "Kemungkinan batas perangkat keras",
    "rec_hardware_diagnostic_or_service": "Diagnostik hardware atau service center",
    "rec_check_charge_limit": "Batas pengisian daya (mode konservasi)",
}


# ============================================================
# 5. RULES (31 FINAL RULE)
# ------------------------------------------------------------
# id         : ID rule (R01–R31)
# name       : nama singkat rule
# conditions : daftar fakta yang HARUS ada semuanya (hubungan AND)
# then       : fakta baru yang ditambahkan jika semua conditions terpenuhi
# type       : "derived"        -> then adalah fakta turunan (tanpa output)
#              "recommendation" -> then adalah rekomendasi (ada output)
# output     : teks untuk pengguna (None untuk rule "derived")
# source     : daftar kode sumber (lihat SOURCES)
#
# Urutan di list ini TIDAK menentukan urutan eksekusi. Urutan dan prioritas
# akan diatur oleh inference engine pada tahap berikutnya.
# ============================================================
RULES = [
    # ----- Daya — laptop tidak menyala -----
    {
        "id": "R01",
        "name": "Charger belum terpasang",
        "conditions": ["no_power", "charger_not_connected"],
        "then": "rec_connect_charger",
        "type": "recommendation",
        "output": (
            "Hubungkan laptop ke charger bawaannya, colokkan charger ke stopkontak, lalu "
            "coba nyalakan kembali."
        ),
        "source": ["S14", "S2", "T1"],
    },
    {
        "id": "R02",
        "name": "Periksa jalur daya",
        "conditions": ["no_power", "charger_connected"],
        "then": "rec_check_power_connection",
        "type": "recommendation",
        "output": (
            "Periksa sambungan charger di tiga titik: kabel ke adaptor, adaptor ke "
            "stopkontak, dan konektor ke laptop. Colokkan langsung ke stopkontak dinding "
            "tanpa terminal/power strip, lalu pastikan stopkontaknya berfungsi dengan "
            "mencoba perangkat lain. Periksa kabel, adaptor, dan steker dari kerusakan "
            "fisik. Bila laptop terpasang di docking station, lepaskan dulu."
        ),
        "source": ["S14", "S5", "S6"],
    },
    {
        "id": "R03",
        "name": "Lepas perangkat & power reset",
        "conditions": ["no_power", "persists_after_basic"],
        "then": "rec_power_reset",
        "type": "recommendation",
        "output": (
            "Lakukan power reset: matikan laptop, cabut charger, lepaskan semua perangkat "
            "eksternal (USB, kartu memori, printer, hard disk eksternal, monitor), dan "
            "lepas baterai bila bisa dilepas. Tunggu sebentar atau tahan tombol power, "
            "sambungkan kembali charger saja, lalu nyalakan. Pasang kembali perangkat satu "
            "per satu. Durasinya berbeda antar merek (HP: tahan tombol power ±15 detik; "
            "Lenovo ThinkPad: tunggu 30 detik), jadi ikuti manual laptop Anda."
        ),
        "source": ["S14", "T3", "T1"],
    },
    {
        "id": "R04",
        "name": "Eskalasi: tetap tidak menyala",
        "conditions": ["no_power", "persists_after_advanced"],
        "then": "needs_hardware_check",
        "type": "derived",
        "output": None,
        "source": ["S8", "S14"],
    },
    # ----- Baterai & pengisian daya -----
    {
        "id": "R05",
        "name": "Klasifikasi: pengisian lambat",
        "conditions": ["charging_slow"],
        "then": "charging_issue",
        "type": "derived",
        "output": None,
        "source": ["S1", "S5"],
    },
    {
        "id": "R06",
        "name": "Klasifikasi: baterai tidak mengisi",
        "conditions": ["battery_not_charging"],
        "then": "charging_issue",
        "type": "derived",
        "output": None,
        "source": ["S7", "T2"],
    },
    {
        "id": "R07",
        "name": "Periksa sambungan & port pengisian",
        "conditions": ["charging_issue"],
        "then": "rec_check_charging_connection",
        "type": "recommendation",
        "output": (
            "Pastikan adaptor, kabel, dan stopkontak tersambung rapat; colokkan langsung ke "
            "stopkontak dinding, bukan ke terminal/power strip. Periksa kerusakan fisik "
            "pada kabel/adaptor dan coba stopkontak lain. Pastikan charger terpasang ke "
            "port pengisian daya laptop; ini penting bila laptop mengisi daya lewat USB-C "
            "dan punya lebih dari satu port."
        ),
        "source": ["S1", "S5", "S6", "S11"],
    },
    {
        "id": "R08",
        "name": "Gunakan charger & kabel yang dirancang untuk laptop",
        "conditions": ["charging_slow", "charger_or_cable_not_original"],
        "then": "rec_use_designed_charger",
        "type": "recommendation",
        "output": (
            "Gunakan charger dan kabel yang dirancang untuk laptop Anda (bawaan atau "
            "rekomendasi produsen), karena charger atau kabel lain mungkin tidak memberi "
            "daya yang cukup. Jika ragu, tanyakan charger yang sesuai kepada produsen "
            "laptop."
        ),
        "source": ["S1", "S6", "S11"],
    },
    {
        "id": "R09",
        "name": "Power reset untuk baterai tidak mengisi",
        "conditions": ["battery_not_charging", "persists_after_basic"],
        "then": "rec_power_reset",
        "type": "recommendation",
        "output": (
            "Lakukan hard reset/power reset: matikan laptop, cabut charger dan perangkat "
            "eksternal, tahan tombol power (HP: ±15 detik) atau tunggu sekitar 30 detik "
            "(Lenovo), lalu sambungkan charger kembali. Ikuti manual laptop Anda untuk "
            "langkah persisnya."
        ),
        "source": ["S7", "T3", "S11"],
    },
    {
        "id": "R10",
        "name": "Diagnostik baterai",
        "conditions": ["charging_issue", "persists_after_basic"],
        "then": "rec_battery_diagnostic",
        "type": "recommendation",
        "output": (
            "Jika masalah masih ada, periksa kondisi baterai dengan diagnostik bawaan "
            "produsen bila tersedia, misalnya HP Battery Check (khusus HP), MyASUS › System "
            "Diagnosis › Battery problems (khusus ASUS), atau Lenovo Vantage (khusus "
            "Lenovo). Lenovo juga menyebut pengecekan lewat Windows. Baterai memang menua "
            "seiring waktu dan mungkin perlu diganti. Jika hasil menunjukkan masalah, "
            "hubungi service center resmi."
        ),
        "source": ["S7", "S5", "S11"],
    },
    # ----- Layar gelap -----
    {
        "id": "R11",
        "name": "Langkah dasar layar gelap",
        "conditions": ["blank_screen"],
        "then": "rec_blank_screen_basic",
        "type": "recommendation",
        "output": (
            "Coba berurutan: pastikan baterai terisi atau charger terpasang; tekan Windows "
            "+ Ctrl + Shift + B untuk me-reset driver grafis (berhasil bila terdengar beep "
            "atau layar berkedip); tekan Windows + P, tekan P lagi lalu Enter untuk "
            "berganti mode tampilan; bila tetap gelap, tekan dan tahan tombol power 20 "
            "detik untuk restart paksa."
        ),
        "source": ["S2"],
    },
    {
        "id": "R12",
        "name": "Periksa monitor eksternal",
        "conditions": ["blank_screen", "external_monitor_connected"],
        "then": "rec_check_external_monitor",
        "type": "recommendation",
        "output": (
            "Pastikan monitor eksternal tersambung, terhubung ke listrik, dan dalam keadaan "
            "menyala."
        ),
        "source": ["S2"],
    },
    {
        "id": "R13",
        "name": "Restart Windows Explorer",
        "conditions": ["blank_screen", "cursor_visible"],
        "then": "rec_restart_explorer",
        "type": "recommendation",
        "output": (
            "Tekan Ctrl + Shift + Esc untuk membuka Task Manager, cari Windows Explorer, "
            "klik kanan lalu pilih Restart. Jika tidak ada di daftar, pilih File › Run new "
            "task, ketik explorer.exe, lalu tekan Enter."
        ),
        "source": ["S2"],
    },
    {
        "id": "R14",
        "name": "Lepas perangkat & masuk Safe Mode",
        "conditions": ["blank_screen", "persists_after_basic"],
        "then": "rec_enter_safe_mode",
        "type": "recommendation",
        "output": (
            "Lepaskan monitor eksternal dan perangkat lain. Jika layar masih gelap, masuk "
            "ke Safe Mode: matikan paksa laptop (tahan tombol power 10 detik) 2–3 kali "
            "hingga muncul Recovery, pilih Troubleshoot › Advanced options › Startup "
            "Settings › Restart, lalu tekan F5 (Safe Mode with Networking). Di Safe Mode, "
            "buka Device Manager › Display adapters dan pilih Update driver. Ini langkah "
            "lanjutan; minta bantuan bila tidak yakin."
        ),
        "source": ["S2"],
    },
    {
        "id": "R15",
        "name": "Rollback driver setelah update",
        "conditions": ["rec_enter_safe_mode", "problem_started_after_update"],
        "then": "rec_rollback_driver",
        "type": "recommendation",
        "output": (
            "Karena masalah muncul setelah update, di Device Manager pilih Roll back "
            "driver, bukan Update driver. Bila masalahnya baru terjadi, System Restore ke "
            "titik sebelum masalah juga bisa dicoba (Troubleshoot › Advanced options › "
            "System Restore)."
        ),
        "source": ["S2"],
    },
    {
        "id": "R16",
        "name": "Eskalasi: layar tetap gelap",
        "conditions": ["blank_screen", "persists_after_advanced"],
        "then": "needs_hardware_check",
        "type": "derived",
        "output": None,
        "source": ["S8"],
    },
    # ----- Panas & kipas -----
    {
        "id": "R17",
        "name": "Klasifikasi: laptop panas",
        "conditions": ["laptop_hot"],
        "then": "cooling_check_needed",
        "type": "derived",
        "output": None,
        "source": ["S4", "S10", "S13"],
    },
    {
        "id": "R18",
        "name": "Klasifikasi: kipas kencang tanpa beban berat",
        "conditions": ["fan_loud", "no_heavy_app_running"],
        "then": "cooling_check_needed",
        "type": "derived",
        "output": None,
        "source": ["S12", "S9", "S4"],
    },
    {
        "id": "R19",
        "name": "Periksa beban di Task Manager",
        "conditions": ["fan_loud"],
        "then": "rec_check_task_manager_fan",
        "type": "recommendation",
        "output": (
            "Kipas lebih kencang saat menjalankan game, edit video, atau pemrosesan berat "
            "adalah hal normal, begitu juga kipas yang keras 5–20 detik saat laptop baru "
            "dinyalakan. Buka Task Manager (Ctrl + Shift + Esc) dan urutkan kolom CPU untuk "
            "melihat aplikasi yang paling berat. Tutup aplikasi yang tidak sedang dipakai "
            "dari jendela aplikasinya sendiri; menutup lewat Task Manager dapat menimbulkan "
            "masalah. Jangan mengakhiri proses yang tidak Anda kenali."
        ),
        "source": ["S4", "S12", "S9"],
    },
    {
        "id": "R20",
        "name": "Pindah ke permukaan keras",
        "conditions": ["cooling_check_needed", "soft_surface"],
        "then": "rec_move_to_hard_surface",
        "type": "recommendation",
        "output": (
            "Letakkan laptop di permukaan yang keras dan rata seperti meja. Hindari kasur, "
            "bantal, sofa, atau pangkuan karena dapat menghalangi aliran udara. Cooling pad "
            "atau stand juga dapat membantu."
        ),
        "source": ["S4", "S9", "S10"],
    },
    {
        "id": "R21",
        "name": "Bebaskan ventilasi",
        "conditions": ["cooling_check_needed", "vents_blocked"],
        "then": "rec_clear_vents",
        "type": "recommendation",
        "output": (
            "Jauhkan benda yang menutupi lubang ventilasi (biasanya di bawah dan di sisi "
            "laptop) dan beri ruang bebas di sekitar setiap lubang; HP menyarankan "
            "sedikitnya 15 cm."
        ),
        "source": ["S4", "S10", "S9"],
    },
    {
        "id": "R22",
        "name": "Bersihkan ventilasi secara aman",
        "conditions": ["cooling_check_needed", "persists_after_basic"],
        "then": "rec_clean_vents_safely",
        "type": "recommendation",
        "output": (
            "Matikan laptop dan cabut charger, lalu semprotkan debu dari lubang ventilasi "
            "bagian luar dengan kaleng udara bertekanan (compressed air) dari jarak "
            "tertentu, tanpa membongkar laptop. Jangan memakai kompresor udara. Jika debu "
            "menumpuk di bagian dalam, bawa ke service center resmi. Setelah itu, perbarui "
            "Windows, driver, dan BIOS hanya melalui aplikasi atau situs resmi produsen "
            "laptop, dan baca peringatannya dengan teliti karena BIOS yang salah dapat "
            "membuat laptop tidak berfungsi."
        ),
        "source": ["S4", "S10", "S12", "S9"],
    },
    {
        "id": "R23",
        "name": "Eskalasi: tetap panas",
        "conditions": ["cooling_check_needed", "persists_after_advanced"],
        "then": "needs_hardware_check",
        "type": "derived",
        "output": None,
        "source": ["S12", "S10", "S4"],
    },
    {
        "id": "R24",
        "name": "Kipas berbunyi abnormal",
        "conditions": ["fan_abnormal_noise"],
        "then": "needs_hardware_check",
        "type": "derived",
        "output": None,
        "source": ["S10"],
    },
    # ----- Performa lambat -----
    {
        "id": "R25",
        "name": "Tutup aplikasi & restart",
        "conditions": ["laptop_slow", "many_apps_running"],
        "then": "rec_close_apps_restart",
        "type": "recommendation",
        "output": (
            "Tutup aplikasi atau tab browser yang tidak diperlukan. Jika performa tidak "
            "membaik, restart laptop (Start › Power › Restart), lalu buka hanya aplikasi "
            "yang dibutuhkan."
        ),
        "source": ["S3", "S13"],
    },
    {
        "id": "R26",
        "name": "Pantau Task Manager",
        "conditions": ["laptop_slow"],
        "then": "rec_monitor_task_manager",
        "type": "recommendation",
        "output": (
            "Buka Task Manager (Ctrl + Shift + Esc). Lihat tab Processes dan Performance "
            "untuk mengetahui apakah CPU, memori, atau disk yang tinggi, dan aplikasi mana "
            "penyebabnya. Tutup aplikasi yang tidak Anda pakai, sebaiknya dari jendela "
            "aplikasinya sendiri."
        ),
        "source": ["S3", "S12"],
    },
    {
        "id": "R27",
        "name": "Kosongkan ruang penyimpanan",
        "conditions": ["laptop_slow", "disk_space_low"],
        "then": "rec_free_disk_space",
        "type": "recommendation",
        "output": (
            "Kosongkan ruang penyimpanan: jalankan Storage Sense atau hapus Temporary files "
            "(Settings › System › Storage), gunakan Disk Cleanup, dan uninstall aplikasi "
            "yang tidak dipakai (Settings › Apps › Installed apps)."
        ),
        "source": ["S3", "S13"],
    },
    {
        "id": "R28",
        "name": "Update & malware scan",
        "conditions": ["laptop_slow", "persists_after_basic"],
        "then": "rec_update_and_scan",
        "type": "recommendation",
        "output": (
            "Periksa pembaruan di Settings › Windows Update › Check for updates, termasuk "
            "Optional updates untuk driver. Lalu jalankan Quick scan di Windows Security › "
            "Virus & threat protection."
        ),
        "source": ["S3", "S13"],
    },
    {
        "id": "R29",
        "name": "Kemungkinan batas perangkat keras",
        "conditions": ["laptop_slow", "persists_after_advanced"],
        "then": "rec_consult_support",
        "type": "recommendation",
        "output": (
            "Jika semua langkah sudah dicoba dan laptop tetap lambat, perangkat keras yang "
            "sudah lama bisa menjadi batasnya. Menurut Microsoft, PC lama mungkin tidak "
            "banyak membaik dengan langkah-langkah ini. Pertimbangkan berkonsultasi dengan "
            "teknisi atau layanan dukungan resmi."
        ),
        "source": ["S3", "S13"],
    },
    # ----- Eskalasi bersama -----
    {
        "id": "R30",
        "name": "Diagnostik hardware atau service center",
        "conditions": ["needs_hardware_check"],
        "then": "rec_hardware_diagnostic_or_service",
        "type": "recommendation",
        "output": (
            "Kondisi ini perlu pemeriksaan perangkat keras. Jalankan diagnostik hardware bawaan "
            "produsen bila tersedia, misalnya HP PC Hardware Diagnostics (khusus laptop HP) "
            "atau MyASUS › System Diagnosis (khusus laptop ASUS), atau bawa laptop ke "
            "service center resmi. Sistem ini tidak dapat memastikan komponen mana yang "
            "bermasalah."
        ),
        "source": ["S8", "S4", "S10"],
    },
    # ----- Tambahan versi 3 (domain: Baterai & pengisian daya) -----
    {
        "id": "R31",
        "name": "Batas pengisian daya (mode konservasi)",
        "conditions": ["battery_not_charging", "charge_stops_at_limit"],
        "then": "rec_check_charge_limit",
        "type": "recommendation",
        "output": (
            "Baterai yang selalu berhenti mengisi di sekitar 55–60% atau 80% biasanya bukan "
            "kerusakan. Kemungkinan besar itu fitur pembatas pengisian untuk memperpanjang "
            "umur baterai. Periksa pengaturannya di aplikasi bawaan produsen, misalnya "
            "Battery Care Mode di MyASUS (ASUS) atau conservation mode/battery charge "
            "threshold (Lenovo). Nonaktifkan bila Anda butuh pengisian penuh. Jika ini "
            "penyebabnya, langkah reset tidak diperlukan."
        ),
        "source": ["S6", "S11"],
    },
]


# ============================================================
# 6. VALIDASI STRUKTUR DATA
# ------------------------------------------------------------
# Fungsi di bawah hanya MEMERIKSA apakah data di atas konsisten.
# Fungsi ini tidak mencocokkan fakta pengguna dengan rule dan tidak
# menghasilkan rekomendasi apa pun (bukan inference engine).
# ============================================================
RULE_TYPES = ("derived", "recommendation")
REQUIRED_FIELDS = ("id", "name", "conditions", "then", "type", "output", "source")
EXPECTED_RULE_COUNT = 31
FACT_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")  # snake_case


def validate_knowledge_base():
    """Kembalikan daftar pesan kesalahan. List kosong berarti data valid."""
    errors = []

    # --- a. jumlah rule dan ID ---
    ids = [rule.get("id") for rule in RULES]
    expected_ids = ["R%02d" % n for n in range(1, EXPECTED_RULE_COUNT + 1)]
    if len(RULES) != EXPECTED_RULE_COUNT:
        errors.append(f"Jumlah rule {len(RULES)}, seharusnya {EXPECTED_RULE_COUNT}.")
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        errors.append(f"ID rule ganda: {duplicates}")
    missing = [i for i in expected_ids if i not in ids]
    if missing:
        errors.append(f"ID rule hilang: {missing}")
    unexpected = [i for i in ids if i not in expected_ids]
    if unexpected:
        errors.append(f"ID rule di luar R01–R31: {unexpected}")

    # --- b. satu nama fakta hanya boleh berada di satu kategori ---
    categories = {
        "INITIAL_FACTS": set(INITIAL_FACTS),
        "DERIVED_FACTS": set(DERIVED_FACTS),
        "RECOMMENDATIONS": set(RECOMMENDATIONS),
    }
    names = list(categories)
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            overlap = categories[names[a]] & categories[names[b]]
            if overlap:
                errors.append(f"Fakta {sorted(overlap)} ada di {names[a]} dan {names[b]}.")
    all_facts = set().union(*categories.values())

    # --- c. format nama fakta ---
    for fact in sorted(all_facts):
        if not FACT_NAME_PATTERN.match(fact):
            errors.append(f"Nama fakta tidak snake_case: {fact!r}")
    for fact in RECOMMENDATIONS:
        if not fact.startswith("rec_"):
            errors.append(f"Rekomendasi harus diawali 'rec_': {fact!r}")
    for fact in set(INITIAL_FACTS) | set(DERIVED_FACTS):
        if fact.startswith("rec_"):
            errors.append(f"Awalan 'rec_' hanya untuk rekomendasi: {fact!r}")

    # --- d. isi setiap rule ---
    for rule in RULES:
        rid = rule.get("id", "?")
        for field in REQUIRED_FIELDS:
            if field not in rule:
                errors.append(f"{rid}: field '{field}' tidak ada.")
        if any(field not in rule for field in REQUIRED_FIELDS):
            continue

        conditions = rule["conditions"]
        if not isinstance(conditions, list) or not conditions:
            errors.append(f"{rid}: conditions harus list yang tidak kosong.")
        if len(conditions) != len(set(conditions)):
            errors.append(f"{rid}: ada condition yang ditulis dua kali.")
        for cond in conditions:
            if cond not in all_facts:
                errors.append(f"{rid}: condition {cond!r} tidak terdaftar sebagai fakta.")
        if rule["then"] in conditions:
            errors.append(f"{rid}: then juga muncul di conditions-nya sendiri.")

        if rule["type"] not in RULE_TYPES:
            errors.append(f"{rid}: type {rule['type']!r} tidak dikenal.")
        elif rule["type"] == "derived":
            if rule["then"] not in DERIVED_FACTS:
                errors.append(f"{rid}: rule derived harus menghasilkan fakta di DERIVED_FACTS.")
            if rule["output"] is not None:
                errors.append(f"{rid}: rule derived tidak boleh punya output.")
        else:
            if rule["then"] not in RECOMMENDATIONS:
                errors.append(f"{rid}: rule recommendation harus menghasilkan fakta di RECOMMENDATIONS.")
            if not isinstance(rule["output"], str) or not rule["output"].strip():
                errors.append(f"{rid}: rule recommendation harus punya teks output.")

        if not rule["source"]:
            errors.append(f"{rid}: source kosong.")
        for code in rule["source"]:
            if code not in SOURCES:
                errors.append(f"{rid}: kode sumber {code!r} tidak ada di SOURCES.")

    # --- e. setiap fakta yang didaftarkan benar-benar dipakai ---
    used_conditions = {c for rule in RULES for c in rule.get("conditions", [])}
    produced = {rule.get("then") for rule in RULES}
    for fact in INITIAL_FACTS:
        if fact not in used_conditions:
            errors.append(f"Fakta awal {fact!r} tidak dipakai rule mana pun.")
    for fact in DERIVED_FACTS:
        if fact not in produced:
            errors.append(f"Fakta turunan {fact!r} tidak dihasilkan rule mana pun.")
        if fact not in used_conditions:
            errors.append(f"Fakta turunan {fact!r} tidak dipakai sebagai condition.")
    for fact in RECOMMENDATIONS:
        if fact not in produced:
            errors.append(f"Rekomendasi {fact!r} tidak dihasilkan rule mana pun.")
    for code in SOURCES:
        if not any(code in rule.get("source", []) for rule in RULES):
            errors.append(f"Sumber {code} tidak dirujuk rule mana pun.")

    return errors


def find_similar_fact_names(threshold=0.85):
    """
    Bantu menemukan kemungkinan typo/sinonim, misalnya laptop_hot vs laptop_is_hot.
    Hasilnya berupa PERINGATAN untuk diperiksa manusia, bukan kesalahan otomatis.
    """
    facts = sorted(set(INITIAL_FACTS) | set(DERIVED_FACTS) | set(RECOMMENDATIONS))
    pairs = []
    for i in range(len(facts)):
        for j in range(i + 1, len(facts)):
            ratio = SequenceMatcher(None, facts[i], facts[j]).ratio()
            if ratio >= threshold:
                pairs.append((facts[i], facts[j], round(ratio, 2)))
    return pairs


if __name__ == "__main__":
    problems = validate_knowledge_base()
    print(f"Rule           : {len(RULES)}")
    print(f"  derived      : {sum(r['type'] == 'derived' for r in RULES)}")
    print(f"  recommendation: {sum(r['type'] == 'recommendation' for r in RULES)}")
    print(f"Fakta awal     : {len(INITIAL_FACTS)}")
    print(f"Fakta turunan  : {len(DERIVED_FACTS)}")
    print(f"Rekomendasi    : {len(RECOMMENDATIONS)}")
    print(f"Sumber         : {len(SOURCES)}")
    print()
    if problems:
        print(f"VALIDASI GAGAL ({len(problems)} masalah):")
        for p in problems:
            print(" -", p)
    else:
        print("VALIDASI BERHASIL: struktur knowledge base konsisten.")
    similar = find_similar_fact_names()
    if similar:
        print("\nNama fakta yang mirip (periksa manual, bisa saja memang disengaja):")
        for a, b, ratio in similar:
            print(f" - {a}  ~  {b}  ({ratio})")
