# from flask import Flask, render_template, request, jsonify
# import sqlite3
# from datetime import datetime
# import os

# # 如果要接 AI
# from anthropic import Anthropic

# app = Flask(__name__)

# DB = "location.db"

# # 初始化資料庫
# def init_db():
    # conn = sqlite3.connect(DB)
    # c = conn.cursor()
    # c.execute("""
        # CREATE TABLE IF NOT EXISTS locations (
            # id INTEGER PRIMARY KEY AUTOINCREMENT,
            # latitude REAL,
            # longitude REAL,
            # timestamp TEXT
        # )
    # """)
    # conn.commit()
    # conn.close()

# # 首頁
# @app.route("/")
# def index():
    # return render_template("index.html")

# # 查看紀錄
# @app.route("/logs")
# def logs():
    # conn = sqlite3.connect(DB)
    # c = conn.cursor()
    # c.execute("SELECT latitude, longitude, timestamp FROM locations ORDER BY id DESC")
    # data = c.fetchall()
    # conn.close()

    # records = []
    # for lat, lon, ts in data:
        # records.append({
            # "latitude": lat,
            # "longitude": lon,
            # "timestamp": ts
        # })

    # return render_template("logs.html", records=records)

# # 儲存位置
# @app.route("/save-location", methods=["POST"])
# def save_location():
    # data = request.json
    # lat = data["latitude"]
    # lon = data["longitude"]
    # timestamp = datetime.now().isoformat()

    # conn = sqlite3.connect(DB)
    # c = conn.cursor()
    # c.execute("INSERT INTO locations (latitude, longitude, timestamp) VALUES (?, ?, ?)",
              # (lat, lon, timestamp))
    # conn.commit()
    # conn.close()

    # return jsonify({"status": "success"})

# # AI 分析位置（可選）
# @app.route("/ai-analysis")
# def ai_analysis():
    # key = os.environ.get("ANTHROPIC_API_KEY")
    # if not key:
        # return {"error": "沒有設定 AI 金鑰"}

    # client = Anthropic(api_key=key)

    # conn = sqlite3.connect(DB)
    # c = conn.cursor()
    # c.execute("SELECT latitude, longitude, timestamp FROM locations ORDER BY id DESC LIMIT 5")
    # data = c.fetchall()
    # conn.close()

    # text = str(data)

    # msg = client.messages.create(
        # model="claude-3-haiku-20240307",
        # max_tokens=200,
        # messages=[{
            # "role": "user",
            # "content": f"分析這些 GPS 行為是否異常：{text}"
        # }]
    # )

    # return {"result": msg.content[0].text}

# if __name__ == "__main__":
    # init_db()
    # app.run(host="0.0.0.0", port=5000
    
from flask import Flask, render_template, request, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

DB = "location.db"


# ===============================
# 初始化資料庫
# ===============================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


# ===============================
# 驗證座標是否合法
# ===============================
def is_valid_coordinate(lat, lon):
    return -90 <= lat <= 90 and -180 <= lon <= 180


# ===============================
# 首頁
# ===============================
@app.route('/')
def index():
    return render_template('index.html')


# ===============================
# 測試 Flask 是否正常
# ===============================
@app.route('/test')
def test():
    return "Flask 正常運作中 ✅"


# ===============================
# 儲存 GPS 位置
# ===============================
@app.route('/save-location', methods=['POST'])
def save_location():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "沒有收到資料"}), 400

        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if latitude is None or longitude is None:
            return jsonify({"error": "資料格式錯誤"}), 400

        if not is_valid_coordinate(latitude, longitude):
            return jsonify({"error": "座標不合法"}), 400

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute(
            'INSERT INTO locations (latitude, longitude, timestamp) VALUES (?, ?, ?)',
            (latitude, longitude, timestamp)
        )
        conn.commit()
        conn.close()

        return jsonify({"status": "success"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===============================
# 顯示歷史紀錄
# ===============================
@app.route('/logs')
def logs():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''
        SELECT latitude, longitude, timestamp
        FROM locations
        ORDER BY id DESC
    ''')
    data = c.fetchall()
    conn.close()

    records = []
    for lat, lon, ts in data:
        records.append({
            "latitude": lat,
            "longitude": lon,
            "timestamp": ts,
            "valid": is_valid_coordinate(lat, lon)
        })

    return render_template('logs.html', records=records)


# ===============================
# API 方式取得最新位置（給地圖用）
# ===============================
@app.route('/latest')
def latest():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''
        SELECT latitude, longitude, timestamp
        FROM locations
        ORDER BY id DESC
        LIMIT 1
    ''')
    row = c.fetchone()
    conn.close()

    if row:
        return jsonify({
            "latitude": row[0],
            "longitude": row[1],
            "timestamp": row[2]
        })
    else:
        return jsonify({
            "latitude": 25.0330,
            "longitude": 121.5654,
            "timestamp": ""
        })


# ===============================
# 啟動
# ===============================
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)