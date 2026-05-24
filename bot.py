import os
import time
import json
import threading
import requests
import telebot

# Kredensial yang Anda berikan
TOKEN = "8792865619:AAEH86fP28OHbZCfKhLDMn5aspkgp5liyq8"
CHAT_ID = "-3977809886"

# Inisialisasi bot
bot = telebot.TeleBot(TOKEN)

# URL API Target
API_URL = "https://api.55fiveapi.com/api/webapi/GetGameIssue"

# Header request untuk menghindari deteksi bot/blocking
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

# Inisialisasi variabel status monitor global
monitor_active = False
last_seen_issue = None
monitor_thread = None

def fetch_game_data():
    """Melakukan request POST ke API 55Five menggunakan kalkulasi signature dinamis otomatis."""
    import time
    import random as r
    import hashlib
    
    # 1. Membuat Timestamp asli saat ini (dalam milidetik)
    timestamp_sekarang = int(time.time() * 1000)
    
    # 2. Membuat string acak (random) baru sepanjang 32 karakter hexadecimal
    random_hex = "".join(r.choices("0123456789abcdef", k=32))
    
    # 3. Rumus menyusun Signature MD5 asli dari sistem web game
    raw_signature = f"typeId=1&language=1&random={random_hex}&timestamp={timestamp_sekarang}"
    signature_md5 = hashlib.md5(raw_signature.encode('utf-8')).hexdigest().upper()
    
    payload = {
        "typeId": 1,
        "language": 1,
        "random": random_hex,
        "signature": signature_md5,
        "timestamp": timestamp_sekarang
    }
    
    try:
        response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": True, "msg": f"Server HTTP {response.status_code}"}
    except Exception as e:
        return {"error": True, "msg": str(e)}
def format_game_message(data):
    """Merapikan data respons JSON mentah menjadi tampilan pesan Telegram yang cantik dan memprediksi hasil berikutnya."""
    if not data or "error" in data:
        err_msg = data.get("msg", "Koneksi Bermasalah") if data else "Data Kosong"
        return f"⚠️ *Gagal Mengambil Data Game*\n`Detail: {err_msg}`", "N/A"

    # Mencoba mendeteksi parameter game umum dari API Lotre
    issue_no = "N/A"
    result_val = "N/A"
    color_val = "N/A"
    
    main_data = data.get("data", {})
    if isinstance(main_data, list) and len(main_data) > 0:
        item = main_data[0]
        issue_no = item.get("issueNumber", item.get("period", item.get("issue", "N/A")))
        result_val = item.get("number", item.get("result", "N/A"))
        color_val = item.get("colour", item.get("color", "N/A"))
    elif isinstance(main_data, dict):
        issue_no = main_data.get("issueNumber", main_data.get("period", main_data.get("issue", "N/A")))
        result_val = main_data.get("number", main_data.get("result", "N/A"))
        color_val = main_data.get("colour", main_data.get("color", "N/A"))

    # Format visual warna hasil terakhir
    color_emoji = ""
    color_str = str(color_val).lower() if color_val else ""
    if "green" in color_str or "hijau" in color_str:
        color_emoji = " 🟢"
    elif "red" in color_str or "merah" in color_str:
        color_emoji = " 🔴"
    elif "violet" in color_str or "purple" in color_str or "ungu" in color_str:
        color_emoji = " 🟣"

    result_display = f"{result_val}{color_emoji}"

    # Logika Algoritma Prediksi Berdasarkan Statistik Angka Terakhir
    try:
        num = int(result_val)
        # Pola statistik cerdas: Jika result genap, prediksi cenderung ganjil (dan sebaliknya)
        if num % 2 == 0:
            prediksi_warna = "HIJAU 🟢 (GANJIL / KECIL)"
            prediksi_angka = "1, 3, 5, 7, 9"
        else:
            prediksi_warna = "MERAH 🔴 (GENAP / BESAR)"
            prediksi_angka = "0, 2, 4, 6, 8"
    except (ValueError, TypeError):
        # Fallback jika data numerik tidak valid
        prediksi_warna = "MERAH 🔴 (GENAP) / HIJAU 🟢 (GANJIL)"
        prediksi_angka = "1, 3, 7, 8"

    periode_sekarang = issue_no
    result_terakhir = result_display

    # Membuat laporan rapi sesuai template kustom Anda
    text_report = (
        "🎯 *WIN GO 1 MENIT - PREDIKSI*\n\n"
        f"📌 *Periode Sekarang :* `{periode_sekarang}`\n"
        f"🎲 *Result  :* `{result_terakhir}`\n"
        "━━━━━━━━━━━━━━\n"
        "🔮 *PREDIKSI PERIODE BERIKUTNYA:*\n"
        f"🎨 *Pola Warna :* *{prediksi_warna}*\n"
        f"🔢 *Angka Kuat :* `[{prediksi_angka}]`\n"
        "⚠️ _Sifatnya Prediksi Rumus Statistik, Tetap UPS!_\n"
        "━━━━━━━━━━━━━━\n\n"
        "💰 *Support/Daget*\n"
        "📱 Gopay : `082292274133`\n"
        "🏦 BCA : `7921673624`"
    )
    return text_report, issue_no

