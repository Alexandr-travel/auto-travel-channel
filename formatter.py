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

# 🔗 ПРЯМЫЕ ССЫЛКИ AVIASALES С ПАРАМЕТРОМ marker=
# ✅ Формат: https://www.aviasales.ru/search/ORIGDEST?marker=XXX&params
# ✅ Клики отслеживаются через параметр marker=2VtzqvfYndD
PARTNER_LINKS = {
    # ✅ Москва → Нячанг (прямые ссылки с marker)
    'MOW_CXR': [
        'https://www.aviasales.ru/search/MOWCXR?marker=2VtzqvfYndD&flexible_dates=1&adults=1',
        'https://www.aviasales.ru/search/MOWCXR?marker=2VtzqvfYndD&flexible_dates=1&adults=1',
        'https://www.aviasales.ru/search/MOWCXR?marker=2VtzqvfYndD&flexible_dates=1&adults=1',
        'https://www.aviasales.ru/search/MOWCXR?marker=2VtzqvfYndD&flexible_dates=1&adults=1',
        'https://www.aviasales.ru/search/MOWCXR?marker=2VtzqvfYndD&flexible_dates=1&adults=1',
    ],
    
    # ✅ Нячанг → Москва (прямые ссылки с marker)
    'CXR_MOW': [
        'https://www.aviasales.ru/search/CXRMOW?marker=2VtzqvfYndD&flexible_dates=1&adults=1',
        'https://www.aviasales.ru/search/CXRMOW?marker=2VtzqvfYndD&flexible_dates=1&adults=1',
        'https://www.aviasales.ru/search/CXRMOW?marker=2VtzqvfYndD&flexible_dates=1&adults=1',
        'https://www.aviasales.ru/search/CXRMOW?marker=2VtzqvfYndD&flexible_dates=1&adults=1',
        'https://www.aviasales.ru/search/CXRMOW?marker=2VtzqvfYndD&flexible_dates=1&adults=1',
    ],
    
    # ✅ Отель (прямая ссылка)
    'hotel': 'https://trip.tpo.lv/7CShdPK6',
    
    # ✅ Тур (прямая ссылка)
    'tour': 'https://level.tpo.lv/yygU1AmM',
}


class FlightFormatter:
    """Форматирование постов в стиле чартеров Москва ↔ Нячанг"""
    
    @staticmethod
    def format(flights) -> dict:
        """
        Форматирование списка авиабилетов в один пост
        
        Формат поста как в примере:
        🔥 Чартер #Москва → Нячанг → Москва:
        🔥26 апреля - 5 мая - 35 251 руб. с багажом 10кг - https://...
        """
        # ✅ Защита от неправильных данных
        if not flights or not isinstance(flights, list):
            return {'text': '❌ Нет доступных рейсов', 'parse_mode': 'HTML'}
        
        first = flights[0]
        if not isinstance(first, dict):
            logger.error(f"❌ Ошибка формата: {type(first)}")
            return {'text': '❌ Ошибка данных', 'parse_mode': 'HTML'}
        
        origin = first.get('origin', 'MOW')
        destination = first.get('destination', 'CXR')
        
        from_city = CITY_NAMES.get(origin, origin)
        to_city = CITY_NAMES.get(destination, destination)
        
        # ✅ Заголовок поста (как в вашем примере)
        title = f"🔥 Чартер #{from_city} → {to_city} → {from_city}:\n"
        
        # ✅ Список рейсов
        flight_lines = []
        links = PARTNER_LINKS.get(f'{origin}_{destination}', PARTNER_LINKS['MOW_CXR'])
        
        for i, flight in enumerate(flights[:5]):  # Максимум 5 рейсов в посте
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
            
            # ✅ Строка рейса (точно как в вашем примере)
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