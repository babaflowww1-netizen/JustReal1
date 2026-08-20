from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import sqlite3
import os
import logging
import requests
import threading
import time
from datetime import datetime

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
app.secret_key = "justreal_super_secret_key_security_998877"

WEB_APP_URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://sitenin-adi.onrender.com')
TELEGRAM_BOT_TOKEN = "8692317800:AAGhN5UEe5Efycth5P6JqvNQ6xAja7D2P7M"
ZORUNLU_KANAL = "@JustRealLog" # Zorunlu kanal kullanıcı adın (Örn: @JustRealChannel)

def init_db():
    conn = sqlite3.connect('justreal_checker.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT UNIQUE,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password TEXT,
            profile_pic TEXT DEFAULT 'https://i.imgur.com/6VBx3io.png',
            role TEXT DEFAULT 'Normal',
            daily_limit INTEGER DEFAULT 1500,
            used_today INTEGER DEFAULT 0,
            total_lives INTEGER DEFAULT 0,
            total_checks INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0,
            theme TEXT DEFAULT 'dark'
        )
    ''')
    
    for col, definition in [('total_checks', 'INTEGER DEFAULT 0'), ('theme', "TEXT DEFAULT 'dark'"), ('profile_pic', "TEXT DEFAULT 'https://i.imgur.com/6VBx3io.png'")]:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
            conn.commit()
        except:
            pass
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checker_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            gateway TEXT,
            masked_card TEXT,
            status TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    try:
        admin_mail = "admin.security.master_2026@justreal-secure.net"
        admin_pass = "Xy&9#mP$2vL!qK7*wZ#8"
        admin_user = "JustReal_MasterAdmin"
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, email, password, profile_pic, role, daily_limit, total_lives, is_banned) 
            VALUES (?, ?, ?, 'https://i.imgur.com/6VBx3io.png', 'Admin', 999999, 100, 0)
        ''', (admin_user, admin_mail, admin_pass))
        conn.commit()
    except Exception as e:
        print("Admin hatası:", e)
        
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect('justreal_checker.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def background_scheduler():
    while True:
        try:
            now = datetime.now()
            if now.hour == 0 and now.minute == 0:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET used_today = 0')
                conn.commit()
                conn.close()
                time.sleep(60)
        except:
            pass
        time.sleep(30)

threading.Thread(target=background_scheduler, daemon=True).start()

def send_telegram_channel_log(masked_cc, mm, yy, gateway, username, role):
    CHANNEL_ID = "SENIN_KANAL_ID"
    role_text = "Normal Üye"
    if role == 'VIP': role_text = "VIP Üye"
    elif role == 'Admin': role_text = "Admin"
    
    message = (
        "💎 YENİ LİVE KART BULUNDU! 🟢\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💳 Kart: {masked_cc}\n"
        f"📅 Skat: {mm}/{yy} | 🔒 CVV: ***\n"
        f"🌐 Gateway: {gateway}\n"
        f"👤 Checkleyen: @{username} ({role_text})\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ Bot: JustReal Multi-Checker"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHANNEL_ID, "text": message}, timeout=3)
    except:
        pass

def check_user_channel_membership(chat_id):
    if ZORUNLU_KANAL == "@senin_kanal_kullanici_adin":
        return True
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getChatMember?chat_id={ZORUNLU_KANAL}&user_id={chat_id}"
    try:
        res = requests.get(url, timeout=3).json()
        if res.get("ok"):
            status = res["result"].get("status")
            if status in ["creator", "administrator", "member"]:
                return True
    except:
        pass
    return False

