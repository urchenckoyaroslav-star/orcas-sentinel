from flask import Flask, render_template, jsonify, request
import time

app = Flask(__name__)

store = {
    "pulse": {
        "btc_price": 0, "gold_price": 0, "silver_price": 0, "oil_price": 0, "dxy_index": 0,
        "funding": 0, "spot_pct": 0, "spot_dir": "WAIT", "signal": "WAIT", "last_update": 0
    },
    "chart": []
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/update', methods=['POST'])
def update():
    data = request.json
    if data:
        if "pulse" in data:
            store["pulse"].update(data["pulse"])
            store["pulse"]["last_update"] = time.time()
        if "chart" in data:
            store["chart"] = data["chart"]
        return {"status": "ok"}, 200
    return {"status": "error"}, 400

@app.route('/api/pulse')
def get_pulse():
    is_sleeping = (time.time() - store["pulse"]["last_update"]) > 150
    return jsonify({**store["pulse"], "is_sleeping": is_sleeping})

@app.route('/api/chart_data')
def get_chart():
    return jsonify(store["chart"])

if __name__ == '__main__':
    app.run(debug=True)
