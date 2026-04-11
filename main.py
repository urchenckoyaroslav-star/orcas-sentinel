from flask import Flask, render_template, jsonify, request
import threading
import time

app = Flask(__name__)

# Сюда будут прилетать данные с твоего ноута
market_state = {
    "btc_price": 0, "gold_price": 0, "silver_price": 0,
    "oil_price": 84.15, "dxy_index": 105.20,
    "signal": "WAIT", "status_code": "SYNC",
    "funding": 0
}

FUNDING_THRESHOLD = 0.0010

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/pulse')
def get_pulse():
    return jsonify(market_state)

# СЕКРЕТНЫЙ ВХОД ДЛЯ ТВОЕГО НОУТБУКА
@app.route('/api/update', methods=['POST'])
def update_data():
    data = request.json
    try:
        market_state["btc_price"] = data.get("btc", market_state["btc_price"])
        market_state["funding"] = data.get("fund", market_state["funding"])
        market_state["gold_price"] = data.get("gold", market_state["gold_price"])
        market_state["silver_price"] = data.get("silver", market_state["silver_price"])
        market_state["oil_price"] = data.get("oil", market_state["oil_price"])
        
        # Логика сигналов на основе присланного фандинга
        fund = market_state["funding"]
        if fund < -FUNDING_THRESHOLD:
            market_state["signal"], market_state["status_code"] = "BUY", "BUY"
        elif fund > FUNDING_THRESHOLD:
            market_state["signal"], market_state["status_code"] = "SELL", "SELL"
        else:
            market_state["signal"], market_state["status_code"] = "WAIT", "FLAT"
            
        return {"status": "success"}, 200
    except Exception as e:
        return {"status": "error", "message": str(e)}, 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
