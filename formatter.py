import logging
from datetime import datetime
from config import POST_SETTINGS

logger = logging.getLogger(__name__)

# ✅ Названия городов
CITY_NAMES = {
    'MOW': 'Москва',
    'CXR': 'Нячанг',
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
}

# ✅ Ваши рабочие ссылки (УЖЕ ВСТАВЛЕНЫ!)
# 🔗 Москва → Нячанг: https://aviasales.tpm.lv/jocJAnWm?erid=2VtzqvfYndD
# 🔗 Нячанг → Москва: https://aviasales.tpm.lv/YsBVke5L?erid=2VtzqvfYndD
# 🔗 Отель: https://trip.tpo.lv/7CShdPK6
# 🔗 Тур: https://level.tpo.lv/yygU1AmM

PARTNER_LINKS = {
    # ✅ Москва → Нячанг (5 вариантов для разнообразия — все ведут на одну ссылку)
    'MOW_CXR': [
        'https://aviasales.tpm.lv/jocJAnWm?erid=2VtzqvfYndD',
        'https://aviasales.tpm.lv/jocJAnWm?erid=2VtzqvfYndD',
        'https://aviasales.tpm.lv/jocJAnWm?erid=2VtzqvfYndD',
        'https://aviasales.tpm.lv/jocJAnWm?erid=2VtzqvfYndD',
        'https://aviasales.tpm.lv/jocJAnWm?erid=2VtzqvfYndD',
    ],
    
    # ✅ Нячанг → Москва (5 вариантов для разнообразия — все ведут на одну ссылку)
    'CXR_MOW': [
        'https://aviasales.tpm.lv/YsBVke5L?erid=2VtzqvfYndD',
        'https://aviasales.tpm.lv/YsBVke5L?erid=2VtzqvfYndD',
        'https://aviasales.tpm.lv/YsBVke5L?erid=2VtzqvfYndD',
        'https://aviasales.tpm.lv/YsBVke5L?erid=2VtzqvfYndD',
        'https://aviasales.tpm.lv/YsBVke5L?erid=2VtzqvfYndD',
    ],
    
    # ✅ Отель
    'hotel': 'https://trip.tpo.lv/7CShdPK6',
    
    # ✅ Тур
    'tour': 'https://level.tpo.lv/yygU1AmM',
}


class FlightFormatter:
    """Форматирование постов в стиле чартеров Москва ↔ Нячанг"""
    
    @staticmethod
    def format(flights) -> dict:
        """
        Форматирование списка авиабилетов в один пост
        
        Args:
            flights: список словарей с данными о рейсах
            
        Returns:
            dict с текстом поста и настройками
        """
        # ✅ ЗАЩИТА: проверяем тип данных
        if not flights:
            return {'text': '❌ Нет доступных рейсов', 'parse_mode': 'HTML'}
        
        if not isinstance(flights, list):
            logger.error(f"❌ Ожидался список, получено: {type(flights)}")
            return {'text': '❌ Ошибка формата данных', 'parse_mode': 'HTML'}
        
        # ✅ Берём первый элемент для определения направления
        first = flights[0]
        
        # ✅ ЗАЩИТА: первый элемент должен быть словарём
        if not isinstance(first, dict):
            logger.error(f"❌ Ожидался dict, получено: {type(first)}")
            logger.error(f"📋 Структура flights: {flights[:2]}")
            return {'text': '❌ Ошибка формата данных', 'parse_mode': 'HTML'}
        
        origin = first.get('origin', 'MOW')
        destination = first.get('destination', 'CXR')
        
        from_city = CITY_NAMES.get(origin, origin)
        to_city = CITY_NAMES.get(destination, destination)
        
        # ✅ Заголовок поста
        title = f"🔥 Чартер #{from_city} → {to_city} → {from_city}:\n"
        
        # ✅ Список рейсов
        flight_lines = []
        links = PARTNER_LINKS.get(f'{origin}_{destination}', PARTNER_LINKS['MOW_CXR'])
        
        for i, flight in enumerate(flights[:5]):  # Максимум 5 рейсов
            # ✅ ЗАЩИТА: каждый элемент должен быть словарём
            if not isinstance(flight, dict):
                logger.warning(f"⚠️ Пропущен элемент {i}: {type(flight)}")
                continue
            
            depart_date = flight.get('depart_date', '')
            return_date = flight.get('return_date', '')
            price = flight.get('price', 0)
            baggage = flight.get('baggage', '10кг')
            
            # Форматируем даты: "26 апреля - 5 мая"
            dep_str = FlightFormatter._format_date_russian(depart_date)
            ret_str = FlightFormatter._format_date_russian(return_date)
            date_range = f"{dep_str} - {ret_str}"
            
            # Форматируем цену: "35 251 руб."
            price_str = f"{price:,} руб.".replace(',', ' ')
            
            # Берём ссылку по очереди из списка
            link = links[i % len(links)] if links else '#'
            
            # ✅ Строка рейса (как в вашем примере)
            line = f"🔥{date_range} - {price_str} с багажом {baggage} - {link}"
            flight_lines.append(line)
        
        if not flight_lines:
            return {'text': '❌ Нет доступных рейсов', 'parse_mode': 'HTML'}
        
        # ✅ Блок с отелем и туром (как в вашем примере)
        hotel_block = (
            f"\n🏨 Забронируй отель ({PARTNER_LINKS['hotel']}) "
            f"с оплатой картой любого банка и через СБП. "
            f"Или хватай тур на эти даты! ({PARTNER_LINKS['tour']})"
        )
        
        # ✅ Предупреждение (как в вашем примере)
        warning = (
            "\n\n⚠️ Цена и наличие билетов может измениться в любой момент. "
            "Проверь прямо сейчас — часто после публикации становится ещё дешевле!"
        )
        
        # ✅ Собираем полный текст
        text = title + "\n" + "\n".join(flight_lines) + hotel_block + warning
        
        return {
            'text': text,
            'image': None,
            'link': links[0] if links else '#',
            'parse_mode': 'HTML'
        }
    
    @staticmethod
    def _format_date_russian(date_str: str) -> str:
        """
        Форматирование даты в стиле: "26 апреля"
        
        Args:
            date_str: дата в формате ISO (2026-04-26)
            
        Returns:
            Строка в формате "26 апреля"
        """
        if not date_str:
            return 'Гибкие даты'
        
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            day = dt.day
            
            # Месяцы на русском
            months = [
                '', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
            ]
            month = months[dt.month]
            
            return f"{day} {month}"
            
        except (ValueError, TypeError):
            # Если не получилось — возвращаем как есть
            return date_str[:10] if len(date_str) >= 10 else date_str
    
    @staticmethod
    def add_hashtags(text: str, tags: list) -> str:
        """Добавление хэштегов (опционально)"""
        if not tags:
            return text
        hashtags = ' '.join(f'#{tag}' for tag in tags)
        return f"{text}\n\n{hashtags}"