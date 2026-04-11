from flask import Flask, render_template, jsonify, request
import threading
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
    "status_code": "SYNC",
    "funding": 0
}

# Поріг фандингу для сигналів (0.0010%)
FUNDING_THRESHOLD = 0.0010

@app.route('/')
def index():
    """Головна сторінка терміналу"""
    return render_template('index.html')

@app.route('/api/pulse')
def get_pulse():
    """Віддача даних на фронтенд (для JavaScript на сайті)"""
    return jsonify(market_state)

@app.route('/api/update', methods=['POST'])
def update_data():
    """
    СЕКРЕТНИЙ ЕНДПОЇНТ ДЛЯ ВАШОГО ЛЕПТОПА (bridge.py)
    Приймає реальні ціни та фандинг.
    """
    data = request.json
    if not data:
        return {"status": "error", "message": "No data received"}, 400

    try:
        # Оновлюємо котирування з payload
        market_state["btc_price"] = data.get("btc", market_state["btc_price"])
        market_state["gold_price"] = data.get("gold", market_state["gold_price"])
        market_state["silver_price"] = data.get("silver", market_state["silver_price"])
        market_state["oil_price"] = data.get("oil", market_state["oil_price"])
        market_state["dxy_index"] = data.get("dxy", market_state["dxy_index"])
        
        # Отримуємо фандинг для розрахунку сигналу
        fund = data.get("fund", 0)
        market_state["funding"] = fund
        
        # --- ЛОГІКА СИГНАЛІВ ПАНДИ ---
        if fund < -FUNDING_THRESHOLD:
            # Негативний фандинг -> Сигнал на ПОКУПКУ (Лонг-сквіз навпаки)
            market_state["signal"] = "BUY"
            market_state["status_code"] = "BUY"
        elif fund > FUNDING_THRESHOLD:
            # Високий позитивний фандинг -> Сигнал на ПРОДАЖ (Ризик дампу)
            market_state["signal"] = "SELL"
            market_state["status_code"] = "SELL"
        else:
            # Фандинг у нормі
            market_state["signal"] = "WAIT"
            market_state["status_code"] = "FLAT"

        print(f"📊 [API UPDATE] BTC: {market_state['btc_price']} | Fund: {fund}% | DXY: {market_state['dxy_index']}")
        return {"status": "success"}, 200

    except Exception as e:
        print(f"❌ Ошибка при обновлении данных: {e}")
        return {"status": "error", "message": str(e)}, 500

if __name__ == '__main__':
    # На Render сервер має слухати на 0.0.0.0
    app.run(host='0.0.0.0', port=5000)
