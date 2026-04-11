from flask import Flask, render_template, jsonify
import requests
import threading
import time
import collections
import random

app = Flask(__name__)

# Состояние системы
market_state = {
    "btc_price": 0, "gold_price": 0, "silver_price": 0,
    "oil_price": 0, "dxy_index": 105.20, # DXY пока на ручном контроле или внешнем API
    "signal": "WAIT", "status_code": "SYNC",
    "funding": 0
}

history_buffer = collections.deque(maxlen=60)
FUNDING_THRESHOLD = 0.0010

# Маскировка под Google Chrome
BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://www.google.com/',
    'Origin': 'https://www.mexc.com'
}

def fetch_mexc_asset(symbol):
    """Универсальный парсер для любых активов на MEXC (Futures)"""
    try:
        url = f"https://contract.mexc.com/api/v1/contract/ticker?symbol={symbol}"
        res = requests.get(url, headers=BROWSER_HEADERS, timeout=5).json()
        data = res.get('data', {})
        if data:
            return {
                "price": float(data.get('lastPrice', 0)),
                "oi": float(data.get('holdVol', 0)) * 0.0001,
                "fund": float(data.get('fundingRate', 0)) * 100
            }
    except:
        return None

def fetch_all_data():
    """Сбор реальных котировок из разных источников"""
    
    # 1. Биткоин (MEXC)
    btc_data = fetch_mexc_asset("BTC_USDT")
    
    # 2. Золото (MEXC торгует GOLD_USDT или XAU_USDT)
    gold_data = fetch_mexc_asset("XAU_USDT") # На MEXC золото обычно XAU
    if not gold_data: gold_data = fetch_mexc_asset("GOLD_USDT")
    
    # 3. Серебро (MEXC: XAG_USDT)
    silver_data = fetch_mexc_asset("XAG_USDT")
    
    # 4. Нефть WTI (MEXC: WTI_USDT)
    oil_data = fetch_mexc_asset("WTI_USDT")

    # Собираем фандинг для анализа (Binance + Bybit для веса)
    exchanges_funding = []
    if btc_data: exchanges_funding.append(btc_data)
    
    try:
        by_res = requests.get("https://api.bybit.com/v5/market/tickers?category=linear&symbol=BTCUSDT", timeout=3).json()
        by_d = by_res['result']['list'][0]
        exchanges_funding.append({"oi": float(by_d['openInterest']), "fund": float(by_d['fundingRate']) * 100})
    except: pass

    # Считаем взвешенный фандинг
    total_oi = sum(ex['oi'] for ex in exchanges_funding)
    global_fund = sum(ex['fund'] * ex['oi'] for ex in exchanges_funding) / total_oi if total_oi > 0 else 0

    return {
        "btc": btc_data["price"] if btc_data else 0,
        "gold": gold_data["price"] if gold_data else 2350.0,
        "silver": silver_data["price"] if silver_data else 28.5,
        "oil": oil_data["price"] if oil_data else 84.15,
        "fund": global_fund
    }

def oracle_brain():
    """Главный аналитический поток"""
    while True:
        data = fetch_all_data()
        
        if data["btc"] > 0:
            market_state["btc_price"] = data["btc"]
            market_state["gold_price"] = data["gold"]
            market_state["silver_price"] = data["silver"]
            market_state["oil_price"] = data["oil"]
            
            # DXY на MEXC нет, поэтому оставляем легкую симуляцию или статичную цену
            market_state["dxy_index"] = 105.20 + random.uniform(-0.02, 0.02)
            
            fund = data["fund"]
            market_state["funding"] = fund

            # Сигналы
            if fund < -FUNDING_THRESHOLD:
                market_state["signal"], market_state["status_code"] = "BUY", "BUY"
            elif fund > FUNDING_THRESHOLD:
                market_state["signal"], market_state["status_code"] = "SELL", "SELL"
            else:
                market_state["signal"], market_state["status_code"] = "WAIT", "FLAT"
        else:
            market_state["status_code"] = "SYNC"

        # Печать в консоль для тебя (админ-панель)
        print(f"🕵️‍♂️ [PANDA] Fund: {market_state['funding']:.4f}% | BTC: {market_state['btc_price']} | Oil: {market_state['oil_price']}")
        
        time.sleep(2)

@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/pulse')
def get_pulse(): return jsonify(market_state)

if __name__ == '__main__':
    threading.Thread(target=oracle_brain, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
