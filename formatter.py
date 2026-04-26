import logging
from datetime import datetime, timedelta
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

# 🔗 БАЗОВЫЕ ССЫЛКИ С MARKER + adults=1
# ✅ Формат: https://www.aviasales.ru/search/ORIGDDMMDESTDDMM?marker=XXX&adults=1
BASE_LINKS = {
    'MOW_CXR': 'https://www.aviasales.ru/search/MOW{dep_date}CXR{ret_date}?marker=2VtzqvfYndD&adults=1',
    'CXR_MOW': 'https://www.aviasales.ru/search/CXR{dep_date}MOW{ret_date}?marker=2VtzqvfYndD&adults=1',
}

# ✅ Отель и тур
PARTNER_LINKS = {
    'hotel': 'https://trip.tpo.lv/7CShdPK6',
    'tour': 'https://level.tpo.lv/yygU1AmM',
}

# ✅ Максимум месяцев вперёд для дат
MAX_MONTHS_AHEAD = 3


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
            
            # ✅ Проверяем и корректируем даты (не дальше 3 месяцев)
            depart_date, return_date = FlightFormatter._validate_dates(depart_date, return_date)
            
            # Форматируем даты: "26 апреля - 5 мая"
            dep_str = FlightFormatter._format_date_russian(depart_date)
            ret_str = FlightFormatter._format_date_russian(return_date)
            date_range = f"{dep_str} - {ret_str}"
            
            # ✅ Форматируем цену с "от"
            price_str = f"от {price:,} руб.".replace(',', ' ')
            
            # ✅ Генерируем ссылку с датами и adults=1
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
        
        # ✅ Предупреждение о ценах
        warning = (
            "\n\n⚠️ <b>Внимание!</b> Цены актуальны на момент публикации и могут измениться. "
            "Переходите по ссылке для проверки актуальной стоимости — часто после публикации становится ещё дешевле!"
        )
        
        text = title + "\n" + "\n".join(flight_lines) + hotel_block + warning
        
        return {
            'text': text,
            'image': None,
            'link': flight_lines[0].split(' - ')[-1] if flight_lines else '#',
            'parse_mode': 'HTML'
        }
    
    @staticmethod
    def _validate_dates(depart_date: str, return_date: str) -> tuple:
        """
        ✅ ПРОВЕРКА И КОРРЕКТИРОВКА ДАТ
        
        Если даты больше 3 месяцев от сегодня — корректируем на +1 месяц от сегодня
        
        Returns:
            (depart_date, return_date) — проверенные даты
        """
        today = datetime.now()
        max_date = today + timedelta(days=MAX_MONTHS_AHEAD * 30)  # 3 месяца вперёд
        min_date = today + timedelta(days=7)  # Минимум 7 дней от сегодня
        
        # ✅ Проверяем дату вылета
        if depart_date:
            try:
                dep_dt = datetime.fromisoformat(depart_date.replace('Z', '+00:00')).replace(tzinfo=None)
                
                # Если дата слишком далеко — корректируем
                if dep_dt > max_date:
                    new_dep = today + timedelta(days=30)  # +1 месяц
                    depart_date = new_dep.strftime('%Y-%m-%d')
                    logger.info(f"⚠️ Дата вылета скорректирована: {depart_date}")
                
                # Если дата слишком близко — корректируем
                elif dep_dt < min_date:
                    new_dep = min_date
                    depart_date = new_dep.strftime('%Y-%m-%d')
                    logger.info(f"⚠️ Дата вылета скорректирована (слишком рано): {depart_date}")
                    
            except:
                # При ошибке — дата +30 дней от сегодня
                depart_date = (today + timedelta(days=30)).strftime('%Y-%m-%d')
        else:
            depart_date = (today + timedelta(days=30)).strftime('%Y-%m-%d')
        
        # ✅ Проверяем дату возвращения
        if return_date:
            try:
                ret_dt = datetime.fromisoformat(return_date.replace('Z', '+00:00')).replace(tzinfo=None)
                
                # Если дата слишком далеко — корректируем
                if ret_dt > max_date:
                    new_ret = today + timedelta(days=45)  # +1.5 месяца (на 2 недели после вылета)
                    return_date = new_ret.strftime('%Y-%m-%d')
                    logger.info(f"⚠️ Дата возвращения скорректирована: {return_date}")
                    
            except:
                # При ошибке — дата +45 дней от сегодня
                return_date = (today + timedelta(days=45)).strftime('%Y-%m-%d')
        else:
            return_date = (today + timedelta(days=45)).strftime('%Y-%m-%d')
        
        return depart_date, return_date
    
    @staticmethod
    def _generate_link(origin: str, destination: str, depart_date: str, return_date: str) -> str:
        """
        ✅ ГЕНЕРАЦИЯ ССЫЛКИ С adults=1
        
        Формат: https://www.aviasales.ru/search/MOWDDMMCXRDDMM?marker=XXX&adults=1
        """
        # ✅ Форматируем даты в DDMM
        dep_ddmm = FlightFormatter._format_date_ddmm(depart_date)
        ret_ddmm = FlightFormatter._format_date_ddmm(return_date)
        
        # ✅ Определяем направление
        route_key = f'{origin}_{destination}'
        base_template = BASE_LINKS.get(route_key, BASE_LINKS['MOW_CXR'])
        
        # ✅ Подставляем даты в шаблон (adults=1 уже в шаблоне!)
        link = base_template.format(dep_date=dep_ddmm, ret_date=ret_ddmm)
        
        logger.debug(f"🔗 Сгенерирована ссылка: {link[:80]}...")
        return link
    
    @staticmethod
    def _format_date_ddmm(date_str: str) -> str:
        """Форматирование даты в DDMM для ссылки Aviasales"""
        if not date_str:
            return '0112'  # Дата по умолчанию
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return f"{dt.day:02d}{dt.month:02d}"  # DDMM с ведущими нулями
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