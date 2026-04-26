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

# 🔗 ВАШИ РАБОЧИЕ ССЫЛКИ (ОПТИМИЗИРОВАННЫЕ)
# 💡 Добавлены параметры поиска для целевого редиректа
PARTNER_LINKS = {
    # ✅ Москва → Нячанг (с параметрами для целевого поиска)
    'MOW_CXR': [
        'https://aviasales.tpm.lv/jocJAnWm?erid=2VtzqvfYndD&origin=MOW&destination=CXR&flexible_dates=1',
        'https://aviasales.tpm.lv/jocJAnWm?erid=2VtzqvfYndD&origin=MOW&destination=CXR&flexible_dates=1',
        'https://aviasales.tpm.lv/jocJAnWm?erid=2VtzqvfYndD&origin=MOW&destination=CXR&flexible_dates=1',
        'https://aviasales.tpm.lv/jocJAnWm?erid=2VtzqvfYndD&origin=MOW&destination=CXR&flexible_dates=1',
        'https://aviasales.tpm.lv/jocJAnWm?erid=2VtzqvfYndD&origin=MOW&destination=CXR&flexible_dates=1',
    ],
    
    # ✅ Нячанг → Москва (с параметрами для целевого поиска)
    'CXR_MOW': [
        'https://aviasales.tpm.lv/YsBVke5L?erid=2VtzqvfYndD&origin=CXR&destination=MOW&flexible_dates=1',
        'https://aviasales.tpm.lv/YsBVke5L?erid=2VtzqvfYndD&origin=CXR&destination=MOW&flexible_dates=1',
        'https://aviasales.tpm.lv/YsBVke5L?erid=2VtzqvfYndD&origin=CXR&destination=MOW&flexible_dates=1',
        'https://aviasales.tpm.lv/YsBVke5L?erid=2VtzqvfYndD&origin=CXR&destination=MOW&flexible_dates=1',
        'https://aviasales.tpm.lv/YsBVke5L?erid=2VtzqvfYndD&origin=CXR&destination=MOW&flexible_dates=1',
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
        """Форматирование списка авиабилетов в один пост"""
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
        
        # Заголовок поста
        title = f"🔥 Чартер #{from_city} → {to_city} → {from_city}:\n"
        
        # Список рейсов
        flight_lines = []
        links = PARTNER_LINKS.get(f'{origin}_{destination}', PARTNER_LINKS['MOW_CXR'])
        
        for i, flight in enumerate(flights[:5]):
            if not isinstance(flight, dict):
                continue
            
            depart_date = flight.get('depart_date', '')
            return_date = flight.get('return_date', '')
            price = flight.get('price', 0)
            baggage = flight.get('baggage', '10кг')
            
            dep_str = FlightFormatter._format_date_russian(depart_date)
            ret_str = FlightFormatter._format_date_russian(return_date)
            date_range = f"{dep_str} - {ret_str}"
            price_str = f"{price:,} руб.".replace(',', ' ')
            link = links[i % len(links)] if links else '#'
            
            # ✅ Формат строки как в вашем примере
            line = f"🔥{date_range} - {price_str} с багажом {baggage} - {link}"
            flight_lines.append(line)
        
        if not flight_lines:
            return {'text': '❌ Нет рейсов', 'parse_mode': 'HTML'}
        
        # Блок с отелем и туром
        hotel_block = (
            f"\n🏨 Забронируй отель ({PARTNER_LINKS['hotel']}) "
            f"с оплатой картой любого банка и через СБП. "
            f"Или хватай тур на эти даты! ({PARTNER_LINKS['tour']})"
        )
        
        # Предупреждение
        warning = (
            "\n\n⚠️ Цена и наличие билетов может измениться в любой момент. "
            "Проверь прямо сейчас — часто после публикации становится ещё дешевле!"
        )
        
        text = title + "\n" + "\n".join(flight_lines) + hotel_block + warning
        
        return {
            'text': text,
            'image': None,
            'link': links[0] if links else '#',
            'parse_mode': 'HTML'
        }
    
    @staticmethod
    def _format_date_russian(date_str: str) -> str:
        """Форматирование даты: "26 апреля" """
        if not date_str:
            return 'Гибкие даты'
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            day = dt.day
            months = ['', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                     'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
            return f"{day} {months[dt.month]}"
        except:
            return date_str[:10] if len(date_str) >= 10 else date_str
    
    @staticmethod
    def add_hashtags(text: str, tags: list) -> str:
        if not tags:
            return text
        hashtags = ' '.join(f'#{tag}' for tag in tags)
        return f"{text}\n\n{hashtags}"