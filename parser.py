import aiohttp
import asyncio
import logging
import random
from datetime import datetime
from typing import List, Dict, Optional
from config import TP_TOKEN, TP_MARKER, FILTERS, TEST_MODE

logger = logging.getLogger(__name__)

# ✅ ТЕСТОВЫЕ ДАННЫЕ: авиабилеты с ГОТОВЫМИ короткими ссылками
# 💡 Замените эти ссылки на свои из генератора: app.travelpayouts.com/tools/links
TEST_FLIGHTS = [
    {
        'origin': 'MOW', 'destination': 'DXB', 'price': 25400,
        'airline': 'Аэрофлот', 'depart_date': '2026-05-15',
        # ✅ Короткая ссылка с трекингом (замените на свою!)
        'link': 'https://aviasales.tpm.lv/lumhq0tS?erid=2VtzqvfYndD',
        'country_name': 'ОАЭ', 'hotel_name': '', 'nights': 7, 'hotel_rating': 0,
    },
    {
        'origin': 'MOW', 'destination': 'IST', 'price': 18900,
        'airline': 'Turkish Airlines', 'depart_date': '2026-05-20',
        'link': 'https://aviasales.tpm.lv/abc123?erid=xyz789',  # ← замените на свою
        'country_name': 'Турция', 'hotel_name': '', 'nights': 7, 'hotel_rating': 0,
    },
    {
        'origin': 'MOW', 'destination': 'BKK', 'price': 32100,
        'airline': 'S7', 'depart_date': '2026-06-01',
        'link': 'https://aviasales.tpm.lv/def456?erid=uvw012',  # ← замените на свою
        'country_name': 'Таиланд', 'hotel_name': '', 'nights': 10, 'hotel_rating': 0,
    },
    {
        'origin': 'MOW', 'destination': 'AER', 'price': 8900,
        'airline': 'Победа', 'depart_date': '2026-05-25',
        'link': 'https://aviasales.tpm.lv/ghi789?erid=rst345',  # ← замените на свою
        'country_name': 'Россия', 'hotel_name': '', 'nights': 5, 'hotel_rating': 0,
    },
    {
        'origin': 'MOW', 'destination': 'LED', 'price': 4500,
        'airline': 'Аэрофлот', 'depart_date': '2026-05-18',
        'link': 'https://aviasales.tpm.lv/jkl012?erid=opq678',  # ← замените на свою
        'country_name': 'Россия', 'hotel_name': '', 'nights': 3, 'hotel_rating': 0,
    },
    {
        'origin': 'MOW', 'destination': 'TBS', 'price': 12300,
        'airline': 'Georgian Airways', 'depart_date': '2026-06-10',
        'link': 'https://aviasales.tpm.lv/mno345?erid=lmn901',  # ← замените на свою
        'country_name': 'Грузия', 'hotel_name': '', 'nights': 6, 'hotel_rating': 0,
    },
    {
        'origin': 'MOW', 'destination': 'EVN', 'price': 15600,
        'airline': 'Armenian Airlines', 'depart_date': '2026-05-28',
        'link': 'https://aviasales.tpm.lv/pqr678?erid=ijk234',  # ← замените на свою
        'country_name': 'Армения', 'hotel_name': '', 'nights': 4, 'hotel_rating': 0,
    },
    {
        'origin': 'MOW', 'destination': 'HKT', 'price': 38900,
        'airline': 'Azur Air', 'depart_date': '2026-06-15',
        'link': 'https://aviasales.tpm.lv/stu901?erid=ghi567',  # ← замените на свою
        'country_name': 'Таиланд', 'hotel_name': '', 'nights': 12, 'hotel_rating': 0,
    },
]

