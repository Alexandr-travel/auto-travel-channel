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

# 🔗 БАЗОВЫЕ ССЫЛКИ С MARKER (даты добавим динамически)
BASE_LINKS = {
    'MOW_CXR': 'https://www.aviasales.ru/search/MOW{dep_date}CXR{ret_date}?marker=2VtzqvfYndD',
    'CXR_MOW': 'https://www.aviasales.ru/search/CXR{dep_date}MOW{ret_date}?marker=2VtzqvfYndD',
}

# ✅ Отель и тур
PARTNER_LINKS = {
    'hotel': 'https://trip.tpo.lv/7CShdPK6',
    'tour': 'https://level.tpo.lv/yygU1AmM',
}


class FlightFormatter:
    """Форматирование постов в стиле чартеров Москва ↔ Нячанг"""
    
    @staticmethod
    def format(flights) -> dict:
        """Форматирование списка авиабилетов в один пост"""
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
        
        # ✅ Заголовок поста
        title = f"🔥 Чартер #{from_city} → {to_city} → {from_city}:\n"
        
        # ✅ Список рейсов
        flight_lines = []
        
        for i, flight in enumerate(flights[:5]):
            if not isinstance(flight, dict):
                continue
            
            depart_date = flight.get('depart_date', '')
            return_date = flight.get('return_date', '')
            price = flight.get('price', 0)
            baggage = flight.get('baggage', '10кг')
            
            # Форматируем даты
            dep_str = FlightFormatter._format_date_russian(depart_date)
            ret_str = FlightFormatter._format_date_russian(return_date)
            date_range = f"{dep_str} - {ret_str}"
            
            # ✅ Форматируем цену с "от" (чтобы было понятно, что цена примерная)
            price_str = f"от {price:,} руб.".replace(',', ' ')
            
            # ✅ Генерируем ссылку с датами
            link = FlightFormatter._generate_link(origin, destination, depart_date, return_date)
            
            # ✅ Строка рейса
            line = f"🔥{date_range} - {price_str} с багажом {baggage} - {link}"
            flight_lines.append(line)
        
        if not flight_lines:
            return {'text': '❌ Нет рейсов', 'parse_mode': 'HTML'}
        
        # ✅ Блок с отелем и туром
        hotel_block = (
            f"\n🏨 Забронируй отель ({PARTNER_LINKS['hotel']}) "
            f"с оплатой картой любого банка и через СБП. "
            f"Или хватай тур на эти даты! ({PARTNER_LINKS['tour']})"
        )
        
        # ✅ УЛУЧШЕННОЕ предупреждение о ценах
        warning = (
            "\n\n⚠️ <b>Внимание!</b> Цены актуальны на момент публикации и могут измениться. "
            "Переходите по ссылке для проверки актуальной стоимости — часто после публикации становится ещё дешевле!"
        )
        
        # ✅ Дополнительный дисклеймер
        disclaimer = (
            "\n\n<i>📊 Цены могут отличаться на сайте партнёра в момент бронирования. "
            "Это связано с динамическим ценообразованием авиакомпаний.</i>"
        )
        
        text = title + "\n" + "\n".join(flight_lines) + hotel_block + warning + disclaimer
        
        return {
            'text': text,
            'image': None,
            'link': flight_lines[0].split(' - ')[-1] if flight_lines else '#',
            'parse_mode': 'HTML'
        }
    
    @staticmethod
    def _generate_link(origin: str, destination: str, depart_date: str, return_date: str) -> str:
        """Генерация ссылки с динамическими датами"""
        dep_ddmm = FlightFormatter._format_date_ddmm(depart_date)
        ret_ddmm = FlightFormatter._format_date_ddmm(return_date)
        
        route_key = f'{origin}_{destination}'
        base_template = BASE_LINKS.get(route_key, BASE_LINKS['MOW_CXR'])
        
        link = base_template.format(dep_date=dep_ddmm, ret_date=ret_ddmm)
        
        logger.debug(f"🔗 Сгенерирована ссылка: {link[:80]}...")
        return link
    
    @staticmethod
    def _format_date_ddmm(date_str: str) -> str:
        """Форматирование даты в DDMM для ссылки"""
        if not date_str:
            return '0112'
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return f"{dt.day:02d}{dt.month:02d}"
        except:
            return '0112'
    
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