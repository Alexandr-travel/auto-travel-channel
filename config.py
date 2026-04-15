import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')  # @username или -100...

# TravelPayouts
TP_TOKEN = os.getenv('TRAVELPAYOUTS_API_KEY')
TP_MARKER = os.getenv('TP_MARKER', 'your_marker')  # Ваш маркер для ссылок

# Фильтры туров
FILTERS = {
    'min_price': 15000,      # Минимальная цена (₽)
    'max_price': 150000,     # Максимальная цена (₽)
    'countries': [          # Популярные направления
        'Турция', 'Египет', 'ОАЭ', 'Таиланд', 'Вьетнам', 
        'Грузия', 'Армения', 'Мальдивы', 'Шри-Ланка'
    ],
    'min_rating': 3,         # Минимальный рейтинг отеля
    'nights_min': 3,         # Минимум ночей
    'nights_max': 14,        # Максимум ночей
}

# Расписание постинга (по Москве)
SCHEDULE = {
    'morning': {'hour': 9, 'minute': 0},    # Утренний пост
    'evening': {'hour': 19, 'minute': 30},  # Вечерний пост
    'weekend': {'hour': 12, 'minute': 0},   # Выходные
}

# Настройки постов
POST_SETTINGS = {
    'max_posts_per_day': 4,      # Лимит постов в день
    'min_hours_between': 3,      # Минимум часов между постами
    'include_image': True,        # Добавлять фото отеля
    'emoji_style': 'travel',      # 'travel' | 'fire' | 'minimal'
}

# Логирование
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')