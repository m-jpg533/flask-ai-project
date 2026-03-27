from flask import Flask, request, jsonify
import requests
import sqlite3
import time
import os
from collections import defaultdict
from dotenv import load_dotenv

# 🔐 載入 .env
load_dotenv()

app = Flask(__name__)

# 🔑 LINE 設定
LINE_TOKEN = os.getenv("LINE_TOKEN")
USER_ID = os.getenv("USER_ID")

#print("TOKEN:", LINE_TOKEN)
#print("USER:", USER_ID)

# 🗄️ 初始化資料庫
def init_db():
    conn = sqlite3.connect("attack.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip TEXT,
        type TEXT,
        detail TEXT,
        time TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# 📊 記錄攻擊
def log_attack(ip, attack_type, detail):
    conn = sqlite3.connect("attack.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO logs (ip, type, detail, time) VALUES (?, ?, ?, datetime('now'))",
        (ip, attack_type, detail)
    )
    conn.commit()
    conn.close()

# 📱 LINE 通知
def send_line(msg):
    if not LINE_TOKEN or not USER_ID:
        print("❗ LINE 未設定")
        return

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": msg}]
    }

    res = requests.post(url, headers=headers, json=data)
    print("LINE狀態碼:", res.status_code)

# 🛡️ 防火牆 & 攻擊偵測
blocked_ips = set()
ip_requests = defaultdict(list)

xss_patterns = ["<script", "javascript:", "onerror", "onload"]
sqli_patterns = ["' or", "--", "union", "select", "drop", "1=1"]

suspicious_paths = ["/admin", "/login", "/phpmyadmin", "/wp-login"]

@app.before_request
def security_layer():
    ip = request.remote_addr
    path = request.path
    query = request.query_string.decode().lower()
    now = time.time()

    # 🔒 已封鎖 IP
    if ip in blocked_ips:
        return "❌ IP已封鎖", 403

    # ======================
    # 🚨 DDoS 防護（單IP）
    # ======================
    ip_requests[ip].append(now)
    ip_requests[ip] = [t for t in ip_requests[ip] if now - t < 5]

    if len(ip_requests[ip]) > 3:
        blocked_ips.add(ip)
        log_attack(ip, "DDoS", "High frequency requests")
        send_line(f"🚨 DDoS攻擊\nIP: {ip}")
        return "Too many requests", 429

    # ======================
    # 🌍 全站流量偵測
    # ======================
    total = sum(len(v) for v in ip_requests.values())
    if total > 100:
        send_line("🚨 疑似DDoS（全站流量暴增）")

    # ======================
    # 💣 XSS 攻擊
    # ======================
    if any(p in query for p in xss_patterns):
        blocked_ips.add(ip)
        log_attack(ip, "XSS", query)
        send_line(f"🚨 XSS攻擊\nIP: {ip}\n內容: {query}")
        return "XSS blocked", 403

    # ======================
    # 💉 SQL Injection
    # ======================
    if any(p in query for p in sqli_patterns):
        blocked_ips.add(ip)
        log_attack(ip, "SQLi", query)
        send_line(f"🚨 SQL Injection\nIP: {ip}\n內容: {query}")
        return "SQLi blocked", 403

    # ======================
    # 🔍 掃描攻擊
    # ======================
    if any(p in path for p in suspicious_paths):
        log_attack(ip, "Scan", path)
        send_line(f"🚨 掃描攻擊\nIP: {ip}\nPath: {path}")

# 🏠 首頁
@app.route("/")
def home():
    return "🛡️ 安全監控系統運作中"

# 🧪 測試攻擊
@app.route("/test/admin")
def test():
    return "測試路徑"

# 📊 查看攻擊紀錄
@app.route("/logs")
def logs():
    conn = sqlite3.connect("attack.db")
    c = conn.cursor()
    c.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()
    return jsonify(rows)

#if __name__ == "__main__":
    
    #app.run(port=50000, debug=True)
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