def telegram_bot_listener():
    if TELEGRAM_BOT_TOKEN == "SENIN_BOT_TOKENIN":
        return

    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=30"
            response = requests.get(url, timeout=35)
            data = response.json()
            
            if data.get("ok"):
                for result in data.get("result", []):
                    offset = result["update_id"] + 1
                    message = result.get("message")
                    if message and "text" in message:
                        chat_id = message["chat"]["id"]
                        text = message["text"]
                        user_name = message["from"].get("first_name", "Kullanıcı")
                        
                        if text.startswith("/start"):
                            is_member = check_user_channel_membership(chat_id)
                            send_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                            
                            if not is_member:
                                welcome_msg = (
                                    f"👋 Merhaba {user_name}!\n\n"
                                    f"🚨 **JustReal Multi-Checker** sistemini kullanabilmek için öncelikle resmi kanalımıza katılman gerekmektedir.\n\n"
                                    f"👉 Lütfen kanalımıza katıldıktan sonra tekrar `/start` komutuna bas."
                                )
                                keyboard = {
                                    "inline_keyboard": [
                                        [{"text": "📢 Kanala Katıl", "url": f"https://t.me/{ZORUNLU_KANAL.replace('@', '')}"}],
                                        [{"text": "🔄 Kontrol Et / Yeniden Başlat", "url": f"https://t.me/{(requests.get(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe').json().get('result', {}).get('username', ''))}"}]
                                    ]
                                }
                            else:
                                welcome_msg = (
                                    f"👋 Merhaba {user_name}!\n\n"
                                    "🚀 **JustReal Multi-Checker** sistemine hoş geldin.\n\n"
                                    "Aşağıdaki butona tıklayarak güvenli web panelimizi açabilir ve kart check edebilirsin."
                                )
                                keyboard = {
                                    "inline_keyboard": [
                                        [{"text": "🚀 Paneli Aç (Mini App)", "web_app": {"url": WEB_APP_URL}}],
                                        [{"text": "🌐 Web Sitesi Olarak Aç", "url": WEB_APP_URL}]
                                    ]
                                }
                                
                            requests.post(send_url, json={"chat_id": chat_id, "text": welcome_msg, "parse_mode": "Markdown", "reply_markup": keyboard})
        except:
            time.sleep(5)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>JustReal - Multi Checker</title>
    <style>
        :root {
            --bg-grad: linear-gradient(135deg, #0b0f19, #1a1f2c);
            --card-bg: rgba(255,255,255,0.05);
            --text-color: #fff;
            --border-col: rgba(255,255,255,0.1);
            --input-bg: #121826;
        }
        [data-theme="light"] {
            --bg-grad: linear-gradient(135deg, #f3f4f6, #e5e7eb);
            --card-bg: rgba(0,0,0,0.03);
            --text-color: #1f2937;
            --border-col: rgba(0,0,0,0.1);
            --input-bg: #ffffff;
        }
        * { box-sizing: border-box; }
        body { background: var(--bg-grad); color: var(--text-color); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin:0; padding:10px; min-height: 100vh; transition: 0.3s; display: flex; justify-content: center; align-items: flex-start; }
        .container { width: 100%; max-width: 500px; margin: auto; position: relative; padding-bottom: 20px; }
        .brand-corner { position: absolute; top: 10px; right: 10px; font-weight: bold; color: #8b5cf6; font-size: 16px; z-index: 10; }
        .center-brand { text-align: center; font-size: 24px; font-weight: bold; color: #8b5cf6; margin: 15px 0 10px 0; letter-spacing: 1px; }
        .card { background: var(--card-bg); padding: 15px; border-radius: 12px; margin-bottom: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.15); border: 1px solid var(--border-col); }
        input, select, textarea, button { width: 100%; padding: 12px; margin: 6px 0; background: var(--input-bg); border: 1px solid var(--border-col); color: var(--text-color); border-radius: 8px; font-size: 14px; }
        button { background: #8b5cf6; font-weight: bold; cursor: pointer; transition: 0.2s; border: none; color: #fff; }
        button:hover { background: #7c3aed; }
        .badge-normal { background: #10b981; color: #fff; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; display: inline-block; }
        .badge-vip { background: #f59e0b; color: #000; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; display: inline-block; }
        .badge-admin { background: #ef4444; color: #fff; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; display: inline-block; }
        .error-box { background: rgba(239, 68, 68, 0.2); border: 1px solid #ef4444; padding: 10px; border-radius: 8px; margin-bottom: 10px; color: #fca5a5; font-size: 13px; text-align: center; }
        .announcement-box { background: rgba(245, 158, 11, 0.15); border: 1px solid #f59e0b; padding: 10px; border-radius: 8px; margin-bottom: 12px; color: #fde68a; font-size: 13px; }
        .stats-grid { display: flex; justify-content: space-between; gap: 8px; margin-bottom: 12px; }
        .stat-card { background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); flex: 1; padding: 8px; border-radius: 8px; text-align: center; }
        .stat-card h5 { margin: 0 0 3px 0; color: #a78bfa; font-size: 11px; }
        .stat-card span { font-size: 15px; font-weight: bold; color: var(--text-color); }
        .avatar-img { width: 45px; height: 45px; border-radius: 50%; object-fit: cover; border: 2px solid #8b5cf6; flex-shrink: 0; }
        .live-feed { max-height: 85px; overflow-y: auto; font-size: 11px; background: rgba(0,0,0,0.1); padding: 8px; border-radius: 6px; color: #10b981; }
        
        /* Mobil ve Desktop Esneklik Ayarları */
        @media (min-width: 768px) {
            body { padding: 30px; }
            .container { max-width: 550px; }
            .card { padding: 20px; }
        }

        #toast { visibility: hidden; min-width: 220px; background-color: #10b981; color: #fff; text-align: center; border-radius: 8px; padding: 12px; position: fixed; z-index: 1000; left: 50%; transform: translateX(-50%); bottom: 20px; font-weight: bold; box-shadow: 0 4px 12px rgba(0,0,0,0.5); font-size: 13px; }
        #toast.show { visibility: visible; animation: fadein 0.5s, fadeout 0.5s 2.5s; }
        @keyframes fadein { from {bottom: 0; opacity: 0;} to {bottom: 20px; opacity: 1;} }
        @keyframes fadeout { from {bottom: 20px; opacity: 1;} to {bottom: 0; opacity: 0;} }
    </style>
</head>
<body data-theme="{{ session.get('user', {}).get('theme', 'dark') }}">
    <div class="brand-corner">JustReal</div>
    <div class="container">
        <div class="center-brand">JustReal</div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h5>👥 Üyeler</h5>
                <span>{{ stats.total_users }}</span>
            </div>
            <div class="stat-card">
                <h5>💎 Toplam Live</h5>
                <span>{{ stats.total_lives }}</span>
            </div>
            <div class="stat-card">
                <h5>🟢 Aktif / Gün</h5>
                <span>{{ stats.active_today }}</span>
            </div>
        </div>

        {% if error %}
            <div class="error-box">{{ error }}</div>
        {% endif %}

        {% if latest_announcement %}
            <div class="announcement-box">
                📢 <b>Admin Duyurusu:</b><br>{{ latest_announcement }}
            </div>
        {% endif %}

        <div class="card" style="padding: 10px;">
            <div style="font-size:12px; font-weight:bold; margin-bottom:5px; color:#a78bfa;">⚡ Son Global Live Kart Akışı</div>
            <div class="live-feed">
                {% for feed in live_feeds %}
                    <div>🟢 @{{ feed.username }} [{{ feed.gateway }}] -> <b>{{ feed.masked_card }}</b></div>
                {% else %}
                    <div>Henüz sistemde canlı live kart akışı yok.</div>
                {% endfor %}
            </div>
        </div>

        {% if not session.get('user') %}
            <div class="card">
                <h3 style="margin-top:0; text-align:center; font-size:18px;">Giriş Yap / Kayıt Ol</h3>
                <form method="POST" action="/auth">
                    <label style="font-size:13px;">Gmail Adresi:</label>
                    <input type="email" name="email" placeholder="ornek@eposta.com" required>
                    <label style="font-size:13px;">Kullanıcı Adı:</label>
                    <input type="text" name="username" placeholder="Richy" required>
                    <label style="font-size:13px;">Şifre:</label>
                    <input type="password" name="password" placeholder="••••••••" required>
                    <button type="submit" name="action" value="login">🚀 Giriş Yap Butonu</button>
                    <button type="submit" name="action" value="register" style="background:#3b82f6;">📝 Kayıt Ol Butonu</button>
                </form>
            </div>
        {% else %}
            <div class="card">
                <div style="display:flex; align-items:center; gap:12px;">
                    <img src="{{ session['user']['profile_pic'] }}" class="avatar-img" alt="Avatar">
                    <div style="flex-grow:1; min-width: 0;">
                        <div style="display:flex; justify-content:space-between; align-items:center; gap: 5px;">
                            <span style="font-weight:bold; font-size:15px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">@{{ session['user']['username'] }}</span>
                            {% if session['user']['role'] == 'Admin' %}
                                <span class="badge-admin">ADMİN</span>
                            {% elif session['user']['role'] == 'VIP' %}
                                <span class="badge-vip">VİP</span>
                            {% else %}
                                <span class="badge-normal">NORMAL</span>
                            {% endif %}
                        </div>
                        <p style="margin:4px 0 0 0; font-size:12px; opacity: 0.8;">⚡ Günlük Hak: {{ session['user']['used_today'] }} / {{ session['user']['daily_limit'] }}</p>
                    </div>
                </div>
            </div>

            <div class="card">
                <form method="POST" action="/run-check" id="checkForm" onsubmit="return handleCheckSubmit()">
                    <label style="font-size:13px;">Gateway Seçimi:</label>
                    <select name="gateway">
                        <option value="Auth Gate">🌐 Auth Gate</option>
                        <option value="Puan Gate">💳 Puan Gate</option>
                        <option value="Shopify Gate">🔄 Shopify Gate</option>
                    </select>
                    
                    <label style="font-size:13px; margin-top:5px; display:block;">Kartları Yapıştır (CC|MM|YY|CVV):</label>
                    <textarea name="cards" rows="4" placeholder="453210|12|28|123" required style="font-family:monospace;"></textarea>
                    <button type="submit" id="checkBtn">🚀 Check Başlat Butonu</button>
                </form>
            </div>

            <div class="card">
                <button onclick="location.href='/bin-tool'">🔍 Bin Kontrol Aracı</button>
                <button onclick="location.href='/cc-cleaner'" style="background:#3b82f6;">🧹 CC Temizleyici (Cleaner)</button>
                <button onclick="location.href='/leaderboard'" style="background:#f59e0b; color:#000;">👑 En İyiler Butonu</button>
                <button onclick="location.href='/profile'" style="background:#6366f1;">👤 Profil & Tema Ayarları</button>
                {% if session['user']['role'] == 'Admin' %}
                    <button onclick="location.href='/admin'" style="background:#ef4444;">⚙️ Admin Paneli Butonu</button>
                {% endif %}
                <button onclick="location.href='/logout'" style="background:#374151; margin-top:5px;">Çıkış Yap</button>
            </div>
        {% endif %}
    </div>

    <div id="toast">🟢 İşlem Başarılı / Live Kart Çıktı!</div>
    <script>
        let lastCheckTime = 0;
        function handleCheckSubmit() {
            let now = Date.now();
            if (now - lastCheckTime < 3000) {
                alert("Anti-Spam Koruması: Lütfen ard arda çok hızlı istek atmayın, 3 saniye bekleyin!");
                return false;
            }
            lastCheckTime = now;
            
            var x = document.getElementById("toast");
            x.className = "show";
            setTimeout(function(){ x.className = x.className.replace("show", ""); }, 3000);
            
            try {
                let ctx = new (window.AudioContext || window.webkitAudioContext)();
                let osc = ctx.createOscillator();
                let gain = ctx.createGain();
                osc.type = "sine";
                osc.frequency.setValueAtTime(587.33, ctx.currentTime);
                gain.gain.setValueAtTime(0.1, ctx.currentTime);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start();
                osc.stop(ctx.currentTime + 0.15);
            } catch(e) {}
            return true;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    error = request.args.get('error')
    
    if 'user' in session:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (session['user']['id'],))
        db_user = cursor.fetchone()
        if db_user:
            if db_user['is_banned'] == 1:
                session.clear()
                conn.close()
                return redirect(url_for('index', error="Hesabınız yasaklandığı için oturumunuz sonlandırıldı!"))
            session['user'] = dict(db_user)
        conn.close()

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT content FROM announcements ORDER BY id DESC LIMIT 1')
    ann = cursor.fetchone()
    
    cursor.execute('SELECT COUNT(*) as cnt FROM users')
    total_users = cursor.fetchone()['cnt']
    
    cursor.execute('SELECT SUM(total_lives) as lives FROM users')
    total_lives_res = cursor.fetchone()['lives']
    total_lives = total_lives_res if total_lives_res else 0
    
    cursor.execute('SELECT COUNT(DISTINCT username) as active FROM checker_logs')
    active_today = cursor.fetchone()['active']
    
    cursor.execute('SELECT username, gateway, masked_card FROM checker_logs WHERE status = "LIVE" ORDER BY id DESC LIMIT 5')
    live_feeds = cursor.fetchall()
    
    conn.close()
    
    latest_announcement = ann['content'] if ann else None
    stats = {
        "total_users": total_users,
        "total_lives": total_lives,
        "active_today": active_today
    }
    return render_template_string(HTML_TEMPLATE, error=error, latest_announcement=latest_announcement, stats=stats, live_feeds=live_feeds)

@app.route('/auth', methods=['POST'])
def auth():
    action = request.form.get('action')
    email = request.form.get('email')
    username = request.form.get('username')
    password = request.form.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if action == 'register':
        try:
            default_avatar = "https://i.imgur.com/6VBx3io.png"
            cursor.execute('INSERT INTO users (username, email, password, profile_pic, role, daily_limit, total_lives, total_checks, is_banned, theme) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, ?)',
                           (username, email, password, default_avatar, 'Normal', 1500, 0, 'dark'))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return redirect(url_for('index', error="Bu Gmail veya Kullanıcı Adı zaten kayıtlı!"))
    
    cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        if user['is_banned'] == 1:
            return redirect(url_for('index', error="Hesabınız sistem yöneticisi tarafından yasaklanmıştır!"))
        session['user'] = dict(user)
        return redirect(url_for('index'))
    return redirect(url_for('index', error="Giriş Başarısız! Bilgileri kontrol edin."))

@app.route('/run-check', methods=['POST'])
def run_check():
    if 'user' not in session or session['user'].get('is_banned') == 1:
        return redirect(url_for('index'))
        
    gateway = request.form.get('gateway')
    cards_text = request.form.get('cards', '')
    cards = [c.strip() for c in cards_text.split('\n') if c.strip()]
    username = session['user']['username']
    role = session['user']['role']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for card in cards:
        parts = card.split('|')
        if len(parts) == 4:
            cc, mm, yy, cvv = parts
            masked_cc = f"{cc[:6]}******{cc[-4:]}"
            
            send_telegram_channel_log(masked_cc, mm, yy, gateway, username, role)
            
            cursor.execute('INSERT INTO checker_logs (username, gateway, masked_card, status) VALUES (?, ?, ?, ?)',
                           (username, gateway, masked_cc, 'LIVE'))
            
            cursor.execute('UPDATE users SET total_lives = total_lives + 1, total_checks = total_checks + 1, used_today = used_today + 1 WHERE id = ?', (session['user']['id'],))
            conn.commit()
            break 

    cursor.execute('SELECT * FROM users WHERE id = ?', (session['user']['id'],))
    session['user'] = dict(cursor.fetchone())
    conn.close()

    return redirect(url_for('index'))

@app.route('/bin-tool', methods=['GET', 'POST'])
def bin_tool():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    bin_result = None
    if request.method == 'POST':
        bin_code = request.form.get('bin_code', '').strip()
        if len(bin_code) >= 6:
            clean_bin = bin_code[:6]
            try:
                res = requests.get(f"https://lookup.binlist.net/{clean_bin}", headers={"Accept-Version": "3"}, timeout=3)
                if res.status_code == 200:
                    data = res.json()
                    scheme = data.get('scheme', 'Bilinmiyor').upper()
                    brand = data.get('brand', 'Bilinmiyor')
                    type_c = data.get('type', 'Bilinmiyor').upper()
                    bank_name = data.get('bank', {}).get('name', 'Bilinmiyor')
                    country = data.get('country', {}).get('name', 'Bilinmiyor')
                    bin_result = f"BIN: {clean_bin} | Kart Türü: {scheme} ({type_c}) | Marka: {brand} | Banka: {bank_name} | Ülke: {country}"
                else:
                    bin_result = f"BIN: {clean_bin} için detay bulunamadı."
            except:
                bin_result = f"BIN: {clean_bin} (Sorgulama Servisi Yoğun)"
        else:
            bin_result = "Lütfen en az ilk 6 haneyi girin!"

    bin_html = """
    <div style="width:100%; max-width:480px; margin:20px auto; background:var(--input-bg); padding:20px; border-radius:10px; color:var(--text-color); font-family:sans-serif; border:1px solid rgba(139,92,246,0.3);">
        <h3>🔍 Bin Kontrol Aracı</h3>
        <p style="font-size:13px; opacity:0.7;">Kartın ilk 6 hanesini yazarak banka ve ülke bilgilerini öğrenebilirsiniz.</p>
        <form method="POST">
            <input type="text" name="bin_code" placeholder="453210 veya tam kart" maxlength="19" required style="width:100%; padding:10px; margin:5px 0; background:rgba(255,255,255,0.05); color:inherit; border:1px solid rgba(255,255,255,0.1); border-radius:6px;">
            <button type="submit" style="width:100%; padding:12px; margin-top:10px; background:#8b5cf6; color:#fff; border:none; border-radius:6px; font-weight:bold;">🔍 BIN Sorgula</button>
        </form>
        {% if bin_result %}
            <div style="background:rgba(139, 92, 246, 0.1); border:1px solid #8b5cf6; padding:10px; border-radius:6px; margin-top:10px; font-size:13px;">{{ bin_result }}</div>
        {% endif %}
        <button onclick="location.href='/'" style="width:100%; padding:12px; margin-top:15px; background:#374151; color:#fff; border:none; border-radius:6px; font-weight:bold;">⬅️ Ana Menüye Dön</button>
    </div>
    """
    return render_template_string(bin_html, bin_result=bin_result)

@app.route('/cc-cleaner', methods=['GET', 'POST'])
def cc_cleaner():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    cleaned_output = ""
    if request.method == 'POST':
        raw_text = request.form.get('raw_text', '')
        lines = raw_text.split('\n')
        valid_cards = []
        for line in lines:
            line = line.strip()
            parts = line.replace(';', '|').replace(':', '|').replace(',', '|').split('|')
            if len(parts) >= 4:
                cc = parts[0].strip()
                mm = parts[1].strip()
                yy = parts[2].strip()
                cvv = parts[3].strip()
                if cc.isdigit() and len(cc) >= 13 and mm.isdigit() and yy.isdigit() and cvv.isdigit():
                    valid_cards.append(f"{cc}|{mm}|{yy}|{cvv}")
        cleaned_output = "\n".join(valid_cards)

    cleaner_html = f"""
    <div style="width:100%; max-width:480px; margin:20px auto; background:var(--input-bg); padding:20px; border-radius:10px; color:var(--text-color); font-family:sans-serif; border:1px solid rgba(59,130,246,0.3);">
        <h3>🧹 CC Temizleyici & Ayıklayıcı</h3>
        <p style="font-size:13px; opacity:0.7;">Karışık metinler içindeki bozuk satırları temizler ve sadece düzgün CC|MM|YY|CVV formatını ayıklar.</p>
        <form method="POST">
            <textarea name="raw_text" rows="5" placeholder="Karışık kart listesini buraya yapıştırın..." required style="width:100%; padding:10px; background:rgba(255,255,255,0.05); color:inherit; border:1px solid rgba(255,255,255,0.1); border-radius:6px; box-sizing:border-box; font-family:monospace;"></textarea>
            <button type="submit" style="width:100%; padding:12px; margin-top:5px; background:#3b82f6; color:#fff; border:none; border-radius:6px; font-weight:bold;">🧹 Temizle ve Ayıkla</button>
        </form>
        {% if request.method == 'POST' %}
            <label style="font-size:13px; margin-top:10px; display:block;">Temizlenmiş Liste ({{ cleaned_output.splitlines()|length if cleaned_output else 0 }} Adet):</label>
            <textarea rows="5" readonly style="width:100%; padding:10px; background:rgba(0,0,0,0.2); color:#10b981; border:1px solid #10b981; border-radius:6px; box-sizing:border-box; font-family:monospace;">{{ cleaned_output }}</textarea>
        {% endif %}
        <button onclick="location.href='/'" style="width:100%; padding:12px; margin-top:15px; background:#374151; color:#fff; border:none; border-radius:6px; font-weight:bold;">⬅️ Ana Menüye Dön</button>
    </div>
    """
    return render_template_string(cleaner_html, cleaned_output=cleaned_output)

@app.route('/leaderboard')
def leaderboard():
    if 'user' not in session:
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT username, role, total_lives FROM users ORDER BY total_lives DESC LIMIT 15')
    top_users = cursor.fetchall()
    conn.close()
    
    rows_html = ""
    for index, row in enumerate(top_users, start=1):
        medal = "🥇" if index == 1 else ("🥈" if index == 2 else ("🥉" if index == 3 else f"{index}."))
        rows_html += f"""
        <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
            <td style="padding:10px; text-align:center;">{medal}</td>
            <td style="padding:10px; font-weight:bold;">@{row['username']}</td>
            <td style="padding:10px; text-align:center;">{row['role']}</td>
            <td style="padding:10px; text-align:center; color:#10b981; font-weight:bold;">{row['total_lives']} Live</td>
        </tr>
        """

    lb_html = f"""
    <div style="width:100%; max-width:480px; margin:20px auto; background:var(--input-bg); padding:20px; border-radius:10px; color:var(--text-color); font-family:sans-serif; border:1px solid rgba(245,158,11,0.3);">
        <h3 style="text-align:center;">👑 En İyiler Listesi (Top 15)</h3>
        <p style="font-size:12px; opacity:0.7; text-align:center;">En çok başarılı live kart çıkartan lider kullanıcılar.</p>
        <div style="overflow-x:auto;">
            <table style="width:100%; border-collapse:collapse; margin-top:10px; font-size:14px;">
                <thead>
                    <tr style="background:rgba(255,255,255,0.05); opacity:0.8;">
                        <th style="padding:8px; text-align:center;">Sıra</th>
                        <th style="padding:8px; text-align:left;">Kullanıcı</th>
                        <th style="padding:8px; text-align:center;">Rol</th>
                        <th style="padding:8px; text-align:center;">Live</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html if rows_html else '<tr><td colspan="4" style="text-align:center; padding:15px;">Henüz listelenen veri yok.</td></tr>'}
                </tbody>
            </table>
        </div>
        <button onclick="location.href='/'" style="width:100%; padding:12px; margin-top:20px; background:#374151; color:#fff; border:none; border-radius:6px; font-weight:bold;">⬅️ Ana Menüye Dön</button>
    </div>
    """
    return render_template_string(lb_html)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    error = None
    success_msg = None
    
    if request.method == 'POST':
        new_name = request.form.get('username')
        new_email = request.form.get('email')
        new_pic = request.form.get('profile_pic')
        new_theme = request.form.get('theme')
        
        try:
            cursor.execute('UPDATE users SET username = ?, email = ?, profile_pic = ?, theme = ? WHERE id = ?', 
                           (new_name, new_email, new_pic, new_theme, session['user']['id']))
            conn.commit()
            cursor.execute('SELECT * FROM users WHERE id = ?', (session['user']['id'],))
            session['user'] = dict(cursor.fetchone())
            success_msg = "Profil ve tema tercihleriniz başarıyla kaydedildi!"
        except sqlite3.IntegrityError:
            error = "Hata: Bu ad veya Gmail başka bir kullanıcı tarafından kullanımda!"
            
    u = session['user']
    t_checks = u.get('total_checks', 0)
    t_lives = u.get('total_lives', 0)
    success_rate = round((t_lives / t_checks * 100), 1) if t_checks > 0 else 0.0

    conn.close()
    
    profile_html = f"""
    <div style="width:100%; max-width:450px; margin:20px auto; background:var(--input-bg); padding:20px; border-radius:10px; color:var(--text-color); font-family:sans-serif; border:1px solid rgba(99,102,241,0.3);">
        <h3>👤 Profil, İstatistik & Tema</h3>
        <p style="font-size:12px; opacity:0.7;">Verileriniz güvenli veritabanında saklanır.</p>
        
        {% if error %}<p style="color:#fca5a5; font-size:13px;">{{ error }}</p>{% endif %}
        {% if success_msg %}<p style="color:#6ee7b7; font-size:13px;">{{ success_msg }}</p>{% endif %}
        
        <div style="text-align:center; margin:15px 0;">
            <img src="{u['profile_pic']}" style="width:70px; height:70px; border-radius:50%; object-fit:cover; border:2px solid #8b5cf6;" alt="Avatar">
        </div>

        <div style="background:rgba(139,92,246,0.1); padding:10px; border-radius:6px; margin-bottom:15px; font-size:13px; display:flex; justify-content:space-around; text-align:center;">
            <div><b>{t_checks}</b><br><span style="font-size:11px; opacity:0.7;">Toplam Check</span></div>
            <div><b>{t_lives}</b><br><span style="font-size:11px; opacity:0.7;">Toplam Live</span></div>
            <div><b>%{success_rate}</b><br><span style="font-size:11px; opacity:0.7;">Başarı Oranı</span></div>
        </div>
        
        <form method="POST">
            <label style="font-size:13px;">Kullanıcı Adı:</label>
            <input type="text" name="username" value="{u['username']}" required style="width:100%; padding:10px; margin:4px 0; background:rgba(255,255,255,0.05); color:inherit; border:1px solid rgba(255,255,255,0.1); border-radius:6px;">
            
            <label style="font-size:13px;">Gmail Adresi:</label>
            <input type="email" name="email" value="{u['email']}" required style="width:100%; padding:10px; margin:4px 0; background:rgba(255,255,255,0.05); color:inherit; border:1px solid rgba(255,255,255,0.1); border-radius:6px;">
            
            <label style="font-size:13px;">Avatar URL:</label>
            <input type="url" name="profile_pic" value="{u['profile_pic']}" required style="width:100%; padding:10px; margin:4px 0; background:rgba(255,255,255,0.05); color:inherit; border:1px solid rgba(255,255,255,0.1); border-radius:6px;">
            
            <label style="font-size:13px;">Arayüz Teması:</label>
            <select name="theme" style="width:100%; padding:10px; margin:4px 0; background:rgba(255,255,255,0.05); color:inherit; border:1px solid rgba(255,255,255,0.1); border-radius:6px;">
                <option value="dark" {'selected' if u.get('theme')=='dark' else ''}>Koyu Tema (Dark Mode)</option>
                <option value="light" {'selected' if u.get('theme')=='light' else ''}>Açık Tema (Light Mode)</option>
            </select>
            
            <button type="submit" style="width:100%; padding:12px; margin-top:10px; background:#6366f1; color:#fff; border:none; border-radius:6px; font-weight:bold;">💾 Kalıcı Kaydet</button>
        </form>
        
        <button onclick="location.href='/'" style="width:100%; padding:12px; margin-top:10px; background:#374151; color:#fff; border:none; border-radius:6px; font-weight:bold;">⬅️ Ana Menüye Dön</button>
    </div>
    """
    return render_template_string(profile_html, error=error, success_msg=success_msg)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user' not in session or session['user']['role'] != 'Admin':
        return "Yetkisiz Erişim!"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    success_msg = None
    
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        
        if form_type == 'limit':
            target = request.form.get('target')
            extra_limit = int(request.form.get('extra_limit', 0))
            cursor.execute('UPDATE users SET daily_limit = daily_limit + ? WHERE username = ? OR id = ?', (extra_limit, target, target))
            conn.commit()
            success_msg = "Hak başarıyla eklendi!"
            
        elif form_type == 'role':
            target = request.form.get('target_user')
            new_role = request.form.get('new_role')
            cursor.execute('UPDATE users SET role = ? WHERE username = ? OR id = ?', (new_role, target, target))
            conn.commit()
            success_msg = f"Kullanıcı rolü '{new_role}' olarak güncellendi!"

        elif form_type == 'ban':
            target = request.form.get('target_ban')
            ban_status = int(request.form.get('ban_status'))
            cursor.execute('UPDATE users SET is_banned = ? WHERE username = ? OR id = ?', (ban_status, target, target))
            conn.commit()
            success_msg = "Kullanıcı ban durumu güncellendi!"

        elif form_type == 'announcement':
            announcement_text = request.form.get('announcement_text')
            cursor.execute('INSERT INTO announcements (content) VALUES (?)', (announcement_text,))
            conn.commit()
            success_msg = "Duyuru başarıyla yayınlandı!"

    cursor.execute('SELECT * FROM checker_logs ORDER BY id DESC LIMIT 20')
    logs = cursor.fetchall()
    conn.close()
    
    logs_html = ""
    for l in logs:
        logs_html += f"""
        <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); font-size:12px;">
            <td style="padding:6px;">@{l['username']}</td>
            <td style="padding:6px;">{l['gateway']}</td>
            <td style="padding:6px;">{l['masked_card']}</td>
            <td style="padding:6px; color:#10b981; font-weight:bold;">{l['status']}</td>
            <td style="padding:6px; opacity:0.7;">{l['date']}</td>
        </tr>
        """

    admin_html = f"""
    <div style="width:100%; max-width:500px; margin:20px auto; background:var(--input-bg); padding:20px; border-radius:10px; color:var(--text-color); font-family:sans-serif; border:1px solid rgba(239,68,68,0.3);">
        <h3>🛠️ Gelişmiş Admin Paneli</h3>
        
        {f'<div style="background:rgba(16, 185, 129, 0.2); border:1px solid #10b981; padding:8px; border-radius:6px; margin-bottom:10px; color:#6ee7b7; font-size:13px; text-align:center;">{success_msg}</div>' if success_msg else ''}

        <div style="background:rgba(255,255,255,0.03); padding:12px; border-radius:8px; margin-bottom:12px; border:1px solid rgba(255,255,255,0.08);">
            <h4 style="margin:0 0 8px 0; color:#8b5cf6;">➕ Kullanıcıya Hak Ekle</h4>
            <form method="POST">
                <input type="hidden" name="form_type" value="limit">
                <input type="text" name="target" placeholder="Kullanıcı Adı" required style="width:100%; padding:8px; margin:4px 0; background:rgba(255,255,255,0.05); color:inherit; border:1px solid rgba(255,255,255,0.1); border-radius:6px;">
                <input type="number" name="extra_limit" placeholder="Eklenecek Hak (Örn: 500)" required style="width:100%; padding:8px; margin:4px 0; background:rgba(255,255,255,0.05); color:inherit; border:1px solid rgba(255,255,255,0.1); border-radius:6px;">
                <button type="submit" style="width:100%; padding:8px; margin-top:4px; background:#ef4444; color:#fff; border:none; border-radius:6px; font-weight:bold;">Hak Ekle</button>
            </form>
        </div>

        <div style="background:rgba(255,255,255,0.03); padding:12px; border-radius:8px; margin-bottom:12px; border:1px solid rgba(255,255,255,0.08);">
            <h4 style="margin:0 0 8px 0; color:#10b981;">👑 Kullanıcıya VIP / Admin Ver</h4>
            <form method="POST">
                <input type="hidden" name="form_type" value="role">
                <input type="text" name="target_user" placeholder="Kullanıcı Adı" required style="width:100%; padding:8px; margin:4px 0; background:rgba(255,255,255,0.05); color:inherit; border:1px solid rgba(255,255,255,0.1); border-radius:6px;">
                <select name="new_role" style="width:100%; padding:8px; margin:4px 0; background:rgba(255,255,255,0.05); color:inherit; border:1px solid rgba(255,255,255,0.1); border-radius:6px;">
                    <option value="Normal">Normal Üye</option>
                    <option value="VIP">VIP Üye</option>
                    <option value="Admin">Admin</option>
                </select>
                <button type="submit" style="width:100%; padding:8px; margin-top:4px; background:#10b981; color:#fff; border:none; border-radius:6px; font-weight:bold;">Rolü Güncelle</button>
            </form>
        </div>

        <div style="background:rgba(255,255,255,0.03); padding:12px; border-radius:8px; margin-bottom:12px; border:1px solid rgba(255,255,255,0.08);">
            <h4 style="margin:0 0 8px 0; color:#ef4444;">🚫 Kullanıcı Yasaklama (Ban)</h4>
            <form method="POST">
                <input type="hidden" name="form_type" value="ban">
                <input type="text" name="target_ban" placeholder="Kullanıcı Adı" required style="width:100%; padding:8px; margin:4px 0; background:rgba(255,255,255,0.05); color:inherit; border:1px solid rgba(255,255,255,0.1); border-radius:6px;">
                <select name="ban_status" style="width:100%; padding:8px; margin:4px 0; background:rgba(255,255,255,0.05); color:inherit; border:1px solid rgba(255,255,255,0.1); border-radius:6px;">
                    <option value="1">Yasakla (Banla)</option>
                    <option value="0">Yasağı Kaldır</option>
                </select>
                <button type="submit" style="width:100%; padding:8px; margin-top:4px; background:#b91c1c; color:#fff; border:none; border-radius:6px; font-weight:bold;">Uygula</button>
            </form>
        </div>

        <div style="background:rgba(255,255,255,0.03); padding:12px; border-radius:8px; margin-bottom:12px; border:1px solid rgba(255,255,255,0.08);">
            <h4 style="margin:0 0 8px 0; color:#f59e0b;">📢 Genel Duyuru Yayınla</h4>
            <form method="POST">
                <input type="hidden" name="form_type" value="announcement">
                <textarea name="announcement_text" rows="2" placeholder="Duyuru metni..." required style="width:100%; padding:8px; margin:4px 0; background:rgba(255,255,255,0.05); color:inherit; border:1px solid rgba(255,255,255,0.1); border-radius:6px; box-sizing:border-box;"></textarea>
                <button type="submit" style="width:100%; padding:8px; margin-top:4px; background:#f59e0b; color:#000; border:none; border-radius:6px; font-weight:bold;">Yayınla</button>
            </form>
        </div>

        <h4 style="margin:15px 0 5px 0; color:#a78bfa; font-size:14px;">📊 Son Check Logları</h4>
        <div style="max-height: 180px; overflow-y: auto; border: 1px solid rgba(255,255,255,0.1); border-radius: 6px;">
            <div style="overflow-x:auto;">
                <table style="width:100%; border-collapse:collapse; min-width: 350px;">
                    <thead>
                        <tr style="background:rgba(255,255,255,0.05); opacity:0.8; font-size:11px;">
                            <th style="padding:6px; text-align:left;">Kullanıcı</th>
                            <th style="padding:6px; text-align:left;">Gate</th>
                            <th style="padding:6px; text-align:left;">Kart</th>
                            <th style="padding:6px; text-align:left;">Durum</th>
                            <th style="padding:6px; text-align:left;">Tarih</th>
                        </tr>
                    </thead>
                    <tbody>
                        {logs_html if logs_html else '<tr><td colspan="5" style="text-align:center; padding:10px; font-size:12px;">Log bulunamadı.</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>

        <button onclick="location.href='/'" style="width:100%; padding:12px; margin-top:15px; background:#374151; color:#fff; border:none; border-radius:6px; font-weight:bold;">⬅️ Geri Dön</button>
    </div>
    """
    return render_template_string(admin_html)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    t = threading.Thread(target=telegram_bot_listener, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=5000, debug=False)
