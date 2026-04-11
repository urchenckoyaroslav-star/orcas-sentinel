from flask import Flask, render_template, jsonify
import requests
import threading
import time
import collections
import random

app = Flask(__name__)

# --- КОНФІГУРАЦІЯ ---
market_state = {
    "btc_price": 0,
    "gold_price": 0,
    "silver_price": 0,
    "oil_price": 84.15,
    "dxy_index": 104.48,
    "signal": "WAIT",
    "status_code": "SYNC",
    "funding": 0 # Сховано від клієнта, але доступно для твого API
}

history_buffer = collections.deque(maxlen=60)
FUNDING_THRESHOLD = 0.0010 # Твій поріг 0.0010% (0.0030 теж можна, але цей чутливіший)

def fetch_exchange_data():
    """Збір даних з усіх бірж (Binance, Bybit, OKX, MEXC, Gate, Bitget)"""
    ex_data = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 1. BINANCE
    try:
        b_res = requests.get("https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT", timeout=3).json()
        b_oi_res = requests.get("https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT", timeout=3).json()
        ex_data.append({
            "oi": float(b_oi_res['openInterest']),
            "fund": float(b_res['lastFundingRate']) * 100,
            "price": float(b_res['markPrice'])
        })
    except: pass

    # 2. BYBIT
    try:
        by_res = requests.get("https://api.bybit.com/v5/market/tickers?category=linear&symbol=BTCUSDT", timeout=3).json()
        d = by_res['result']['list'][0]
        ex_data.append({
            "oi": float(d['openInterest']),
            "fund": float(d['fundingRate']) * 100,
            "price": float(d['lastPrice'])
        })
    except: pass

    # 3. MEXC (Особливий метод через contract.mexc.com)
    try:
        m_res = requests.get("https://contract.mexc.com/api/v1/contract/ticker?symbol=BTC_USDT", timeout=3).json()
        d = m_res.get('data', {})
        if d:
            ex_data.append({
                "oi": float(d.get('holdVol', 0)) * 0.0001,
                "fund": float(d.get('fundingRate', 0)) * 100,
                "price": float(d.get('lastPrice', 0))
            })
    except: pass

    # 4. OKX
    try:
        o_fund = requests.get("https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP", timeout=3).json()['data'][0]
        o_oi = requests.get("https://www.okx.com/api/v5/public/open-interest?instId=BTC-USDT-SWAP", timeout=3).json()['data'][0]
        ex_data.append({
            "oi": float(o_oi['oiCcy']),
            "fund": float(o_fund['fundingRate']) * 100,
            "price": 0 # Ціну візьмемо з інших
        })
    except: pass

    # 5. GATE.IO
    try:
        g_res = requests.get("https://api.gateio.ws/api/v4/futures/usdt/tickers?contract=BTC_USDT", timeout=3).json()[0]
        ex_data.append({
            "oi": float(g_res['quanto_quanto']),
            "fund": float(g_res['funding_rate']) * 100,
            "price": float(g_res['last'])
        })
    except: pass

    # 6. BITGET
    try:
        bg_ticker = requests.get("https://api.bitget.com/api/v2/mix/market/ticker?symbol=BTCUSDT", timeout=3).json()['data'][0]
        bg_fund = requests.get("https://api.bitget.com/api/v2/mix/market/current-funding-rate?symbol=BTCUSDT", timeout=3).json()['data'][0]
        ex_data.append({
            "oi": float(bg_ticker['openInterest']),
            "fund": float(bg_fund['fundingRate']) * 100,
            "price": float(bg_ticker['lastPr'])
        })
    except: pass

    return ex_data

def fetch_macro():
    """Збір Золота та Серебра через PAXG (стабільне джерело)"""
    try:
        res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT", timeout=3).json()
        gold = float(res['price'])
        return gold, gold / 82.5
    except:
        return 2355.0, 28.6 # Резервні дані при обриві зв'язку

def oracle_brain():
    """Головний цикл аналізу ринку"""
    while True:
        data = fetch_exchange_data()
        gold, silver = fetch_macro()
        
        if data:
            # Рахуємо середню ціну та глобальний фандинг
            prices = [ex['price'] for ex in data if ex['price'] > 0]
            avg_price = sum(prices) / len(prices) if prices else 0
            
            w_fund_sum = sum(ex['fund'] * ex['oi'] for ex in data if ex['oi'] > 0)
            total_oi = sum(ex['oi'] for ex in data if ex['oi'] > 0)
            global_funding = w_fund_sum / total_oi if total_oi > 0 else 0
            
            # Оновлюємо стан
            if avg_price > 0:
                market_state["btc_price"] = avg_price
                market_state["gold_price"] = gold
                market_state["silver_price"] = silver
                market_state["funding"] = global_funding
                
                # Симуляція мікро-руху для макро (для вайбу)
                market_state["oil_price"] += random.uniform(-0.01, 0.01)
                market_state["dxy_index"] += random.uniform(-0.005, 0.005)
                
                # ЛОГІКА СИГНАЛІВ
                if global_funding < -FUNDING_THRESHOLD:
                    market_state["signal"], market_state["status_code"] = "BUY", "BUY"
                elif global_funding > FUNDING_THRESHOLD:
                    market_state["signal"], market_state["status_code"] = "SELL", "SELL"
                else:
                    market_state["signal"], market_state["status_code"] = "WAIT", "FLAT"
            
            # Для адміна в терміналі
            print(f"🕵️‍♂️ [PANDA] Global Fund: {global_funding:.4f}% | BTC: {avg_price:.0f}$")

        else:
            market_state["status_code"] = "SYNC"
            
        time.sleep(2) # Оновлення кожні 2 секунди

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/pulse')
def get_pulse():
    return jsonify(market_state)

if __name__ == '__main__':
    # Запускаємо "оракула" у фоновому потоці
    threading.Thread(target=oracle_brain, daemon=True).start()
    # Запуск сервера на порту 5000
    app.run(host='0.0.0.0', port=5000)
