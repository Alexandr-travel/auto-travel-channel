import aiohttp
import asyncio
import logging
import random
import urllib.parse
from datetime import datetime
from typing import List, Dict, Optional
from config import TP_TOKEN, TP_MARKER, FILTERS, TEST_MODE, TP_PARTNER_ID

logger = logging.getLogger(__name__)

# ✅ ТЕСТОВЫЕ ДАННЫЕ: авиабилеты
TEST_FLIGHTS = [
    {
        'origin': 'MOW', 'destination': 'DXB', 'price': 25400,
        'airline': 'Аэрофлот', 'depart_date': '2026-05-15',
        'link': 'https://www.aviasales.ru/search/MOW1505DXB1',
        'country_name': 'ОАЭ', 'hotel_name': '', 'nights': 7, 'hotel_rating': 0,
    },
    {
        'origin': 'MOW', 'destination': 'IST', 'price': 18900,
        'airline': 'Turkish Airlines', 'depart_date': '2026-05-20',
        'link': 'https://www.aviasales.ru/search/MOW2005IST1',
        'country_name': 'Турция', 'hotel_name': '', 'nights': 7, 'hotel_rating': 0,
    },
    {
        'origin': 'MOW', 'destination': 'BKK', 'price': 32100,
        'airline': 'S7', 'depart_date': '2026-06-01',
        'link': 'https://www.aviasales.ru/search/MOW0106BKK1',
        'country_name': 'Таиланд', 'hotel_name': '', 'nights': 10, 'hotel_rating': 0,
    },
    {
        'origin': 'MOW', 'destination': 'AER', 'price': 8900,
        'airline': 'Победа', 'depart_date': '2026-05-25',
        'link': 'https://www.aviasales.ru/search/MOW2505AER1',
        'country_name': 'Россия', 'hotel_name': '', 'nights': 5, 'hotel_rating': 0,
    },
    {
        'origin': 'MOW', 'destination': 'LED', 'price': 4500,
        'airline': 'Аэрофлот', 'depart_date': '2026-05-18',
        'link': 'https://www.aviasales.ru/search/MOW1805LED1',
        'country_name': 'Россия', 'hotel_name': '', 'nights': 3, 'hotel_rating': 0,
    },
    {
        'origin': 'MOW', 'destination': 'TBS', 'price': 12300,
        'airline': 'Georgian Airways', 'depart_date': '2026-06-10',
        'link': 'https://www.aviasales.ru/search/MOW1006TBS1',
        'country_name': 'Грузия', 'hotel_name': '', 'nights': 6, 'hotel_rating': 0,
    },
    {
        'origin': 'MOW', 'destination': 'EVN', 'price': 15600,
        'airline': 'Armenian Airlines', 'depart_date': '2026-05-28',
        'link': 'https://www.aviasales.ru/search/MOW2805EVN1',
        'country_name': 'Армения', 'hotel_name': '', 'nights': 4, 'hotel_rating': 0,
    },
    {
        'origin': 'MOW', 'destination': 'HKT', 'price': 38900,
        'airline': 'Azur Air', 'depart_date': '2026-06-15',
        'link': 'https://www.aviasales.ru/search/MOW1506HKT1',
        'country_name': 'Таиланд', 'hotel_name': '', 'nights': 12, 'hotel_rating': 0,
    },
]

