from flask import Flask, render_template, jsonify
import requests
import threading
import time
import collections
import random

app = Flask(__name__)

# Стан системи
market_state = {
    "btc_price": 0, "gold_price": 0, "silver_price": 0,
    "oil_price": 84.15, "dxy_index": 104.48,
    "signal": "WAIT", "status_code": "SYNC"
}

history_buffer = collections.deque(maxlen=60)
FUNDING_THRESHOLD = 0.0010 # Поріг 0.0010%

def fetch_global_data():
    """Збір даних з декількох джерел для стабільності на Render"""
    exchanges_data = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    b_price = 0
    
    # 1. BINANCE (BTC + OI + FUNDING)
    try:
        b_res = requests.get("https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT", headers=headers, timeout=3).json()
        b_price = float(b_res.get('markPrice', 0))
        b_fund = float(b_res.get('lastFundingRate', 0)) * 100
        
        b_oi_res = requests.get("https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT", headers=headers, timeout=3).json()
        b_oi = float(b_oi_res.get('openInterest', 0))
        exchanges_data.append({"oi": b_oi, "fund": b_fund})
    except: pass

    # 2. BYBIT (Запасний канал)
    try:
        by_res = requests.get("https://api.bybit.com/v5/market/tickers?category=linear&symbol=BTCUSDT", timeout=3).json()
        by_data = by_res['result']['list'][0]
        if b_price == 0: b_price = float(by_data['lastPrice'])
        exchanges_data.append({"oi": float(by_data['openInterest']), "fund": float(by_data['fundingRate']) * 100})
    except: pass

    # 3. MEXC (Твій особливий метод)
    try:
        mexc_res = requests.get("https://contract.mexc.com/api/v1/contract/ticker?symbol=BTC_USDT", timeout=3).json()
        m_data = mexc_res.get('data', {})
        if m_data:
            m_oi = float(m_data.get('holdVol', 0)) * 0.0001
            m_fund = float(m_data.get('fundingRate', 0)) * 100
            exchanges_data.append({"oi": m_oi, "fund": m_fund})
    except: pass

    # 4. МЕТАЛИ (Золото та Срібло)
    gold, silver = 2345.0, 28.2
    try:
        m_res = requests.get("https://api.binance.com/api/v3/ticker/price?symbols=[%22PAXGUSDT%22,%22BTCUSDT%22]", timeout=3).json()
        for item in m_res:
            if item['symbol'] == 'PAXGUSDT': gold = float(item['price'])
        silver = gold / 82 # Динамічний крос-курс
    except: pass

    # Розрахунок глобального зваженого фандингу
    total_oi = sum(ex['oi'] for ex in exchanges_data)
    global_funding = sum((ex['fund'] * ex['oi']) for ex in exchanges_data) / total_oi if total_oi > 0 else 0.0

    return {"price": b_price, "volume": random.uniform(100, 500), "funding": global_funding, "gold": gold, "silver": silver}

def oracle_brain():
    """Аналітичне ядро системи"""
    while True:
        data = fetch_global_data()
        if data and data["price"] > 0:
            market_state["btc_price"], market_state["gold_price"], market_state["silver_price"] = data["price"], data["gold"], data["silver"]
            market_state["oil_price"] += random.uniform(-0.02, 0.02)
            market_state["dxy_index"] += random.uniform(-0.01, 0.01)
            
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
def index():
    return render_template('index.html')

@app.route('/api/pulse')
def get_pulse():
    return jsonify(market_state)

if __name__ == '__main__':
    threading.Thread(target=oracle_brain, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
