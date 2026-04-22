import logging
from datetime import datetime
from config import POST_SETTINGS

logger = logging.getLogger(__name__)

class TourFormatter:
    """Форматирование постов для канала"""
    
    EMOJIS = {
        'travel': {
            'tour': '🏖️', 'flight': '✈️', 'hotel': '🏨', 
            'price': '💰', 'date': '📅', 'link': '🔗',
            'fire': '🔥', 'new': '✨', 'top': '🏆'
        },
        'fire': {
            'tour': '🔥', 'flight': '⚡', 'hotel': '🏨',
            'price': '💸', 'date': '🗓️', 'link': '👉',
            'fire': '🔥🔥', 'new': '🆕', 'top': '👑'
        },
        'minimal': {'tour': '', 'flight': '', 'hotel': '', 'price': '', 'date': '', 'link': '', 'fire': '', 'new': '', 'top': ''}
    }
    
    @staticmethod
    def format(item: dict, post_type: str = 'tour') -> dict:
        style = POST_SETTINGS.get('emoji_style', 'travel')
        emojis = TourFormatter.EMOJIS.get(style, TourFormatter.EMOJIS['travel'])
        if post_type == 'tour':
            return TourFormatter._format_tour(item, emojis)
        elif post_type == 'flight':
            return TourFormatter._format_flight(item, emojis)
        return {}
    
    @staticmethod
    def _format_tour(tour: dict, emojis: dict) -> dict:
        country = tour.get('country_name', 'Неизвестно')
        city = tour.get('city_name', '')
        hotel = tour.get('hotel_name', 'Отель')
        price = tour.get('price', 0)
        old_price = tour.get('old_price', 0)
        nights = tour.get('nights', 7)
        rating = tour.get('hotel_rating', 0)
        departure = tour.get('departure_at', '')
        link = tour.get('affiliate_link', tour.get('link', '#'))
        
        discount = ''
        if old_price and old_price > price:
            saved = old_price - price
            percent = int((saved / old_price) * 100)
            discount = f"\n{emojis['fire']} СКИДКА {percent}% (экономия {saved:,}₽)"
        
        stars = '⭐' * int(rating) if rating else ''
        date_str = departure[:10] if departure else 'Гибкие даты'
        
        text = (
            f"{emojis['fire']} <b>ГОРЯЩИЙ ТУР: {country}</b> {emojis['fire']}\n"
            f"{'📍 ' + city + '\n' if city else ''}"
            f"🏨 {hotel}\n"
            f"{stars}{' (' + str(rating) + '/5)' if rating else ''}\n"
            f"🌙 {nights} ночей / 2 человека\n"
            f"{emojis['date']} Вылет: {date_str}\n"
            f"{emojis['price']} <b>{price:,}₽</b>{discount}\n"
            f"\n{emojis['link']} <a href='{link}'>Забронировать тур</a>\n"
            f"\n<i>Цены актуальны на момент публикации. Партнёр @TravelPayouts</i>"
        )
        return {'text': text, 'image': None, 'link': link, 'parse_mode': 'HTML'}
    
    @staticmethod
    def _format_flight(flight: dict, emojis: dict) -> dict:
        origin = flight.get('origin', 'MOW')
        destination = flight.get('destination', '?')
        price = flight.get('price', 0)
        airline = flight.get('airline', '')
        depart_date = flight.get('depart_date', '')
        link = flight.get('affiliate_link', flight.get('link', '#'))
        
        cities = {'MOW': 'Москва', 'LED': 'Санкт-Петербург', 'AER': 'Сочи', 'IST': 'Стамбул', 'DXB': 'Дубай', 'BKK': 'Бангкок', 'HKT': 'Пхукет', 'TBS': 'Тбилиси', 'EVN': 'Ереван', 'AYT': 'Анталья', 'SSH': 'Шарм-эль-Шейх'}
        from_city = cities.get(origin, origin)
        to_city = cities.get(destination, destination)
        
        text = (
            f"{emojis['flight']} <b>ВЫГОДНЫЙ АВИАБИЛЕТ</b>\n"
            f"🛫 {from_city} → {to_city}\n"
            f"{'✈️ ' + airline + '\n' if airline else ''}"
            f"{emojis['date']} Дата: {depart_date or 'Гибкие даты'}\n"
            f"{emojis['price']} <b>{price:,}₽</b>\n"
            f"\n{emojis['link']} <a href='{link}'>Найти билеты</a>\n"
            f"\n<i>Цены могут измениться. Партнёр @Aviasales</i>"
        )
        return {'text': text, 'image': None, 'link': link, 'parse_mode': 'HTML'}