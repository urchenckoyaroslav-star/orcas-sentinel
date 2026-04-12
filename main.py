from flask import Flask, render_template, jsonify, request
import requests
import threading
import time

app = Flask(__name__)

# Сховище даних (об'єднує дані від Оркаса та фонового парсера альткоїнів)
store = {
    "pulse": {
        "btc_price": 0,
        "eth_price": 0,
        "bnb_price": 0,
        "sol_price": 0,
        "xrp_price": 0,
        "doge_price": 0,
        "signal": "WAIT",
        "last_update": 0 # Мітка часу для перевірки на сплячку
    }
}

def fetch_altcoins():
    """Фоновий потік, який тягне ціни 5 монет з Binance Spot API"""
    while True:
        try:
            res = requests.get('https://api.binance.com/api/v3/ticker/price', timeout=3).json()
            # Перетворюємо список у словник для швидкого пошуку
            prices = {item['symbol']: float(item['price']) for item in res}
            
            store["pulse"]["eth_price"] = prices.get('ETHUSDT', 0)
            store["pulse"]["bnb_price"] = prices.get('BNBUSDT', 0)
            store["pulse"]["sol_price"] = prices.get('SOLUSDT', 0)
            store["pulse"]["xrp_price"] = prices.get('XRPUSDT', 0)
            store["pulse"]["doge_price"] = prices.get('DOGEUSDT', 0)
        except Exception as e:
            print(f"Помилка парсингу альткоїнів: {e}")
        
        time.sleep(3) # Оновлюємо кожні 3 секунди

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/update', methods=['POST'])
def update():
    """Сюди бот Оркас надсилає ціну BTC та сигнал світлофора"""
    data = request.json
    if data and "pulse" in data:
        # Оновлюємо лише ті поля, які прислав Оркас
        for key, value in data["pulse"].items():
            store["pulse"][key] = value
        
        store["pulse"]["last_update"] = time.time()
        return {"status": "ok"}, 200
    return {"status": "error"}, 400

@app.route('/api/pulse')
def get_pulse():
    """Віддаємо дані на фронтенд"""
    # Якщо Оркас мовчить більше 120 секунд - вмикаємо сплячу панду
    is_sleeping = (time.time() - store["pulse"]["last_update"]) > 120
    return jsonify({**store["pulse"], "is_sleeping": is_sleeping})

if __name__ == '__main__':
    # Запускаємо фоновий збір цін альткоїнів
    threading.Thread(target=fetch_altcoins, daemon=True).start()
    app.run(debug=True, port=5000)
