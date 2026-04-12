from flask import Flask, render_template, jsonify, request
import pandas as pd
import time
import os
import random

app = Flask(__name__)

# ... (тут залишається твій код для START_BALANCES та /api/pulse) ...

@app.route('/api/chart_data')
def chart_data():
    """
    Читає реальні дані з твого CSV файлу та віддає їх на графік.
    """
    file_name = "ORCAS_PULSE_LOG.xlsx - Макро Пульс 5м.csv"
    
    # Перевіряємо, чи існує файл у папці
    if not os.path.exists(file_name):
        print(f"⚠️ УВАГА: Файл {file_name} не знайдено!")
        return jsonify([]) # Повертаємо порожній масив, щоб графік не зламався

    try:
        # Читаємо CSV файл
        df = pd.read_csv(file_name)

        # ==========================================
        # ❗️ КІБЕР-НАЛАШТУВАННЯ (ЗВЕРНИ УВАГУ) ❗️
        # Тут вказані назви колонок. Якщо у твоєму файлі вони 
        # називаються інакше (наприклад, 'Цена Закрытия' замість 'Close'), 
        # просто поміняй їх тут у дужках:
        # ==========================================
        col_time = 'Time'    # Колонка з часом (наприклад: 2024-05-12 15:30:00)
        col_open = 'Open'    # Ціна відкриття
        col_high = 'High'    # Максимальна ціна
        col_low = 'Low'      # Мінімальна ціна
        col_close = 'Close'  # Ціна закриття
        col_signal = 'Signal'# Сигнал (повинен містити текст BUY, SELL або WAIT)
        
        # Графік Lightweight Charts розуміє тільки Unix Time (секунди).
        # Цей рядок автоматично перетворює звичайний час з Екселю в секунди:
        df['UnixTime'] = pd.to_datetime(df[col_time]).astype('int64') // 10**9

        data = []
        # Проходимося по кожному рядку твого файлу
        for index, row in df.iterrows():
            
            # Читаємо сигнал. Якщо клітинка порожня, ставимо 'WAIT'
            raw_signal = str(row.get(col_signal, 'WAIT')).upper().strip()
            if raw_signal not in ['BUY', 'SELL']:
                raw_signal = 'WAIT'

            data.append({
                "time": int(row['UnixTime']),
                "open": float(row[col_open]),
                "high": float(row[col_high]),
                "low": float(row[col_low]),
                "close": float(row[col_close]),
                "signal": raw_signal
            })
            
        print(f"✅ Успішно завантажено {len(data)} свічок з Екселю!")
        return jsonify(data)
        
    except Exception as e:
        print(f"❌ Помилка обробки файлу: {e}")
        return jsonify([])

# ... (решта коду main.py) ...
