import time
import random

@app.route('/api/chart_data')
def get_chart_data():
    """
    Отдает исторические данные графика и сигналы.
    В БУДУЩЕМ: Здесь ты напишешь код, который читает твой Excel (pandas.read_excel)
    и конвертирует его в такой же формат. Пока генерируем тестовые свечи.
    """
    data = []
    # Генерируем последние 60 "свечей" для теста
    current_time = int(time.time()) - (60 * 15 * 60) # Начинаем издалека (15-минутки)
    base_price = 71000

    for i in range(60):
        open_p = base_price + random.uniform(-100, 100)
        close_p = open_p + random.uniform(-200, 200)
        high_p = max(open_p, close_p) + random.uniform(0, 100)
        low_p = min(open_p, close_p) - random.uniform(0, 100)
        base_price = close_p
        
        # Рандомно раскидываем сигналы светофора для визуала
        signal = "WAIT"
        rand_val = random.random()
        if rand_val > 0.85:
            signal = "BUY"
        elif rand_val < 0.15:
            signal = "SELL"

        data.append({
            "time": current_time + (i * 15 * 60), # +15 минут
            "open": round(open_p, 2),
            "high": round(high_p, 2),
            "low": round(low_p, 2),
            "close": round(close_p, 2),
            "signal": signal
        })
        
    return jsonify(data)
