from flask import Flask, render_template, jsonify, request
import time

app = Flask(__name__)

# Память сервера
store = {
    "pulse": {
        "btc_price": 0,
        "funding": 0,
        "spot_pct": 0,
        "spot_dir": "WAIT",
        "signal": "WAIT",
        "last_update": 0  # Метка времени для спящей панды
    }
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/update', methods=['POST'])
def update():
    data = request.json
    if data and "pulse" in data:
        store["pulse"] = data["pulse"]
        store["pulse"]["last_update"] = time.time()
        return {"status": "ok"}, 200
    return {"status": "error"}, 400

@app.route('/api/pulse')
def get_pulse():
    # Проверяем, не заснул ли бот (больше 2 минут тишины)
    is_sleeping = (time.time() - store["pulse"]["last_update"]) > 120
    return jsonify({**store["pulse"], "is_sleeping": is_sleeping})

if __name__ == '__main__':
    app.run(debug=True)
