from flask import Flask, render_template, jsonify, request
import time

app = Flask(__name__)

# Хранилище данных (обновляется ботом)
store = {
    "pulse": {
        "btc_price": 0,
        "gold_price": 2340.50, 
        "silver_price": 28.15,
        "oil_price": 82.40,
        "dxy_index": 104.20,
        "funding": 0.0,
        "spot_pct": 0,
        "spot_dir": "WAIT",
        "signal": "WAIT",
        "last_update": 0
    }
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/update', methods=['POST'])
def update():
    data = request.json
    if data and "pulse" in data:
        store["pulse"].update(data["pulse"])
        store["pulse"]["last_update"] = time.time()
        return {"status": "ok"}, 200
    return {"status": "error"}, 400

@app.route('/api/pulse')
def get_pulse():
    # Если бот не присылал данные больше 2 минут - он спит
    is_sleeping = (time.time() - store["pulse"]["last_update"]) > 120
    return jsonify({**store["pulse"], "is_sleeping": is_sleeping})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
