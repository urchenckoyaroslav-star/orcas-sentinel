from flask import Flask, render_template, jsonify
import random
import time

app = Flask(__name__)

# Поточні "фейкові" дані для верхньої панелі та світлофора
current_market_data = {
    "btc_price": 71050.00,
    "gold_price": 2340.50,
    "silver_price": 28.15,
    "oil_price": 82.40,
    "dxy_index": 104.20,
    "signal": "WAIT",     # BUY, SELL, WAIT
    "status_code": "FLAT" # SYNC, BUY, SELL, FLAT, OFFLINE
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/pulse')
def pulse():
    """Пульс системи: оновлює верхні віджети та велику ціну BTC кожні 2 секунди"""
    # Імітація живого ринку
    current_market_data["btc_price"] += random.uniform(-10, 10)
    
    # Випадковий сигнал для світлофора
    rand_sig = random.random()
    if rand_sig > 0.9:
        current_market_data["signal"] = "BUY"
        current_market_data["status_code"] = "BUY"
    elif rand_sig < 0.1:
        current_market_data["signal"] = "SELL"
        current_market_data["status_code"] = "SELL"
    else:
        current_market_data["signal"] = "WAIT"
        current_market_data["status_code"] = "FLAT"

    return jsonify(current_market_data)

@app.route('/api/chart_data')
def chart_data():
    """
    Дані для побудови графіка Lightweight Charts.
    ТУТ ТИ БУДЕШ ЧИТАТИ СВІЙ EXCEL (через pandas).
    Поки генеруємо 60 останніх свічок.
    """
    data = []
    current_time = int(time.time()) - (60 * 15 * 60) # Імітація 15-хвилинного таймфрейму
    base_price = 70000

    for i in range(60):
        open_p = base_price + random.uniform(-50, 50)
        close_p = open_p + random.uniform(-150, 150)
        high_p = max(open_p, close_p) + random.uniform(0, 100)
        low_p = min(open_p, close_p) - random.uniform(0, 100)
        base_price = close_p
        
        # Імітація твоїх історичних сигналів з Excel
        signal = "WAIT"
        rand_val = random.random()
        if rand_val > 0.85:
            signal = "BUY"
        elif rand_val < 0.15:
            signal = "SELL"

        data.append({
            "time": current_time + (i * 15 * 60),
            "open": round(open_p, 2),
            "high": round(high_p, 2),
            "low": round(low_p, 2),
            "close": round(close_p, 2),
            "signal": signal
        })
        
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
