import logging
from datetime import datetime
from config import POST_SETTINGS

logger = logging.getLogger(__name__)

# ✅ Названия городов — ПРОВЕРЬТЕ, ЧТО CXR ЕСТЬ!
CITY_NAMES = {
    'MOW': 'Москва',
    'CXR': 'Нячанг (Камрань)',  # ✅ Ключевое: CXR → Нячанг
    'LED': 'Санкт-Петербург',
    'SVX': 'Екатеринбург',
    'KZN': 'Казань',
    'DXB': 'Дубай',
    'IST': 'Стамбул',
    'BKK': 'Бангкок',
    'HKT': 'Пхукет',
    'AER': 'Сочи',
    'TBS': 'Тбилиси',
    'EVN': 'Ереван',
    'GOA': 'Гоа',
    'AYT': 'Анталья',
    'SSH': 'Шарм-эль-Шейх',
    'SGN': 'Хошимин',
    'HAN': 'Ханой',
}

# ✅ Эмодзи для разных стилей
EMOJIS = {
    'flight': {
        'flight': '✈️',
        'price': '💰',
        'date': '📅',
        'link': '🔗',
        'fire': '🔥',
        'new': '✨',
        'top': '🏆',
        'arrow': '➡️',
        'beach': '🏖️'
    },
    'fire': {
        'flight': '🔥',
        'price': '💸',
        'date': '🗓️',
        'link': '👉',
        'fire': '🔥🔥',
        'new': '🆕',
        'top': '👑',
        'arrow': '➡️',
        'beach': '🏝️'
    },
    'minimal': {
        'flight': '',
        'price': '',
        'date': '',
        'link': '',
        'fire': '',
        'new': '',
        'top': '',
        'arrow': '→',
        'beach': ''
    }
}


class FlightFormatter:
    """Форматирование постов с авиабилетами"""
    
    @staticmethod
    def format(flight: dict) -> dict:
        """Основной метод форматирования"""
        style = POST_SETTINGS.get('emoji_style', 'flight')
        emojis = EMOJIS.get(style, EMOJIS['flight'])
        return FlightFormatter._format_flight(flight, emojis)
    
    @staticmethod
    def _format_flight(flight: dict, emojis: dict) -> dict:
        """Форматирование одного авиабилета"""
        origin = flight.get('origin', '???')
        destination = flight.get('destination', '???')
        price = flight.get('price', 0)
        airline = flight.get('airline', '')
        depart_date = flight.get('depart_date', '')
        return_date = flight.get('return_date', '')
        link = flight.get('affiliate_link', flight.get('link', '#'))
        country = flight.get('country_name', '')
        city = flight.get('city_name', '')
        
        # ✅ Форматируем названия городов — ПРОВЕРКА НА CXR
        from_city = CITY_NAMES.get(origin, origin)
        to_city = CITY_NAMES.get(destination, destination)
        
        # ✅ Дополнительная проверка: если city задан — используем его
        if city and city.lower() not in to_city.lower():
            to_city = f"{city}, {country}" if country else city
        
        # ✅ Добавляем эмодзи пляжа для Вьетнама
        beach_emoji = emojis.get('beach', '🏖️') if destination == 'CXR' else ''
        
        # ✅ Форматируем даты
        dep_str = FlightFormatter._format_date(depart_date)
        
        # Возвратная дата
        return_text = ""
        if return_date:
            ret_str = FlightFormatter._format_date(return_date, short=True)
            return_text = f" — {ret_str}"
        
        # ✅ Заголовок поста в зависимости от направления
        if destination == 'CXR':
            title = f"{emojis['fire']} <b>АВИАБИЛЕТЫ В НЯЧАНГ</b> {beach_emoji} {emojis['fire']}"
        elif origin == 'CXR':
            title = f"{emojis['fire']} <b>АВИАБИЛЕТЫ ИЗ НЯЧАНГА</b> {beach_emoji} {emojis['fire']}"
        else:
            title = f"{emojis['fire']} <b>ВЫГОДНЫЙ АВИАБИЛЕТ</b> {emojis['fire']}"
        
        # ✅ Текст поста
        text = (
            f"{title}\n\n"
            f"🛫 {from_city} {emojis['arrow']} {to_city}\n"
            f"{'✈️ ' + airline + '\n' if airline else ''}"
            f"{emojis['date']} {dep_str}{return_text}\n"
            f"{emojis['price']} <b>{price:,}₽</b>\n\n"
            f"{emojis['link']} <a href='{link}'>Найти билеты</a>\n\n"
            f"<i>Цены актуальны на момент публикации. Партнёр @Aviasales</i>"
        )
        
        return {
            'text': text,
            'image': None,
            'link': link,
            'parse_mode': 'HTML'
        }
    
    @staticmethod
    def _format_date(date_str: str, short: bool = False) -> str:
        """Форматирование даты"""
        if not date_str:
            return 'Гибкие даты'
        
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            if short:
                return dt.strftime('%d.%m')
            else:
                return dt.strftime('%d.%m.%Y')
        except (ValueError, TypeError):
            return date_str[:10] if len(date_str) >= 10 else date_str
    
    @staticmethod
    def add_hashtags(text: str, tags: list) -> str:
        """Добавление хэштегов"""
        if not tags:
            return text
        hashtags = ' '.join(f'#{tag}' for tag in tags)
        return f"{text}\n\n{hashtags}"