from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# Память сервера: здесь хранятся данные, которые пришлет твой ноутбук
server_data = {
    "pulse": {
        "btc_price": 0.0,
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
def update_data():
    """СЮДА СТУЧИТСЯ ТВОЙ НОУТБУК (bridge.py) И ОТДАЕТ EXCEL-ДАННЫЕ"""
    data = request.json
    if data:
        server_data["pulse"] = data.get("pulse", server_data["pulse"])
        server_data["chart"] = data.get("chart", server_data["chart"])
        return {"status": "success"}, 200
    return {"error": "No data"}, 400

@app.route('/api/pulse')
def pulse():
    """Отдает сайту верхние виджеты и светофор"""
    return jsonify(server_data["pulse"])

@app.route('/api/chart_data')
def chart_data():
    """Отдает сайту неоновые свечи"""
    return jsonify(server_data["chart"])

if __name__ == '__main__':
    app.run(debug=True, port=5000)
