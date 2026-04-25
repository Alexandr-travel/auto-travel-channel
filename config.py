import os
from dotenv import load_dotenv

load_dotenv()

# ✅ Telegram
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
ADMIN_ID = os.getenv('ADMIN_ID')

# ✅ TravelPayouts (токен для API, если понадобится)
TP_TOKEN = os.getenv('TRAVELPAYOUTS_API_KEY')

# ✅ Проверка критичных переменных
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден! Добавьте в Railway Variables")
if not CHANNEL_ID:
    raise ValueError("❌ CHANNEL_ID не найден! Добавьте в Railway Variables")

# ✅ ТЕСТОВЫЙ РЕЖИМ: используем тестовые данные
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'

# ✅ Фильтры авиабилетов
FILTERS = {
    'min_price': 3000,       # Мин. цена авиа (₽)
    'max_price': 50000,     # Макс. цена авиа (₽)
    'origins': ['MOW', 'LED', 'SVX', 'KZN'],  # Города вылета (IATA)
    'destinations': ['NHA1'],      # Пустой = все направления
    'airlines': [],          # Пустой = все авиакомпании
}

# ✅ Расписание постинга (по UTC, МСК = UTC+3)
SCHEDULE = {
    'morning': {'hour': 5, 'minute': 30},   # 08:30 МСК — утренние рейсы
    'afternoon': {'hour': 11, 'minute': 0}, # 14:00 МСК — дневные предложения
    'evening': {'hour': 17, 'minute': 0},   # 20:00 МСК — вечерние рейсы
}

# Настройки постов
POST_SETTINGS = {
    'max_posts_per_day': 6,      # Лимит постов в день
    'min_hours_between': 2,      # Минимум часов между постами
    'emoji_style': 'flight',     # 'flight' | 'fire' | 'minimal'
}

# Логирование
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')