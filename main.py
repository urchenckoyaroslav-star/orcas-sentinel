from flask import Flask, render_template, jsonify, request
import time

app = Flask(__name__)

# --- ЦЕНТРАЛЬНЕ СХОВИЩЕ ДАНИХ (PANDA STATE) ---
market_state = {
    "btc_price": 0,
    "gold_price": 0,
    "silver_price": 0,
    "oil_price": 0,
    "dxy_index": 105.20,
    "signal": "WAIT",
    "status_code": "OFFLINE", # Початковий статус тепер завжди OFFLINE
    "funding": 0,
    "last_update": 0 
}

# Поріг фандингу
FUNDING_THRESHOLD = 0.0010

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/pulse')
def get_pulse():
    # Якщо даних немає взагалі (0) або вони старі (> 180 сек) — Панда спить
    now = time.time()
    if market_state["last_update"] == 0 or (now - market_state["last_update"] > 180):
        market_state["status_code"] = "OFFLINE"
    
    return jsonify(market_state)

@app.route('/api/update', methods=['POST'])
def update_data():
    data = request.json
    if not data:
        return {"status": "error", "message": "No data received"}, 400

    try:
        market_state["btc_price"] = data.get("btc", market_state["btc_price"])
        market_state["gold_price"] = data.get("gold", market_state["gold_price"])
        market_state["silver_price"] = data.get("silver", market_state["silver_price"])
        market_state["oil_price"] = data.get("oil", market_state["oil_price"])
        market_state["dxy_index"] = data.get("dxy", market_state["dxy_index"])
        
        fund = data.get("fund", 0)
        market_state["funding"] = fund
        market_state["last_update"] = time.time() 
        
        # Визначаємо статус на основі фандингу
        if fund < -FUNDING_THRESHOLD:
            market_state["signal"], market_state["status_code"] = "BUY", "BUY"
        elif fund > FUNDING_THRESHOLD:
            market_state["signal"], market_state["status_code"] = "SELL", "SELL"
        else:
            market_state["signal"], market_state["status_code"] = "WAIT", "FLAT"

        return {"status": "success"}, 200

    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
