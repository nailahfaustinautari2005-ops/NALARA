# Tabel verifikasi knowledge_base.py

Dibuat otomatis dari `knowledge_base.py`, jadi isinya pasti sama dengan kode. Sesuai dokumen audit versi 4 (perubahan dari v3: hanya teks output R30).

## A. Daftar fakta

| Kategori | Nama fakta | Keterangan | Sumber/asal |
|---|---|---|---|
| Initial Fact (gejala) | `no_power` | Laptop sama sekali tidak menyala: tidak ada lampu, suara kipas, atau gambar saat tombol power ditekan. | user input · dipakai di R01, R02, R03, R04 |
| Initial Fact (gejala) | `blank_screen` | Laptop tampak menyala (ada lampu atau suara kipas), tetapi layarnya hitam/kosong. | user input · dipakai di R11, R12, R13, R14, R16 |
| Initial Fact (gejala) | `charging_slow` | Saat charger terpasang, Windows menampilkan 'charging slowly' atau persentase baterai justru turun. | user input · dipakai di R05, R08 |
| Initial Fact (gejala) | `battery_not_charging` | Charger terpasang, tetapi persentase baterai tidak bertambah atau selalu berhenti di angka tertentu. | user input · dipakai di R06, R09, R31 |
| Initial Fact (gejala) | `laptop_hot` | Badan laptop terasa jauh lebih panas dari biasanya (bisa keluhan utama atau jawaban di alur lambat/kipas). | user input · dipakai di R17 |
| Initial Fact (gejala) | `fan_loud` | Kipas terdengar kencang atau berputar terus-menerus. | user input · dipakai di R18, R19 |
| Initial Fact (gejala) | `laptop_slow` | Laptop lambat atau sering tersendat. | user input · dipakai di R25, R26, R27, R28, R29 |
| Initial Fact (kondisi) | `charger_not_connected` | Charger tidak terpasang ke laptop dan/atau ke stopkontak. | user input · dipakai di R01 |
| Initial Fact (kondisi) | `charger_connected` | Charger terpasang ke laptop dan ke stopkontak. | user input · dipakai di R02 |
| Initial Fact (kondisi) | `charger_or_cable_not_original` | Charger atau kabel bukan bawaan/rekomendasi produsen laptop (atau pengguna tidak yakin). | user input · dipakai di R08 |
| Initial Fact (kondisi) | `external_monitor_connected` | Laptop sedang tersambung ke monitor eksternal atau proyektor. | user input · dipakai di R12 |
| Initial Fact (kondisi) | `cursor_visible` | Di layar yang gelap terlihat panah kursor mouse yang bisa digerakkan. | user input · dipakai di R13 |
| Initial Fact (kondisi) | `problem_started_after_update` | Layar gelap mulai terjadi setelah Windows atau driver di-update. | user input · dipakai di R15 |
| Initial Fact (kondisi) | `no_heavy_app_running` | Tidak ada aplikasi berat (game, edit video, render) yang sedang berjalan. | user input · dipakai di R18 |
| Initial Fact (kondisi) | `soft_surface` | Laptop dipakai di atas kasur, bantal, sofa, atau pangkuan. | user input · dipakai di R20 |
| Initial Fact (kondisi) | `vents_blocked` | Ada benda yang menutupi lubang ventilasi laptop. | user input · dipakai di R21 |
| Initial Fact (kondisi) | `fan_abnormal_noise` | Kipas berbunyi kasar (menggeram/berderak) atau tidak berputar sama sekali padahal laptop panas. | user input · dipakai di R24 |
| Initial Fact (kondisi) | `many_apps_running` | Banyak aplikasi atau tab browser yang sedang terbuka. | user input · dipakai di R25 |
| Initial Fact (kondisi) | `disk_space_low` | Drive C hampir penuh. | user input · dipakai di R27 |
| Initial Fact (kondisi) | `charge_stops_at_limit` | Baterai selalu berhenti mengisi di angka yang sama, misalnya sekitar 55–60% atau 80%. | user input · dipakai di R31 |
| Initial Fact (tahap) | `persists_after_basic` | Masalah masih terjadi setelah pengguna mencoba rekomendasi tahap dasar. | user input · dipakai di R03, R09, R10, R14, R22, R28 |
| Initial Fact (tahap) | `persists_after_advanced` | Masalah masih terjadi setelah pengguna mencoba rekomendasi tahap lanjutan. | user input · dipakai di R04, R16, R23, R29 |
| Derived Fact | `charging_issue` | Ada masalah pada jalur pengisian daya (pengisian lambat atau baterai tidak mengisi). | rule R05 / R06 · dipakai di R07, R10 |
| Derived Fact | `cooling_check_needed` | Sistem pendinginan laptop perlu diperiksa. | rule R17 / R18 · dipakai di R20, R21, R22, R23 |
| Derived Fact | `needs_hardware_check` | Langkah mandiri sudah habis; perlu diagnostik hardware atau service center. | rule R04 / R16 / R23 / R24 · dipakai di R30 |
| Recommendation | `rec_connect_charger` | Charger belum terpasang | rule R01 |
| Recommendation | `rec_check_power_connection` | Periksa jalur daya | rule R02 |
| Recommendation | `rec_power_reset` | Lepas perangkat & power reset / Power reset untuk baterai tidak mengisi | rule R03 / R09 |
| Recommendation | `rec_check_charging_connection` | Periksa sambungan & port pengisian | rule R07 |
| Recommendation | `rec_use_designed_charger` | Gunakan charger & kabel yang dirancang untuk laptop | rule R08 |
| Recommendation | `rec_battery_diagnostic` | Diagnostik baterai | rule R10 |
| Recommendation | `rec_blank_screen_basic` | Langkah dasar layar gelap | rule R11 |
| Recommendation | `rec_check_external_monitor` | Periksa monitor eksternal | rule R12 |
| Recommendation | `rec_restart_explorer` | Restart Windows Explorer | rule R13 |
| Recommendation | `rec_enter_safe_mode` | Lepas perangkat & masuk Safe Mode | rule R14 · juga condition di R15 |
| Recommendation | `rec_rollback_driver` | Rollback driver setelah update | rule R15 |
| Recommendation | `rec_check_task_manager_fan` | Periksa beban di Task Manager | rule R19 |
| Recommendation | `rec_move_to_hard_surface` | Pindah ke permukaan keras | rule R20 |
| Recommendation | `rec_clear_vents` | Bebaskan ventilasi | rule R21 |
| Recommendation | `rec_clean_vents_safely` | Bersihkan ventilasi secara aman | rule R22 |
| Recommendation | `rec_close_apps_restart` | Tutup aplikasi & restart | rule R25 |
| Recommendation | `rec_monitor_task_manager` | Pantau Task Manager | rule R26 |
| Recommendation | `rec_free_disk_space` | Kosongkan ruang penyimpanan | rule R27 |
| Recommendation | `rec_update_and_scan` | Update & malware scan | rule R28 |
| Recommendation | `rec_consult_support` | Kemungkinan batas perangkat keras | rule R29 |
| Recommendation | `rec_hardware_diagnostic_or_service` | Diagnostik hardware atau service center | rule R30 |
| Recommendation | `rec_check_charge_limit` | Batas pengisian daya (mode konservasi) | rule R31 |