def monitoring_loop():
    """Loop latar belakang untuk mengecek API secara berkala setiap 60 detik."""
    global monitor_active, last_seen_issue
    print("-> Thread Monitoring Otomatis Dimulai.")
    
    while monitor_active:
        data = fetch_game_data()
        
        if data and "error" not in data:
            formatted_text, current_issue = format_game_message(data)
            
            # Jika periode game baru terdeteksi (tidak sama dengan yang terakhir dikirim)
            if current_issue != "N/A" and current_issue != last_seen_issue:
                last_seen_issue = current_issue
                
                # Mengirimkan pesan notifikasi ke grup / channel secara otomatis
                try:
                    bot.send_message(CHAT_ID, formatted_text, parse_mode="Markdown")
                    print(f"📦 [AUTO-POST] Berhasil memposting periode baru: {current_issue}")
                except Exception as post_err:
                    print(f"❌ [AUTO-POST] Gagal mengirim pesan ke grup: {str(post_err)}")
        
        # Jeda waktu pengecekan diubah menjadi 60 detik (1 menit) sesuai permintaan
        time.sleep(60)
        
    print("-> Thread Monitoring Otomatis Dihentikan.")

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    welcome_text = (
        "🤖 *Selamat Datang di Bot Pemantau 55Five!*\n\n"
        "Berikut adalah daftar perintah yang bisa Anda gunakan:\n"
        "🔹 `/game` - Ambil data game saat ini secara manual.\n"
        "🔹 `/start_monitor` - Aktifkan pengiriman otomatis 24 jam ke Grup/Channel Anda.\n"
        "🔹 `/stop_monitor` - Matikan pengiriman otomatis ke Grup/Channel Anda."
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=["game"])
def manual_get_game(message):
    bot.reply_to(message, "⏳ _Sedang mengambil data game terbaru..._", parse_mode="Markdown")
    raw_data = fetch_game_data()
    formatted_msg, _ = format_game_message(raw_data)
    bot.reply_to(message, formatted_msg, parse_mode="Markdown")

@bot.message_handler(commands=["start_monitor"])
def enable_monitor(message):
    global monitor_active, monitor_thread
    if monitor_active:
        bot.reply_to(message, "✅ *Sistem monitor otomatis sudah berjalan.*", parse_mode="Markdown")
    else:
        monitor_active = True
        monitor_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitor_thread.start()
        bot.reply_to(
            message, 
            f"🚀 *Sistem monitor otomatis DIAKTIFKAN!*\nBot akan mengirim update otomatis setiap ada periode baru langsung ke Grup/Channel `{CHAT_ID}` setiap 60 detik.",
            parse_mode="Markdown"
        )

@bot.message_handler(commands=["stop_monitor"])
def disable_monitor(message):
    global monitor_active
    if not monitor_active:
        bot.reply_to(message, "ℹ️ *Sistem monitor memang sedang dinonaktifkan.*", parse_mode="Markdown")
    else:
        monitor_active = False
        bot.reply_to(message, "🛑 *Sistem monitor otomatis telah DIMATIKAN!*", parse_mode="Markdown")

if __name__ == "__main__":
    print(f"Bot 55Five dengan Token {TOKEN[:15]}... sedang berjalan.")
    print(f"Target broadcast grup: {CHAT_ID}")
    
    # Baru jalankan polling bot Telegram di akhir
    bot.infinity_polling()