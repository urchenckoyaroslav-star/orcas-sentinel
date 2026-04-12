from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# Сховище в пам'яті
store = {
    "pulse": {"btc_price": 0, "signal": "WAIT", "status_code": "SYNC"},
    "chart": []
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/update', methods=['POST'])
def update():
    data = request.json
    if data:
        store["pulse"] = data.get("pulse", store["pulse"])
        store["chart"] = data.get("chart", store["chart"])
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
