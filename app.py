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

# Render dış adresini otomatik alır
WEB_APP_URL = os.environ.get('RENDER_EXTERNAL_URL', '')
TELEGRAM_BOT_TOKEN = "8692317800:AAGhN5UEe5Efycth5P6JqvNQ6xAja7D2P7M"
ZORUNLU_KANAL = "@JustRealLog"

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
        admin_mail = "JustRealAdmin@gmail.com"
        admin_pass = "JustRealAdminPanel2026!Orj#"
        admin_user = "JustReal"
        
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, email, password, profile_pic, role, daily_limit, total_lives, is_banned) 
            VALUES (?, ?, ?, 'https://i.imgur.com/6VBx3io.png', 'Admin', 999999, 100, 0)
        ''', (admin_user, admin_mail, admin_pass))
        
        cursor.execute("UPDATE users SET username = ?, role = 'Admin', password = ?, daily_limit = 999999 WHERE email = ?", (admin_user, admin_pass, admin_mail))
        conn.commit()
    except:
        pass
        
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
    CHANNEL_ID = "@JustRealLog"
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

def setup_webhook():
    if WEB_APP_URL:
        webhook_url = f"{WEB_APP_URL}/webhook"
        try:
            requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={webhook_url}", timeout=5)
        except:
            pass

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error"}), 400

    try:
        if "callback_query" in data:
            cq = data["callback_query"]
            chat_id = cq["message"]["chat"]["id"]
            user_id = cq["from"]["id"]
            callback_data = cq.get("data")
            query_id = cq["id"]
            
            if callback_data == "check_membership":
                is_member = check_user_channel_membership(user_id)
                answer_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
                
                if is_member:
                    requests.post(answer_url, json={"callback_query_id": query_id, "text": "✅ Tebrikler, kanal üyeliğiniz doğrulandı!", "show_alert": True})
                    welcome_msg = (
                        "🎉 **Üyelik Başarıyla Doğrulandı!**\n\n"
                        "🚀 **JustReal Multi-Checker** sistemine tam erişim hakkı kazandın. Paneli açmak için aşağıdaki butonu kullanabilirsin."
                    )
                    keyboard = {
                        "inline_keyboard": [
                            [{"text": "🚀 Paneli Aç (Mini App)", "web_app": {"url": WEB_APP_URL}}],
                            [{"text": "🌐 Web Sitesi Olarak Aç", "url": WEB_APP_URL}]
                        ]
                    }
                    edit_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText"
                    requests.post(edit_url, json={"chat_id": chat_id, "message_id": cq["message"]["message_id"], "text": welcome_msg, "parse_mode": "Markdown", "reply_markup": keyboard})
                else:
                    requests.post(answer_url, json={"callback_query_id": query_id, "text": "❌ Henüz kanala katılmamışsın! Lütfen önce kanala katıl.", "show_alert": True})

        if "message" in data:
            message = data["message"]
            if "text" in message:
                chat_id = message["chat"]["id"]
                user_id = message["from"]["id"]
                text = message["text"]
                user_name = message["from"].get("first_name", "Kullanıcı")
                
                if text.startswith("/start"):
                    is_member = check_user_channel_membership(user_id)
                    send_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                    
                    if not is_member:
                        welcome_msg = (
                            f"👋 Merhaba {user_name}!\n\n"
                            f"🚨 **JustReal Multi-Checker** sistemini kullanabilmek için öncelikle resmi kanalımıza ({ZORUNLU_KANAL}) katılman gerekmektedir.\n\n"
                            "👉 Katıldıktan sonra aşağıdaki **'✅ Katıldım / Kontrol Et'** butonuna basarak sistem kilidini açabilirsin."
                        )
                        keyboard = {
                            "inline_keyboard": [
                                [{"text": "📢 Kanala Katıl", "url": f"https://t.me/{ZORUNLU_KANAL.replace('@', '')}"}],
                                [{"text": "✅ Katıldım / Kontrol Et", "callback_data": "check_membership"}]
                            ]
                        }
                    else:
                        welcome_msg = (
                            f"👋 Merhaba {user_name}!\n\n"
                            "🚀 **JustReal Multi-Checker** sistemine hoş geldin.\n\n"
                            "Aşağıdaki butona tıklayarak güvenli web panelini açabilir ve kart check edebilirsin."
                        )
                        keyboard = {
                            "inline_keyboard": [
                                [{"text": "🚀 Paneli Aç (Mini App)", "web_app": {"url": WEB_APP_URL}}],
                                [{"text": "🌐 Web Sitesi Olarak Aç", "url": WEB_APP_URL}]
                            ]
                        }
                        
                    requests.post(send_url, json={"chat_id": chat_id, "text": welcome_msg, "parse_mode": "Markdown", "reply_markup": keyboard})
    except Exception as e:
        print(f"Webhook hata: {e}")

    return jsonify({"status": "ok"}), 200

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
            --card-bg: rgba(18, 24, 38, 0.85);
            --text-color: #fff;
            --border-col: rgba(255,255,255,0.12);
            --input-bg: #121826;
        }
        [data-theme="light"] {
            --bg-grad: linear-gradient(135deg, #f3f4f6, #e5e7eb);
            --card-bg: rgba(255, 255, 255, 0.9);
            --text-color: #1f2937;
            --border-col: rgba(0,0,0,0.1);
            --input-bg: #ffffff;
        }
        * { box-sizing: border-box; }
        body { 
            background: var(--bg-grad); 
            color: var(--text-color); 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
            margin:0; 
            padding:10px; 
            min-height: 100vh; 
            display: flex; 
            justify-content: center; 
            align-items: flex-start;
            position: relative;
            overflow-x: hidden;
        }
        .container { width: 100%; max-width: 520px; margin: auto; position: relative; padding-bottom: 25px; }
        .top-right-logo { position: absolute; top: 12px; right: 15px; font-weight: 900; color: #8b5cf6; font-size: 18px; z-index: 10; }
        .card { background: var(--card-bg); backdrop-filter: blur(10px); padding: 16px; border-radius: 14px; margin-bottom: 14px; border: 1px solid var(--border-col); }
        input, select, textarea, button { width: 100%; padding: 12px; margin: 6px 0; background: var(--input-bg); border: 1px solid var(--border-col); color: var(--text-color); border-radius: 8px; font-size: 14px; }
        button { background: #8b5cf6; font-weight: bold; cursor: pointer; border: none; color: #fff; }
        .badge-normal { background: #10b981; color: #fff; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; }
        .badge-vip { background: #f59e0b; color: #000; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; }
        .badge-admin { background: #ef4444; color: #fff; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; }
        .error-box { background: rgba(239, 68, 68, 0.2); border: 1px solid #ef4444; padding: 10px; border-radius: 8px; color: #fca5a5; font-size: 13px; text-align: center; margin-bottom: 10px; }
        .announcement-box { background: rgba(245, 158, 11, 0.15); border: 1px solid #f59e0b; padding: 10px; border-radius: 8px; color: #fde68a; font-size: 13px; margin-bottom: 12px; }
        .stats-grid { display: flex; justify-content: space-between; gap: 8px; margin-bottom: 14px; }
        .stat-card { background: rgba(139, 92, 246, 0.12); border: 1px solid rgba(139, 92, 246, 0.3); flex: 1; padding: 10px 6px; border-radius: 10px; text-align: center; }
        .stat-card h5 { margin: 0 0 3px 0; color: #a78bfa; font-size: 11px; }
        .stat-card span { font-size: 15px; font-weight: bold; }
        .avatar-img { width: 50px; height: 50px; border-radius: 50%; object-fit: cover; border: 2px solid #8b5cf6; }
        .live-feed { max-height: 85px; overflow-y: auto; font-size: 11px; background: rgba(0,0,0,0.15); padding: 8px; border-radius: 6px; color: #10b981; }
        .wide-check-card { width: 100%; padding: 18px; background: var(--card-bg); border-radius: 14px; border: 1px solid rgba(139, 92, 246, 0.4); }
        .wide-check-card textarea { width: 100%; min-height: 110px; resize: vertical; }
        #toast { visibility: hidden; min-width: 220px; background-color: #10b981; color: #fff; text-align: center; border-radius: 8px; padding: 12px; position: fixed; left: 50%; transform: translateX(-50%); bottom: 20px; font-weight: bold; z-index: 1000; font-size: 13px; }
        #toast.show { visibility: visible; animation: fadein 0.5s, fadeout 0.5s 2.5s; }
        @keyframes fadein { from {bottom: 0; opacity: 0;} to {bottom: 20px; opacity: 1;} }
        @keyframes fadeout { from {bottom: 20px; opacity: 1;} to {bottom: 0; opacity: 0;} }
    </style>
</head>
<body data-theme="{{ session.get('user', {}).get('theme', 'dark') }}">
    <div class="top-right-logo">JustReal</div>
    <div class="container">
        <div style="height: 10px;"></div>

        {% if not session.get('user') %}
            <div class="card">
                <h3 style="margin-top:0; text-align:center; font-size:18px;">Giriş Yap / Kayıt Ol</h3>
                <form method="POST" action="/auth">
                    <label style="font-size:13px;">Gmail veya Kullanıcı Adı:</label>
                    <input type="text" name="email_or_username" placeholder="JustReal veya eposta@com" required>
                    <label style="font-size:13px;">Şifre:</label>
                    <input type="password" name="password" placeholder="••••••••" required>
                    <button type="submit" name="action" value="login">🚀 Giriş Yap</button>
                    <button type="submit" name="action" value="register" style="background:#3b82f6;">📝 Kayıt Ol</button>
                </form>
            </div>
        {% else %}
            <div class="card" style="border: 1px solid rgba(139,92,246,0.4);">
                <div style="display:flex; align-items:center; gap:12px;">
                    <img src="{{ session['user']['profile_pic'] }}" class="avatar-img" alt="Avatar">
                    <div style="flex-grow:1; min-width: 0;">
                        <div style="display:flex; justify-content:space-between; align-items:center; gap: 5px;">
                            <span style="font-weight:bold; font-size:16px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">@{{ session['user']['username'] }}</span>
                            {% if session['user']['role'] == 'Admin' %}
                                <span class="badge-admin">ADMİN</span>
                            {% elif session['user']['role'] == 'VIP' %}
                                <span class="badge-vip">VİP</span>
                            {% else %}
                                <span class="badge-normal">NORMAL</span>
                            {% endif %}
                        </div>
                        <p style="margin:5px 0 0 0; font-size:12px; opacity: 0.8;">⚡ Günlük Hak: {{ session['user']['used_today'] }} / {{ session['user']['daily_limit'] }}</p>
                    </div>
                </div>
            </div>

            <div class="stats-grid">
                <div class="stat-card"><h5>👥 Üyeler</h5><span>{{ stats.total_users }}</span></div>
                <div class="stat-card"><h5>💎 Toplam Live</h5><span>{{ stats.total_lives }}</span></div>
                <div class="stat-card"><h5>🟢 Aktif / Gün</h5><span>{{ stats.active_today }}</span></div>
            </div>

            {% if error %}
                <div class="error-box">{{ error }}</div>
            {% endif %}

            {% if latest_announcement %}
                <div class="announcement-box">📢 <b>Admin Duyurusu:</b><br>{{ latest_announcement }}</div>
            {% endif %}

            <div class="card" style="padding: 10px;">
                <div style="font-size:12px; font-weight:bold; margin-bottom:5px; color:#a78bfa;">⚡ Son Global Live Kart Akışı</div>
                <div class="live-feed">
                    {% for feed in live_feeds %}
                        <div>🟢 @{{ feed.username }} [{{ feed.gateway}}] -> <b>{{ feed.masked_card }}</b></div>
                    {% else %}
                        <div>Henüz sistemde canlı live kart akışı yok.</div>
                    {% endfor %}
                </div>
            </div>

            <div class="card">
                <div style="font-size:12px; font-weight:bold; margin-bottom:8px; color:#a78bfa;">📂 Hızlı Menü & Seçenekler</div>
                <button onclick="location.href='/bin-tool'">🔍 Bin Kontrol Aracı</button>
                <button onclick="location.href='/cc-cleaner'" style="background:#3b82f6;">🧹 CC Temizleyici (Cleaner)</button>
                <button onclick="location.href='/leaderboard'" style="background:#f59e0b; color:#000;">👑 En İyiler Listesi</button>
                <button onclick="location.href='/profile'" style="background:#6366f1;">👤 Profil & Tema Ayarları</button>
                {% if session['user']['role'] == 'Admin' %}
                    <button onclick="location.href='/admin'" style="background:#ef4444;">⚙️ Admin Paneli</button>
                {% endif %}
                <button onclick="location.href='/logout'" style="background:#374151; margin-top:4px;">Çıkış Yap</button>
            </div>

            <div class="wide-check-card">
                <form method="POST" action="/run-check" id="checkForm" onsubmit="return handleCheckSubmit()">
                    <label style="font-size:13px; font-weight:bold; color:#a78bfa;">Gateway Seçimi:</label>
                    <select name="gateway">
                        <option value="Auth Gate">🌐 Auth Gate</option>
                        <option value="Puan Gate">💳 Puan Gate</option>
                        <option value="Shopify Gate">🔄 Shopify Gate</option>
                    </select>
                    
                    <label style="font-size:13px; font-weight:bold; margin-top:8px; display:block; color:#a78bfa;">Kartları Yapıştır (CC|MM|YY|CVV):</label>
                    <textarea name="cards" placeholder="453210|12|28|123" required style="font-family:monospace;"></textarea>
                    <button type="submit" id="checkBtn" style="margin-top:10px; font-size:15px; padding:14px;">🚀 Check Başlat</button>
                </form>
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
    stats = {"total_users": total_users, "total_lives": total_lives, "active_today": active_today}
    return render_template_string(HTML_TEMPLATE, error=error, latest_announcement=latest_announcement, stats=stats, live_feeds=live_feeds)

@app.route('/auth', methods=['POST'])
def auth():
    action = request.form.get('action')
    input_val = request.form.get('email_or_username', '').strip()
    password = request.form.get('password', '')
    
    if not input_val or not password:
        return redirect(url_for('index', error="Boş alan bıraktın, lütfen doldur!"))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if action == 'register':
            cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (input_val, input_val))
            existing = cursor.fetchone()
            if existing:
                conn.close()
                return redirect(url_for('index', error="Bu kullanıcı adı veya e-posta zaten sistemde kayıtlı!"))
            
            default_avatar = "https://i.imgur.com/6VBx3io.png"
            email_to_save = input_val if "@" in input_val else f"{input_val}@user.com"
            username_to_save = input_val.split('@')[0] if "@" in input_val else input_val
            
            cursor.execute('''
                INSERT INTO users (username, email, password, profile_pic, role, daily_limit, total_lives, total_checks, is_banned, theme) 
                VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0, ?)
            ''', (username_to_save, email_to_save, password, default_avatar, 'Normal', 1500, 'dark'))
            conn.commit()
            
            cursor.execute('SELECT * FROM users WHERE id = ?', (cursor.lastrowid,))
            user = cursor.fetchone()
            session['user'] = dict(user)
            conn.close()
            return redirect(url_for('index'))
            
        elif action == 'login':
            cursor.execute('SELECT * FROM users WHERE (username = ? OR email = ?) AND password = ?', (input_val, input_val, password))
            user = cursor.fetchone()
            
            if user:
                if user['is_banned'] == 1:
                    conn.close()
                    return redirect(url_for('index', error="Hesabın sistem yöneticisi tarafından yasaklanmış!"))
                session['user'] = dict(user)
                conn.close()
                return redirect(url_for('index'))
            else:
                conn.close()
                return redirect(url_for('index', error="Giriş Başarısız! Kullanıcı adı veya şifre hatalı."))
                
    except Exception as e:
        conn.close()
        return redirect(url_for('index', error=f"İşlem sırasında hata oluştu: {str(e)}"))
    
    conn.close()
    return redirect(url_for('index'))

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
            cursor.execute('INSERT INTO checker_logs (username, gateway, masked_card, status) VALUES (?, ?, ?, ?)', (username, gateway, masked_cc, 'LIVE'))
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
                    bin_result = f"BIN: {clean_bin} | Tür: {data.get('scheme','?').upper()} | Marka: {data.get('brand','?')} | Banka: {data.get('bank',{}).get('name','?')} | Ülke: {data.get('country',{}).get('name','?')}"
                else:
                    bin_result = f"BIN: {clean_bin} detay bulunamadı."
            except:
                bin_result = f"BIN: {clean_bin} (Servis yoğun)"
    
    bin_html = """
    <div style="width:100%; max-width:480px; margin:20px auto; background:var(--input-bg); padding:20px; border-radius:10px; color:var(--text-color); font-family:sans-serif; border:1px solid rgba(139,92,246,0.3);">
        <h3>🔍 Bin Kontrol Aracı</h3>
        <form method="POST">
            <input type="text" name="bin_code" placeholder="453210" maxlength="19" required style="width:100%; padding:10px; margin:5px 0;">
            <button type="submit" style="width:100%; padding:12px; margin-top:10px; background:#8b5cf6; color:#fff; border:none; border-radius:6px; font-weight:bold;">🔍 BIN Sorgula</button>
        </form>
        {% if bin_result %}<div style="background:rgba(139,92,246,0.1); border:1px solid #8b5cf6; padding:10px; border-radius:6px; margin-top:10px; font-size:13px;">{{ bin_result }}</div>{% endif %}
        <button onclick="location.href='/'" style="width:100%; padding:12px; margin-top:15px; background:#374151; color:#fff; border:none; border-radius:6px; font-weight:bold;">⬅️ Ana Menü</button>
    </div>
    """
    return render_template_string(bin_html, bin_result=bin_result)

@app.route('/cc-cleaner', methods=['GET', 'POST'])
def cc_cleaner():
    if 'user' not in session:
        return redirect(url_for('index'))
    cleaned_output = ""
    if request.method == 'POST':
        lines = request.form.get('raw_text', '').split('\n')
        valid = []
        for l in lines:
            p = l.replace(';', '|').replace(':', '|').replace(',', '|').split('|')
            if len(p) >= 4 and p[0].strip().isdigit() and p[1].strip().isdigit() and p[2].strip().isdigit() and p[3].strip().isdigit():
                valid.append(f"{p[0].strip()}|{p[1].strip()}|{p[2].strip()}|{p[3].strip()}")
        cleaned_output = "\n".join(valid)
        
    cleaner_html = """
    <div style="width:100%; max-width:480px; margin:20px auto; background:var(--input-bg); padding:20px; border-radius:10px; color:var(--text-color); font-family:sans-serif; border:1px solid rgba(59,130,246,0.3);">
        <h3>🧹 CC Temizleyici</h3>
        <form method="POST">
            <textarea name="raw_text" rows="5" placeholder="Karışık liste..." required style="width:100%; padding:10px; font-family:monospace;"></textarea>
            <button type="submit" style="width:100%; padding:12px; margin-top:5px; background:#3b82f6; color:#fff; border:none; border-radius:6px; font-weight:bold;">🧹 Temizle</button>
        </form>
        {% if request.method == 'POST' %}
            <textarea rows="5" readonly style="width:100%; padding:10px; margin-top:10px; background:rgba(0,0,0,0.2); color:#10b981; font-family:monospace;">{{ cleaned_output }}</textarea>
        {% endif %}
        <button onclick="location.href='/'" style="width:100%; padding:12px; margin-top:15px; background:#374151; color:#fff; border:none; border-radius:6px; font-weight:bold;">⬅️ Ana Menü</button>
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
    
    rows = "".join([f"<tr><td style='padding:8px;'>@{r['username']}</td><td style='padding:8px; text-align:center;'>{r['role']}</td><td style='padding:8px; text-align:center; color:#10b981;'>{r['total_lives']} Live</td></tr>" for r in top_users])
    lb_html = f"""
    <div style="width:100%; max-width:480px; margin:20px auto; background:var(--input-bg); padding:20px; border-radius:10px; color:var(--text-color); font-family:sans-serif; border:1px solid rgba(245,158,11,0.3);">
        <h3 style="text-align:center;">👑 En İyiler Listesi</h3>
        <table style="width:100%; border-collapse:collapse; margin-top:10px;">{rows}</table>
        <button onclick="location.href='/'" style="width:100%; padding:12px; margin-top:20px; background:#374151; color:#fff; border:none; border-radius:6px; font-weight:bold;">⬅️ Ana Menü</button>
    </div>
    """
    return render_template_string(lb_html)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    msg = None
    if request.method == 'POST':
        cursor.execute('UPDATE users SET username = ?, email = ?, profile_pic = ?, theme = ? WHERE id = ?', 
                       (request.form.get('username'), request.form.get('email'), request.form.get('profile_pic'), request.form.get('theme'), session['user']['id']))
        conn.commit()
        cursor.execute('SELECT * FROM users WHERE id = ?', (session['user']['id'],))
        session['user'] = dict(cursor.fetchone())
        msg = "Güncellendi!"
    conn.close()
    
    u = session['user']
    
    p_html = """
    <div style="width:100%; max-width:450px; margin:20px auto; background:var(--input-bg); padding:20px; border-radius:10px; color:var(--text-color); font-family:sans-serif; border:1px solid rgba(99,102,241,0.3);">
        <h3>👤 Profil & Ayarlar</h3>
        {% if msg %}<p style="color:#6ee7b7; font-size:13px;">{{ msg }}</p>{% endif %}
        <form method="POST">
            <label>Kullanıcı Adı:</label><input type="text" name="username" value="{{ u.username }}" required style="width:100%; padding:10px; margin:4px 0;">
            <label>Gmail Adresi:</label><input type="email" name="email" value="{{ u.email }}" required style="width:100%; padding:10px; margin:4px 0;">
            <label>Avatar URL:</label><input type="url" name="profile_pic" value="{{ u.profile_pic }}" required style="width:100%; padding:10px; margin:4px 0;">
            <label>Tema:</label>
            <select name="theme" style="width:100%; padding:10px; margin:4px 0;">
                <option value="dark" {% if u.theme == 'dark' %}selected{% endif %}>Dark</option>
                <option value="light" {% if u.theme == 'light' %}selected{% endif %}>Light</option>
            </select>
            <button type="submit" style="width:100%; padding:12px; margin-top:10px; background:#6366f1; color:#fff; border:none; border-radius:6px; font-weight:bold;">💾 Kaydet</button>
        </form>
        <button onclick="location.href='/'" style="width:100%; padding:12px; margin-top:10px; background:#374151; color:#fff; border:none; border-radius:6px; font-weight:bold;">⬅️ Ana Menü</button>
    </div>
    """
    return render_template_string(p_html, u=u, msg=msg)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user' not in session or session['user']['role'] != 'Admin':
        return "Yetkisiz Erişim!", 403
    conn = get_db_connection()
    cursor = conn.cursor()
    msg = None
    if request.method == 'POST':
        ft = request.form.get('form_type')
        if ft == 'limit':
            cursor.execute('UPDATE users SET daily_limit = daily_limit + ? WHERE username = ? OR id = ?', (int(request.form.get('extra_limit', 0)), request.form.get('target'), request.form.get('target')))
            conn.commit()
            msg = "Hak eklendi!"
        elif ft == 'role':
            cursor.execute('UPDATE users SET role = ? WHERE username = ? OR id = ?', (request.form.get('new_role'), request.form.get('target_user'), request.form.get('target_user')))
            conn.commit()
            msg = "Rol güncellendi!"
        elif ft == 'ban':
            cursor.execute('UPDATE users SET is_banned = ? WHERE username = ? OR id = ?', (int(request.form.get('ban_status')), request.form.get('target_ban'), request.form.get('target_ban')))
            conn.commit()
            msg = "Ban durumu değiştirildi!"
        elif ft == 'announcement':
            cursor.execute('INSERT INTO announcements (content) VALUES (?)', (request.form.get('announcement_text'),))
            conn.commit()
            msg = "Duyuru yayınlandı!"

    cursor.execute('SELECT * FROM checker_logs ORDER BY id DESC LIMIT 15')
    logs = cursor.fetchall()
    conn.close()
    
    rows = "".join([f"<tr style='font-size:12px;'><td style='padding:6px;'>@{l['username']}</td><td style='padding:6px;'>{l['gateway']}</td><td style='padding:6px;'>{l['masked_card']}</td><td style='padding:6px; color:#10b981;'>{l['status']}</td></tr>" for l in logs])
    
    admin_html = """
    <div style="width:100%; max-width:500px; margin:20px auto; background:var(--input-bg); padding:20px; border-radius:10px; color:var(--text-color); font-family:sans-serif; border:1px solid rgba(239,68,68,0.3);">
        <h3>🛠️ Admin Paneli</h3>
        {% if msg %}<div style="background:rgba(16,185,129,0.2); padding:8px; border-radius:6px; color:#6ee7b7; font-size:13px; text-align:center; margin-bottom:10px;">{{ msg }}</div>{% endif %}
        
        <div style="background:rgba(255,255,255,0.03); padding:10px; border-radius:8px; margin-bottom:10px;">
            <h4 style="margin:0 0 5px 0; color:#8b5cf6; font-size:13px;">➕ Hak Ekle</h4>
            <form method="POST">
                <input type="hidden" name="form_type" value="limit">
                <input type="text" name="target" placeholder="Kullanıcı Adı" required style="width:100%; padding:8px; margin:3px 0;">
                <input type="number" name="extra_limit" placeholder="Hak Miktarı" required style="width:100%; padding:8px; margin:3px 0;">
                <button type="submit" style="width:100%; padding:8px; background:#ef4444; color:#fff; border:none; border-radius:6px; font-weight:bold;">Ekle</button>
            </form>
        </div>

        <div style="background:rgba(255,255,255,0.03); padding:10px; border-radius:8px; margin-bottom:10px;">
            <h4 style="margin:0 0 5px 0; color:#10b981; font-size:13px;">👑 Rol Ver</h4>
            <form method="POST">
                <input type="hidden" name="form_type" value="role">
                <input type="text" name="target_user" placeholder="Kullanıcı Adı" required style="width:100%; padding:8px; margin:3px 0;">
                <select name="new_role" style="width:100%; padding:8px; margin:3px 0;"><option value="Normal">Normal</option><option value="VIP">VIP</option><option value="Admin">Admin</option></select>
                <button type="submit" style="width:100%; padding:8px; background:#10b981; color:#fff; border:none; border-radius:6px; font-weight:bold;">Güncelle</button>
            </form>
        </div>

        <div style="background:rgba(255,255,255,0.03); padding:10px; border-radius:8px; margin-bottom:10px;">
            <h4 style="margin:0 0 5px 0; color:#f59e0b; font-size:13px;">📢 Duyuru</h4>
            <form method="POST">
                <input type="hidden" name="form_type" value="announcement">
                <textarea name="announcement_text" rows="2" placeholder="Duyuru..." required style="width:100%; padding:8px; margin:3px 0;"></textarea>
                <button type="submit" style="width:100%; padding:8px; background:#f59e0b; color:#000; border:none; border-radius:6px; font-weight:bold;">Yayınla</button>
            </form>
        </div>

        <h4 style="margin:10px 0 5px 0; color:#a78bfa; font-size:13px;">📊 Son Loglar</h4>
        <div style="max-height:150px; overflow-y:auto; border:1px solid rgba(255,255,255,0.1); border-radius:6px;">
            <table style="width:100%; border-collapse:collapse;">%s</table>
        </div>

        <button onclick="location.href='/'" style="width:100%; padding:12px; margin-top:15px; background:#374151; color:#fff; border:none; border-radius:6px; font-weight:bold;">⬅️ Ana Menü</button>
    </div>
    """ % rows
    return render_template_string(admin_html, msg=msg)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    setup_webhook()
    app.run(host='0.0.0.0', port=5000, debug=False)
