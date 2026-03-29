from flask import Flask, request, jsonify, render_template
import datetime

app = Flask(__name__)

locations = []

@app.route('/')
def index():
    return render_template("map.html")

@app.route('/track')
def track():
    return render_template("track.html")

@app.route('/save-location', methods=['POST'])
def save_location():
    data = request.json
    locations.append({
        "lat": data["latitude"],
        "lng": data["longitude"],
        "time": str(datetime.datetime.now())
    })
    return jsonify({"status": "ok"})

@app.route('/get-locations')
def get_locations():
    return jsonify(locations)

if __name__ == "__main__":
    app.run()