# ✅ ТЕСТОВЫЕ ДАННЫЕ: туры
TEST_TOURS = [
    {
        'origin': 'MOW', 'destination': 'AYT', 'price': 45900,
        'country_name': 'Турция', 'city_name': 'Анталья',
        'hotel_name': 'Rixos Premium Belek 5*', 'nights': 7,
        'hotel_rating': 5, 'departure_at': '2026-06-01',
        'link': 'https://level.travel/search/MOW0106AYT7',
        'old_price': 54000, 'image_url': '',
    },
    {
        'origin': 'MOW', 'destination': 'SSH', 'price': 52300,
        'country_name': 'Египет', 'city_name': 'Шарм-эль-Шейх',
        'hotel_name': 'Alpin Resort 5*', 'nights': 7,
        'hotel_rating': 5, 'departure_at': '2026-06-05',
        'link': 'https://level.travel/search/MOW0506SSH7',
        'old_price': 61000, 'image_url': '',
    },
    {
        'origin': 'MOW', 'destination': 'DXB', 'price': 78900,
        'country_name': 'ОАЭ', 'city_name': 'Дубай',
        'hotel_name': 'Atlantis The Palm 5*', 'nights': 7,
        'hotel_rating': 5, 'departure_at': '2026-06-10',
        'link': 'https://level.travel/search/MOW1006DXB7',
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
            logger.info("🧪 TEST_MODE: используем тестовые данные")
            if random.random() < 0.7:
                return self._get_test_flights(limit)
            else:
                return self._get_test_tours(limit)
        
        return await self._fetch_from_api(limit)
    
    async def _fetch_from_api(self, limit: int) -> List[Dict]:
        """Реальный запрос к API"""
        logger.info("📡 Запрос к реальному API...")
        
        if not TP_TOKEN:
            logger.error("❌ TP_TOKEN не задан!")
            return self._get_test_flights(limit)
        
        session = await self.get_session()
        endpoints = [
            'https://api.travelpayouts.com/v1/prices/direct',
            'https://api.travelpayouts.com/data/prices/direct',
        ]
        
        params = {
            'origin': 'MOW',
            'currency': 'RUB',
            'limit': limit,
            'show_to_affiliates': 'true',
        }
        
        for endpoint in endpoints:
            try:
                # ✅ Токен передаём ТОЛЬКО в заголовке
                headers = {'X-API-Token': TP_TOKEN}
                async with session.get(endpoint, params=params, headers=headers, timeout=30) as response:
                    logger.info(f"📡 {endpoint} → Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        flights = data.get('data', {})
                        deals = self._parse_api_flights(flights)
                        logger.info(f"✅ API вернул {len(deals)} предложений")
                        return self._filter_deals(deals)[:limit]
                    
                    elif response.status in [401, 403]:
                        logger.error(f"❌ Ошибка авторизации ({response.status}): проверьте токен и активацию программ")
                        break
                    
                    elif response.status == 404:
                        logger.warning(f"⚠️ 404 для {endpoint}")
                        continue
                        
            except Exception as e:
                logger.error(f"❌ Ошибка запроса: {e}")
                continue
        
        logger.warning("🔄 API не ответил, используем тестовые данные")
        return self._get_test_flights(limit)[:limit]
    
    def _parse_api_flights(self,  dict) -> List[Dict]:
        """Парсинг ответа API"""
        flights = data if isinstance(data, dict) else {}
        deals = []
        for key, flight in flights.items():
            if isinstance(flight, dict) and 'price' in flight:
                deal = {
                    'origin': flight.get('origin', 'MOW'),
                    'destination': flight.get('destination', ''),
                    'price': flight.get('price', 0),
                    'airline': flight.get('airline', ''),
                    'depart_date': flight.get('depart_date', ''),
                    'link': flight.get('link', ''),
                    'country_name': flight.get('destination', ''),
                    'hotel_name': '',
                    'nights': 7,
                    'hotel_rating': 0,
                    'departure_at': flight.get('depart_date', ''),
                }
                deals.append(deal)
        return deals
    
    def _get_test_flights(self, limit: int) -> List[Dict]:
        """Тестовые авиабилеты С ТРЕК-ССЫЛКАМИ"""
        shuffled = TEST_FLIGHTS.copy()
        random.shuffle(shuffled)
        for flight in shuffled:
            if flight.get('link'):
                flight['affiliate_link'] = self._add_tracker_link(flight['link'])
        return shuffled[:limit]
    
    def _get_test_tours(self, limit: int) -> List[Dict]:
        """Тестовые туры С ТРЕК-ССЫЛКАМИ"""
        shuffled = TEST_TOURS.copy()
        random.shuffle(shuffled)
        for tour in shuffled:
            if tour.get('link'):
                tour['affiliate_link'] = self._add_tracker_link(tour['link'])
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
            
            if deal.get('link') and not deal.get('affiliate_link'):
                deal['affiliate_link'] = self._add_tracker_link(deal['link'])
            
            filtered.append(deal)
        
        logger.info(f"✅ После фильтрации: {len(filtered)} предложений")
        return filtered
    
    def _add_tracker_link(self, url: str) -> str:
        """
        ✅ СОЗДАЁТ ПРАВИЛЬНУЮ ТРЕК-ССЫЛКУ С ПОЛНЫМ КОДИРОВАНИЕМ
        Формат: https://tp.media/click?sh=PARTNER_ID&subid=MARKER&u=FULLY_ENCODED_URL
        """
        if not url:
            return url
        
        partner_id = TP_PARTNER_ID
        if not partner_id:
            logger.error("❌ TP_PARTNER_ID не задан!")
            return url
        
        # ✅ Используем короткий маркер (не токен!)
        # Если TP_MARKER слишком длинный (>20 символов) — используем дефолтный
        raw_subid = TP_MARKER if TP_MARKER else 'telegram_auto'
        subid = raw_subid if len(raw_subid) <= 20 else 'telegram_auto'
        
        if len(raw_subid) > 20:
            logger.warning(f"⚠️ TP_MARKER слишком длинный ({len(raw_subid)} симв.), используем 'telegram_auto'")
        
        # ✅ ПОЛНОЕ кодирование целевой ссылки (все спецсимволы)
        encoded_url = urllib.parse.quote(url, safe='')
        
        # Формируем трек-ссылку
        tracker_url = f"https://tp.media/click?sh={partner_id}&subid={subid}&u={encoded_url}"
        
        logger.debug(f"🔗 Трек-ссылка: {tracker_url[:120]}...")
        return tracker_url
    
    def format_tour_post(self, item: Dict) -> Dict:
        from formatter import TourFormatter
        post_type = 'tour' if item.get('hotel_name') else 'flight'
        return TourFormatter.format(item, post_type=post_type)
    
    def format_flight_post(self, item: Dict) -> Dict:
        from formatter import TourFormatter
        return TourFormatter.format(item, post_type='flight')