## B. Mapping rule

| Rule ID | Conditions | THEN | Type | Output | Source |
|---|---|---|---|---|---|
| R01 | `no_power` ∧ `charger_not_connected` | `rec_connect_charger` | recommendation | Hubungkan laptop ke charger bawaannya, colokkan charger ke stopkontak, lalu coba nyalakan kembali. | S14, S2, T1 |
| R02 | `no_power` ∧ `charger_connected` | `rec_check_power_connection` | recommendation | Periksa sambungan charger di tiga titik: kabel ke adaptor, adaptor ke stopkontak, dan konektor ke laptop. Colokkan langsung ke stopkontak dinding tanpa terminal/power strip, lalu pastikan stopkontaknya berfungsi dengan mencoba perangkat lain. Periksa kabel, adaptor, dan steker dari kerusakan fisik. Bila laptop terpasang di docking station, lepaskan dulu. | S14, S5, S6 |
| R03 | `no_power` ∧ `persists_after_basic` | `rec_power_reset` | recommendation | Lakukan power reset: matikan laptop, cabut charger, lepaskan semua perangkat eksternal (USB, kartu memori, printer, hard disk eksternal, monitor), dan lepas baterai bila bisa dilepas. Tunggu sebentar atau tahan tombol power, sambungkan kembali charger saja, lalu nyalakan. Pasang kembali perangkat satu per satu. Durasinya berbeda antar merek (HP: tahan tombol power ±15 detik; Lenovo ThinkPad: tunggu 30 detik), jadi ikuti manual laptop Anda. | S14, T3, T1 |
| R04 | `no_power` ∧ `persists_after_advanced` | `needs_hardware_check` | derived | — (fakta turunan, tidak ada output) | S8, S14 |
| R05 | `charging_slow` | `charging_issue` | derived | — (fakta turunan, tidak ada output) | S1, S5 |
| R06 | `battery_not_charging` | `charging_issue` | derived | — (fakta turunan, tidak ada output) | S7, T2 |
| R07 | `charging_issue` | `rec_check_charging_connection` | recommendation | Pastikan adaptor, kabel, dan stopkontak tersambung rapat; colokkan langsung ke stopkontak dinding, bukan ke terminal/power strip. Periksa kerusakan fisik pada kabel/adaptor dan coba stopkontak lain. Pastikan charger terpasang ke port pengisian daya laptop; ini penting bila laptop mengisi daya lewat USB-C dan punya lebih dari satu port. | S1, S5, S6, S11 |
| R08 | `charging_slow` ∧ `charger_or_cable_not_original` | `rec_use_designed_charger` | recommendation | Gunakan charger dan kabel yang dirancang untuk laptop Anda (bawaan atau rekomendasi produsen), karena charger atau kabel lain mungkin tidak memberi daya yang cukup. Jika ragu, tanyakan charger yang sesuai kepada produsen laptop. | S1, S6, S11 |
| R09 | `battery_not_charging` ∧ `persists_after_basic` | `rec_power_reset` | recommendation | Lakukan hard reset/power reset: matikan laptop, cabut charger dan perangkat eksternal, tahan tombol power (HP: ±15 detik) atau tunggu sekitar 30 detik (Lenovo), lalu sambungkan charger kembali. Ikuti manual laptop Anda untuk langkah persisnya. | S7, T3, S11 |
| R10 | `charging_issue` ∧ `persists_after_basic` | `rec_battery_diagnostic` | recommendation | Jika masalah masih ada, periksa kondisi baterai dengan diagnostik bawaan produsen bila tersedia, misalnya HP Battery Check (khusus HP), MyASUS › System Diagnosis › Battery problems (khusus ASUS), atau Lenovo Vantage (khusus Lenovo). Lenovo juga menyebut pengecekan lewat Windows. Baterai memang menua seiring waktu dan mungkin perlu diganti. Jika hasil menunjukkan masalah, hubungi service center resmi. | S7, S5, S11 |
| R11 | `blank_screen` | `rec_blank_screen_basic` | recommendation | Coba berurutan: pastikan baterai terisi atau charger terpasang; tekan Windows + Ctrl + Shift + B untuk me-reset driver grafis (berhasil bila terdengar beep atau layar berkedip); tekan Windows + P, tekan P lagi lalu Enter untuk berganti mode tampilan; bila tetap gelap, tekan dan tahan tombol power 20 detik untuk restart paksa. | S2 |
| R12 | `blank_screen` ∧ `external_monitor_connected` | `rec_check_external_monitor` | recommendation | Pastikan monitor eksternal tersambung, terhubung ke listrik, dan dalam keadaan menyala. | S2 |
| R13 | `blank_screen` ∧ `cursor_visible` | `rec_restart_explorer` | recommendation | Tekan Ctrl + Shift + Esc untuk membuka Task Manager, cari Windows Explorer, klik kanan lalu pilih Restart. Jika tidak ada di daftar, pilih File › Run new task, ketik explorer.exe, lalu tekan Enter. | S2 |
| R14 | `blank_screen` ∧ `persists_after_basic` | `rec_enter_safe_mode` | recommendation | Lepaskan monitor eksternal dan perangkat lain. Jika layar masih gelap, masuk ke Safe Mode: matikan paksa laptop (tahan tombol power 10 detik) 2–3 kali hingga muncul Recovery, pilih Troubleshoot › Advanced options › Startup Settings › Restart, lalu tekan F5 (Safe Mode with Networking). Di Safe Mode, buka Device Manager › Display adapters dan pilih Update driver. Ini langkah lanjutan; minta bantuan bila tidak yakin. | S2 |
| R15 | `rec_enter_safe_mode` ∧ `problem_started_after_update` | `rec_rollback_driver` | recommendation | Karena masalah muncul setelah update, di Device Manager pilih Roll back driver, bukan Update driver. Bila masalahnya baru terjadi, System Restore ke titik sebelum masalah juga bisa dicoba (Troubleshoot › Advanced options › System Restore). | S2 |
| R16 | `blank_screen` ∧ `persists_after_advanced` | `needs_hardware_check` | derived | — (fakta turunan, tidak ada output) | S8 |
| R17 | `laptop_hot` | `cooling_check_needed` | derived | — (fakta turunan, tidak ada output) | S4, S10, S13 |
| R18 | `fan_loud` ∧ `no_heavy_app_running` | `cooling_check_needed` | derived | — (fakta turunan, tidak ada output) | S12, S9, S4 |
| R19 | `fan_loud` | `rec_check_task_manager_fan` | recommendation | Kipas lebih kencang saat menjalankan game, edit video, atau pemrosesan berat adalah hal normal, begitu juga kipas yang keras 5–20 detik saat laptop baru dinyalakan. Buka Task Manager (Ctrl + Shift + Esc) dan urutkan kolom CPU untuk melihat aplikasi yang paling berat. Tutup aplikasi yang tidak sedang dipakai dari jendela aplikasinya sendiri; menutup lewat Task Manager dapat menimbulkan masalah. Jangan mengakhiri proses yang tidak Anda kenali. | S4, S12, S9 |
| R20 | `cooling_check_needed` ∧ `soft_surface` | `rec_move_to_hard_surface` | recommendation | Letakkan laptop di permukaan yang keras dan rata seperti meja. Hindari kasur, bantal, sofa, atau pangkuan karena dapat menghalangi aliran udara. Cooling pad atau stand juga dapat membantu. | S4, S9, S10 |
| R21 | `cooling_check_needed` ∧ `vents_blocked` | `rec_clear_vents` | recommendation | Jauhkan benda yang menutupi lubang ventilasi (biasanya di bawah dan di sisi laptop) dan beri ruang bebas di sekitar setiap lubang; HP menyarankan sedikitnya 15 cm. | S4, S10, S9 |
| R22 | `cooling_check_needed` ∧ `persists_after_basic` | `rec_clean_vents_safely` | recommendation | Matikan laptop dan cabut charger, lalu semprotkan debu dari lubang ventilasi bagian luar dengan kaleng udara bertekanan (compressed air) dari jarak tertentu, tanpa membongkar laptop. Jangan memakai kompresor udara. Jika debu menumpuk di bagian dalam, bawa ke service center resmi. Setelah itu, perbarui Windows, driver, dan BIOS hanya melalui aplikasi atau situs resmi produsen laptop, dan baca peringatannya dengan teliti karena BIOS yang salah dapat membuat laptop tidak berfungsi. | S4, S10, S12, S9 |
| R23 | `cooling_check_needed` ∧ `persists_after_advanced` | `needs_hardware_check` | derived | — (fakta turunan, tidak ada output) | S12, S10, S4 |
| R24 | `fan_abnormal_noise` | `needs_hardware_check` | derived | — (fakta turunan, tidak ada output) | S10 |
| R25 | `laptop_slow` ∧ `many_apps_running` | `rec_close_apps_restart` | recommendation | Tutup aplikasi atau tab browser yang tidak diperlukan. Jika performa tidak membaik, restart laptop (Start › Power › Restart), lalu buka hanya aplikasi yang dibutuhkan. | S3, S13 |
| R26 | `laptop_slow` | `rec_monitor_task_manager` | recommendation | Buka Task Manager (Ctrl + Shift + Esc). Lihat tab Processes dan Performance untuk mengetahui apakah CPU, memori, atau disk yang tinggi, dan aplikasi mana penyebabnya. Tutup aplikasi yang tidak Anda pakai, sebaiknya dari jendela aplikasinya sendiri. | S3, S12 |
| R27 | `laptop_slow` ∧ `disk_space_low` | `rec_free_disk_space` | recommendation | Kosongkan ruang penyimpanan: jalankan Storage Sense atau hapus Temporary files (Settings › System › Storage), gunakan Disk Cleanup, dan uninstall aplikasi yang tidak dipakai (Settings › Apps › Installed apps). | S3, S13 |
| R28 | `laptop_slow` ∧ `persists_after_basic` | `rec_update_and_scan` | recommendation | Periksa pembaruan di Settings › Windows Update › Check for updates, termasuk Optional updates untuk driver. Lalu jalankan Quick scan di Windows Security › Virus & threat protection. | S3, S13 |
| R29 | `laptop_slow` ∧ `persists_after_advanced` | `rec_consult_support` | recommendation | Jika semua langkah sudah dicoba dan laptop tetap lambat, perangkat keras yang sudah lama bisa menjadi batasnya. Menurut Microsoft, PC lama mungkin tidak banyak membaik dengan langkah-langkah ini. Pertimbangkan berkonsultasi dengan teknisi atau layanan dukungan resmi. | S3, S13 |
| R30 | `needs_hardware_check` | `rec_hardware_diagnostic_or_service` | recommendation | Kondisi ini perlu pemeriksaan perangkat keras. Jalankan diagnostik hardware bawaan produsen bila tersedia, misalnya HP PC Hardware Diagnostics (khusus laptop HP) atau MyASUS › System Diagnosis (khusus laptop ASUS), atau bawa laptop ke service center resmi. Sistem ini tidak dapat memastikan komponen mana yang bermasalah. | S8, S4, S10 |
| R31 | `battery_not_charging` ∧ `charge_stops_at_limit` | `rec_check_charge_limit` | recommendation | Baterai yang selalu berhenti mengisi di sekitar 55–60% atau 80% biasanya bukan kerusakan. Kemungkinan besar itu fitur pembatas pengisian untuk memperpanjang umur baterai. Periksa pengaturannya di aplikasi bawaan produsen, misalnya Battery Care Mode di MyASUS (ASUS) atau conservation mode/battery charge threshold (Lenovo). Nonaktifkan bila Anda butuh pengisian penuh. Jika ini penyebabnya, langkah reset tidak diperlukan. | S6, S11 |

