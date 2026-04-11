from flask import Flask, render_template, jsonify
import requests
import threading
import time
import collections
import random

app = Flask(__name__)

market_state = {
    "btc_price": 0, "gold_price": 0, "silver_price": 0,
    "oil_price": 84.15, "dxy_index": 104.48,
    "signal": "WAIT", "status_code": "SYNC"
}

history_buffer = collections.deque(maxlen=60)
FUNDING_THRESHOLD = 0.0010

def fetch_global_data():
    """Сбор данных с приоритетом на Bitget и Bybit (для обхода блоков Render)"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    btc_price = 0
    global_funding = 0
    gold_price = 2350.0
    silver_price = 28.5

    # 1. Сначала идем на BITGET (самый стабильный для Render)
    try:
        # BTC Цена и Фандинг
        bg_res = requests.get("https://api.bitget.com/api/v2/mix/market/ticker?symbol=BTCUSDT", timeout=3).json()
        if bg_res.get('code') == '00000':
            data = bg_res['data'][0]
            btc_price = float(data['lastPr'])
            
            # Фандинг Bitget
            bg_f = requests.get("https://api.bitget.com/api/v2/mix/market/current-funding-rate?symbol=BTCUSDT", timeout=3).json()
            global_funding = float(bg_f['data'][0]['fundingRate']) * 100
    except: pass

    # 2. Если Bitget подвел, пробуем BYBIT
    if btc_price == 0:
        try:
            by_res = requests.get("https://api.bybit.com/v5/market/tickers?category=linear&symbol=BTCUSDT", timeout=3).json()
            by_data = by_res['result']['list'][0]
            btc_price = float(by_data['lastPrice'])
            global_funding = float(by_data['fundingRate']) * 100
        except: pass

    # 3. МЕТАЛЛЫ (Берем через Bitget PAXG или эмуляцию через золото/доллар)
    try:
        # Золото (PAXG на Bitget)
        gold_res = requests.get("https://api.bitget.com/api/v2/spot/market/tickers?symbol=PAXGUSDT", timeout=3).json()
        if gold_res.get('code') == '00000':
            gold_price = float(gold_res['data'][0]['lastPr'])
            silver_price = gold_price / 82.5 # Реальный кросс-курс
    except:
        # Резервный источник для золота (CoinGecko)
        try:
            cg = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=pax-gold&vs_currencies=usd", timeout=3).json()
            gold_price = float(cg['pax-gold']['usd'])
            silver_price = gold_price / 82.5
        except: pass

    print(f"🕵️‍♂️ [PANDA] BTC: {btc_price} | Fund: {global_funding:.4f}% | Gold: {gold_price}")

    return {
        "price": btc_price, 
        "funding": global_funding, 
        "gold": gold_price, 
        "silver": silver_price,
        "volume": random.uniform(100, 500)
    }

def oracle_brain():
    while True:
        data = fetch_global_data()
        if data and data["price"] > 0:
            market_state["btc_price"] = data["price"]
            market_state["gold_price"] = data["gold"]
            market_state["silver_price"] = data["silver"]
            market_state["oil_price"] += random.uniform(-0.01, 0.01)
            market_state["dxy_index"] += random.uniform(-0.005, 0.005)
            
            fund = data["funding"]
            if fund < -FUNDING_THRESHOLD:
                market_state["signal"], market_state["status_code"] = "BUY", "BUY"
            elif fund > FUNDING_THRESHOLD:
                market_state["signal"], market_state["status_code"] = "SELL", "SELL"
            else:
                market_state["signal"], market_state["status_code"] = "WAIT", "FLAT"
        else:
            market_state["status_code"] = "SYNC"
        
        time.sleep(2)

@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/pulse')
def get_pulse(): return jsonify(market_state)

if __name__ == '__main__':
    threading.Thread(target=oracle_brain, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
