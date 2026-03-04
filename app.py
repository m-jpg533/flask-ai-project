from flask import Flask, request, jsonify, render_template
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
DB = "database.db"

# 初始化資料庫
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            latitude REAL,
            longitude REAL,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return "GPS Tracker Running"

# 司機頁面
@app.route("/drive")
def drive():
    return render_template("drive.html")

# 地圖頁面
@app.route("/map")
def map_page():
    return render_template("map.html")

# 接收 GPS
@app.route("/update_location", methods=["POST"])
def update_location():
    data = request.get_json()
    lat = data.get("lat")
    lon = data.get("lon")

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO locations (latitude, longitude, timestamp) VALUES (?, ?, ?)",
        (lat, lon, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

# 取得最新位置
@app.route("/get_location")
def get_location():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT latitude, longitude FROM locations ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    conn.close()

    if row:
        return jsonify({"lat": row[0], "lon": row[1]})
    else:
        return jsonify({"lat": 25.0330, "lon": 121.5654})  # 預設台北

if __name__ == "__main__":
    app.run(debug=True)