## C. Sumber

| Kode | Vendor | Judul | Jenis | URL |
|---|---|---|---|---|
| S1 | Microsoft | PC is charging slowly or discharging while it’s plugged in | utama | https://support.microsoft.com/en-us/windows/experience/power-battery/pc-is-charging-slowly-or-discharging-while-it-s-plugged-in |
| S2 | Microsoft | Troubleshooting blank screens in Windows | utama | https://support.microsoft.com/en-us/windows/hardware/display-graphics/troubleshooting-blank-screens-in-windows |
| S3 | Microsoft | Tips to improve PC performance in Windows | utama | https://support.microsoft.com/en-us/windows/experience/performance-optimization/tips-to-improve-pc-performance-in-windows |
| S4 | ASUS | [Windows 11/10] Troubleshooting - Overheating and Fan issues (FAQ 1015064) | utama | https://www.asus.com/support/faq/1015064/ |
| S5 | ASUS | Troubleshooting - Slow Charging / Battery Draining while Plugged in (FAQ 1043611) | utama | https://www.asus.com/support/faq/1043611/ |
| S6 | ASUS | Battery and Power Adapter (Charger) Specifications and Recommended Usage (FAQ 1015066) | utama | https://www.asus.com/support/faq/1015066/ |
| S7 | HP | HP Battery Check: Fix laptop battery not charging | utama | https://support.hp.com/us-en/help/computer/battery-adapter-issues |
| S8 | HP | How to Fix HP Computer and Laptop Power On and Boot Up Problems | utama | https://support.hp.com/bg-en/help/computer/power-boot-issues |
| S9 | HP | HP Notebook PCs - Fan is noisy and spins constantly (Windows) | utama | https://support.hp.com/us-en/document/ish_3045299-2819686-16 |
| S10 | HP | Reduce heat inside the laptop to prevent overheating in Windows | utama | https://support.hp.com/si-en/document/ish_3894569-1692683-16 |
| S11 | Lenovo | Troubleshooting battery issues - PC (HT080185) | utama | https://support.lenovo.com/sg/en/solutions/ht080185-troubleshooting-battery-issues-thinkpad |
| S12 | Lenovo | Fan runs at a higher than expected speed - Windows (HT077046) | utama | https://pcsupport.lenovo.com/us/en/solutions/ht077046 |
| S13 | Lenovo | Freezing or slow performance issues - Windows 10, 11 (HT510168) | utama | https://pcsupport.lenovo.com/us/en/solutions/ht510168 |
| S14 | Lenovo | No power or system does not run on battery power - ThinkPad (HT080218) | utama | https://pcsupport.lenovo.com/us/en/solutions/ht080218 |
| T1 | ASUS | Troubleshooting - Device Boot Failure or No Display After Boot (Black Screen) (FAQ 1014276) | tambahan | https://www.asus.com/support/faq/1014276/ |
| T2 | ASUS | Troubleshooting - Battery not supplying power/charging… (FAQ 1012793) | tambahan | https://www.asus.com/support/faq/1012793/ |
| T3 | HP | HP PCs - How to power reset your computer | tambahan | https://support.hp.com/us-en/document/ish_1997208-1551050-16 |
