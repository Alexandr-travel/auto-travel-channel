import logging
from datetime import datetime
from config import POST_SETTINGS

logger = logging.getLogger(__name__)

# ✅ Названия городов для отображения
CITY_NAMES = {
    'MOW': 'Москва',
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
        'arrow': '➡️'
    },
    'fire': {
        'flight': '🔥',
        'price': '💸',
        'date': '🗓️',
        'link': '👉',
        'fire': '🔥🔥',
        'new': '🆕',
        'top': '👑',
        'arrow': '➡️'
    },
    'minimal': {
        'flight': '',
        'price': '',
        'date': '',
        'link': '',
        'fire': '',
        'new': '',
        'top': '',
        'arrow': '→'
    }
}


class FlightFormatter:
    """Форматирование постов с авиабилетами для Telegram канала"""
    
    @staticmethod
    def format(flight: dict) -> dict:
        """
        Основной метод форматирования авиабилета
        
        Args:
            flight: dict с данными о рейсе
            
        Returns:
            dict с текстом поста, ссылкой и parse_mode
        """
        style = POST_SETTINGS.get('emoji_style', 'flight')
        emojis = EMOJIS.get(style, EMOJIS['flight'])
        return FlightFormatter._format_flight(flight, emojis)
    
    @staticmethod
    def _format_flight(flight: dict, emojis: dict) -> dict:
        """
        Форматирование одного авиабилета
        
        Args:
            flight: dict с данными о рейсе
            emojis: dict с эмодзи для выбранного стиля
            
        Returns:
            dict с готовым постом
        """
        origin = flight.get('origin', '???')
        destination = flight.get('destination', '???')
        price = flight.get('price', 0)
        airline = flight.get('airline', '')
        depart_date = flight.get('depart_date', '')
        return_date = flight.get('return_date', '')
        link = flight.get('affiliate_link', flight.get('link', '#'))
        country = flight.get('country_name', '')
        city = flight.get('city_name', '')
        
        # ✅ Форматируем названия городов
        from_city = CITY_NAMES.get(origin, origin)
        to_city = CITY_NAMES.get(destination, destination)
        
        # Если есть название города — используем его
        if city and city != to_city:
            to_city = f"{city}, {country}" if country else city
        
        # ✅ Форматируем даты
        dep_str = FlightFormatter._format_date(depart_date)
        
        # Возвратная дата (опционально)
        return_text = ""
        if return_date:
            ret_str = FlightFormatter._format_date(return_date, short=True)
            return_text = f" — {ret_str}"
        
        # ✅ Текст поста
        text = (
            f"{emojis['fire']} <b>ВЫГОДНЫЙ АВИАБИЛЕТ</b> {emojis['fire']}\n\n"
            f"🛫 {from_city} {emojis['arrow']} {to_city}\n"
            f"{'✈️ ' + airline + '\n' if airline else ''}"
            f"{emojis['date']} {dep_str}{return_text}\n"
            f"{emojis['price']} <b>{price:,}₽</b>\n\n"
            f"{emojis['link']} <a href='{link}'>Найти билеты</a>\n\n"
            f"<i>Цены актуальны на момент публикации. Партнёр @Aviasales</i>"
        )
        
        return {
            'text': text,
            'image': None,  # Авиа-посты обычно без картинок
            'link': link,
            'parse_mode': 'HTML'
        }
    
    @staticmethod
    def _format_date(date_str: str, short: bool = False) -> str:
        """
        Форматирование даты
        
        Args:
            date_str: дата в формате ISO (2026-05-15)
            short: если True, возвращает только день и месяц
            
        Returns:
            Отформатированная строка даты
        """
        if not date_str:
            return 'Гибкие даты'
        
        try:
            # Пробуем распарсить ISO формат
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            if short:
                return dt.strftime('%d.%m')
            else:
                return dt.strftime('%d.%m.%Y')
        except (ValueError, TypeError):
            # Если не получилось — возвращаем как есть (первые 10 символов)
            return date_str[:10] if len(date_str) >= 10 else date_str
    
    @staticmethod
    def add_hashtags(text: str, tags: list) -> str:
        """
        Добавление хэштегов к посту (опционально)
        
        Args:
            text: исходный текст поста
            tags: список хэштегов без #
            
        Returns:
            Текст с добавленными хэштегами
        """
        if not tags:
            return text
        hashtags = ' '.join(f'#{tag}' for tag in tags)
        return f"{text}\n\n{hashtags}"