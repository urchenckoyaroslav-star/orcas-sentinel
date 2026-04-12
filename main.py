from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# Повне сховище для всіх даних
store = {
    "pulse": {
        "btc_price": 0,
        "gold_price": 2340.50,
        "silver_price": 28.15,
        "oil_price": 82.40,
        "dxy_index": 104.20,
        "signal": "WAIT",
        "status_code": "SYNC"
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
        # Оновлюємо пульс (ціни ф'ючерсів + сигнал)
        if "pulse" in data:
            store["pulse"].update(data["pulse"])
        # Оновлюємо історію графіка
        if "chart" in data:
            store["chart"] = data["chart"]
        return {"status": "ok"}, 200
    return {"status": "error"}, 400

@app.route('/api/pulse')
def get_pulse():
    return jsonify(store["pulse"])

@app.route('/api/chart_data')
def get_chart():
    return jsonify(store["chart"])

if __name__ == '__main__':
    app.run(debug=True)
