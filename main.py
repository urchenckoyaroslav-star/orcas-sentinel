from flask import Flask, render_template, jsonify
import pandas as pd
import os
import time

app = Flask(__name__)

# Имя твоего файла
CSV_FILE = "ORCAS_PULSE_LOG.xlsx - Макро Пульс 5м.csv"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/pulse')
def pulse():
    """Берет самую последнюю строку из файла для светофора и цены BTC"""
    current_market_data = {
        "btc_price": 0.0,
        "gold_price": 2340.50, # Остальные пока статичны
        "silver_price": 28.15,
        "oil_price": 82.40,
        "dxy_index": 104.20,
        "signal": "WAIT",
        "status_code": "FLAT"
    }

    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            if not df.empty:
                # Берем самую последнюю строку из таблицы
                last_row = df.iloc[-1]
                current_market_data["btc_price"] = float(last_row.get('Close', 0.0))
                
                # Берем последний сигнал
                raw_signal = str(last_row.get('Signal', 'WAIT')).upper().strip()
                if raw_signal == 'BUY':
                    current_market_data["signal"] = "BUY"
                    current_market_data["status_code"] = "BUY"
                elif raw_signal == 'SELL':
                    current_market_data["signal"] = "SELL"
                    current_market_data["status_code"] = "SELL"
                else:
                    current_market_data["signal"] = "WAIT"
                    current_market_data["status_code"] = "FLAT"
        except Exception as e:
            print(f"Помилка читання CSV для пульсу: {e}")

    return jsonify(current_market_data)

@app.route('/api/chart_data')
def chart_data():
    """Строит историю графика из файла для неоновых свечей"""
    if not os.path.exists(CSV_FILE):
        return jsonify([])

    try:
        df = pd.read_csv(CSV_FILE)
        # Переводим время из формата Excel в Unix (секунды) для графика
        df['UnixTime'] = pd.to_datetime(df['Time']).astype('int64') // 10**9

        data = []
        for index, row in df.iterrows():
            raw_signal = str(row.get('Signal', 'WAIT')).upper().strip()
            if raw_signal not in ['BUY', 'SELL']:
                raw_signal = 'WAIT'

            data.append({
                "time": int(row['UnixTime']),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close']),
                "signal": raw_signal
            })
            
        return jsonify(data)
        
    except Exception as e:
        print(f"Помилка обробки файлу для графіка: {e}")
        return jsonify([])

if __name__ == '__main__':
    app.run(debug=True, port=5000)