# ✅ ТЕСТОВЫЕ ДАННЫЕ: туры с короткими ссылками Level.Travel
# 💡 Замените на свои из генератора
TEST_TOURS = [
    {
        'origin': 'MOW', 'destination': 'AYT', 'price': 45900,
        'country_name': 'Турция', 'city_name': 'Анталья',
        'hotel_name': 'Rixos Premium Belek 5*', 'nights': 7,
        'hotel_rating': 5, 'departure_at': '2026-06-01',
        'link': 'https://level.travel/r/abc123?erid=xyz',  # ← замените на свою
        'old_price': 54000, 'image_url': '',
    },
    {
        'origin': 'MOW', 'destination': 'SSH', 'price': 52300,
        'country_name': 'Египет', 'city_name': 'Шарм-эль-Шейх',
        'hotel_name': 'Alpin Resort 5*', 'nights': 7,
        'hotel_rating': 5, 'departure_at': '2026-06-05',
        'link': 'https://level.travel/r/def456?erid=uvw',  # ← замените на свою
        'old_price': 61000, 'image_url': '',
    },
    {
        'origin': 'MOW', 'destination': 'DXB', 'price': 78900,
        'country_name': 'ОАЭ', 'city_name': 'Дубай',
        'hotel_name': 'Atlantis The Palm 5*', 'nights': 7,
        'hotel_rating': 5, 'departure_at': '2026-06-10',
        'link': 'https://level.travel/r/ghi789?erid=rst',  # ← замените на свою
        'old_price': 92000, 'image_url': '',
    },
]


class TravelPayoutsParser:
    """Парсер предложений из API TravelPayouts"""
    
    def __init__(self):
        self.base_url = 'https://api.travelpayouts.com'
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            headers = {'X-API-Token': TP_TOKEN} if TP_TOKEN else {}
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def fetch_hot_deals(self, limit: int = 10) -> List[Dict]:
        """Получение предложений"""
        logger.info(f"🔍 Запрос предложений: limit={limit}, TEST_MODE={TEST_MODE}")
        
        if TEST_MODE:
            logger.info("🧪 TEST_MODE: используем тестовые данные с короткими ссылками")
            if random.random() < 0.7:
                return self._get_test_flights(limit)
            else:
                return self._get_test_tours(limit)
        
        return await self._fetch_from_api(limit)
    
    async def _fetch_from_api(self, limit: int) -> List[Dict]:
        """Реальный запрос к API (заглушка)"""
        logger.info("📡 Запрос к реальному API...")
        # Пока используем тестовые данные
        return self._get_test_flights(limit)[:limit]
    
    def _get_test_flights(self, limit: int) -> List[Dict]:
        """Тестовые авиабилеты — ссылки УЖЕ содержат трекинг"""
        shuffled = TEST_FLIGHTS.copy()
        random.shuffle(shuffled)
        # ✅ Ссылки уже готовы, ничего не добавляем
        for flight in shuffled:
            if flight.get('link'):
                flight['affiliate_link'] = flight['link']
        return shuffled[:limit]
    
    def _get_test_tours(self, limit: int) -> List[Dict]:
        """Тестовые туры — ссылки УЖЕ содержат трекинг"""
        shuffled = TEST_TOURS.copy()
        random.shuffle(shuffled)
        for tour in shuffled:
            if tour.get('link'):
                tour['affiliate_link'] = tour['link']
        return shuffled[:limit]
    
    async def fetch_flight_deals(self, limit: int = 10) -> List[Dict]:
        return await self.fetch_hot_deals(limit)
    
    def _filter_deals(self, deals: List[Dict]) -> List[Dict]:
        """Фильтрация предложений"""
        logger.info(f"🔎 Фильтрация {len(deals)} предложений...")
        filtered = []
        
        for deal in deals:
            price = deal.get('price', 0)
            destination = deal.get('destination', '')
            
            if not (FILTERS['min_price'] <= price <= FILTERS['max_price']):
                continue
            if FILTERS['countries'] and destination not in FILTERS['countries']:
                continue
            
            # Ссылка уже содержит трекинг
            if deal.get('link'):
                deal['affiliate_link'] = deal['link']
            
            filtered.append(deal)
        
        logger.info(f"✅ После фильтрации: {len(filtered)} предложений")
        return filtered
    
    def format_tour_post(self, item: Dict) -> Dict:
        from formatter import TourFormatter
        post_type = 'tour' if item.get('hotel_name') else 'flight'
        return TourFormatter.format(item, post_type=post_type)
    
    def format_flight_post(self, item: Dict) -> Dict:
        from formatter import TourFormatter
        return TourFormatter.format(item, post_type='flight')