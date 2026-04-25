import os
from dotenv import load_dotenv

load_dotenv()

# ✅ Telegram
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
ADMIN_ID = os.getenv('ADMIN_ID')

# ✅ TravelPayouts
TP_TOKEN = os.getenv('TRAVELPAYOUTS_API_KEY')

# ✅ Проверка критичных переменных
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден!")
if not CHANNEL_ID:
    raise ValueError("❌ CHANNEL_ID не найден!")

# ✅ ТЕСТОВЫЙ РЕЖИМ
TEST_MODE = False

# ✅ ФИЛЬТРЫ АВИАБИЛЕТОВ (ОСЛАБЛЕНЫ ДЛЯ ТЕСТА)
FILTERS = {
    'min_price': 1000,        # ✅ Мин. цена: 1000₽ (было 3000)
    'max_price': 200000,      # ✅ Макс. цена: 200к₽ (было 100к)
    'origins': [],            # ✅ Пустой = ВСЕ города вылета
    'destinations': [],       # ✅ Пустой = ВСЕ направления
    'airlines': [],           # ✅ Пустой = ВСЕ авиакомпании
}

# ✅ Расписание постинга (по UTC, МСК = UTC+3)
SCHEDULE = {
    'morning': {'hour': 5, 'minute': 30},   # 08:30 МСК
    'afternoon': {'hour': 11, 'minute': 0}, # 14:00 МСК
    'evening': {'hour': 17, 'minute': 0},   # 20:00 МСК
}

# Настройки постов
POST_SETTINGS = {
    'max_posts_per_day': 6,
    'min_hours_between': 2,
    'emoji_style': 'flight',
}

# Логирование
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')  # ✅ DEBUG для отладки