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
    """Сбор Глобального Взвешенного Фандинга со всех бирж"""
    exchanges_data = []
    
    # 1. BINANCE
    try:
        b_ticker = requests.get("https://fapi.binance.com/fapi/v1/ticker/24hr?symbol=BTCUSDT", timeout=2).json()
        b_price, b_vol = float(b_ticker['lastPrice']), float(b_ticker['volume'])
        b_oi = float(requests.get("https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT", timeout=2).json()['openInterest'])
        b_fund = float(requests.get("https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT", timeout=2).json()['lastFundingRate']) * 100
        exchanges_data.append({"oi": b_oi, "fund": b_fund})
    except: b_price, b_vol = 0, 0

    # 2. BYBIT
    try:
        by_data = requests.get("https://api.bybit.com/v5/market/tickers?category=linear&symbol=BTCUSDT", timeout=2).json()['result']['list'][0]
        exchanges_data.append({"oi": float(by_data['openInterest']), "fund": float(by_data['fundingRate']) * 100})
    except: pass

    # 3. MEXC (Особый способ из твоего бота)
    try:
        mexc_res = requests.get("https://contract.mexc.com/api/v1/contract/ticker?symbol=BTC_USDT", timeout=2).json()
        m_data = mexc_res.get('data', {})
        if m_data:
            m_oi = float(m_data.get('holdVol', 0)) * 0.0001
            m_fund = float(m_data.get('fundingRate', 0)) * 100
            exchanges_data.append({"oi": m_oi, "fund": m_fund})
    except: pass

    # 4. OKX
    try:
        okx_fund_data = requests.get("https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP", timeout=2).json()['data'][0]
        okx_oi_data = requests.get("https://www.okx.com/api/v5/public/open-interest?instId=BTC-USDT-SWAP", timeout=2).json()['data'][0]
        exchanges_data.append({"oi": float(okx_oi_data['oiCcy']), "fund": float(okx_fund_data['fundingRate']) * 100})
    except: pass

    # 5. GATE & BITGET (Если публичные API отвечают)
    try:
        gate_data = requests.get("https://api.gateio.ws/api/v4/futures/usdt/tickers?contract=BTC_USDT", timeout=2).json()[0]
        exchanges_data.append({"oi": float(gate_data['quanto_quanto']), "fund": float(gate_data['funding_rate']) * 100})
    except: pass

    # --- РАСЧЕТ ГЛОБАЛЬНОГО ВЗВЕШЕННОГО ФАНДИНГА ---
    total_oi = sum(ex['oi'] for ex in exchanges_data)
    if total_oi > 0:
        global_funding = sum((ex['fund'] * ex['oi']) for ex in exchanges_data) / total_oi
    else:
        global_funding = 0.0

    print(f"🕵️‍♂️ [СИСТЕМА] Global OI: {total_oi:,.0f} | Global Funding: {global_funding:.4f}%")

    try:
        gold = float(requests.get("https://fapi.binance.com/fapi/v1/ticker/price?symbol=XAUUSDT", timeout=2).json()['price'])
        silver = float(requests.get("https://fapi.binance.com/fapi/v1/ticker/price?symbol=XAGUSDT", timeout=2).json()['price'])
        return {"price": b_price, "volume": b_vol, "funding": global_funding, "gold": gold, "silver": silver}
    except: return None

def oracle_brain():
    while True:
        data = fetch_global_data()
        if data and data["price"] > 0:
            market_state["btc_price"], market_state["gold_price"], market_state["silver_price"] = data["price"], data["gold"], data["silver"]
            market_state["oil_price"] += random.uniform(-0.02, 0.02)
            market_state["dxy_index"] += random.uniform(-0.01, 0.01)

            history_buffer.append({"vol": data["volume"]})

            if len(history_buffer) > 2:
                vol_delta = ((history_buffer[-1]["vol"] - history_buffer[0]["vol"]) / history_buffer[0]["vol"]) * 100
                fund = data["funding"]

                if fund < -FUNDING_THRESHOLD:
                    market_state["signal"], market_state["status_code"] = "BUY", "BUY"
                elif fund > FUNDING_THRESHOLD:
                    market_state["signal"], market_state["status_code"] = "SELL", "SELL"
                elif abs(vol_delta) > 0.05:
                    market_state["signal"], market_state["status_code"] = "WAIT", "MOVING"
                else:
                    market_state["signal"], market_state["status_code"] = "WAIT", "FLAT"
        time.sleep(1)

@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/pulse')
def get_pulse(): return jsonify(market_state)

if __name__ == '__main__':
    threading.Thread(target=oracle_brain, daemon=True).start()
    app.run(debug=True, port=5000)