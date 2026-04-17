import aiohttp
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional
from config import TP_TOKEN, TP_MARKER, FILTERS

logger = logging.getLogger(__name__)

class TravelPayoutsParser:
    """Парсер горящих туров из API TravelPayouts"""
    
    def __init__(self):
        self.base_url = 'https://api.travelpayouts.com'
        self.headers = {'X-API-Token': TP_TOKEN} if TP_TOKEN else {}
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def fetch_hot_deals(self, limit: int = 10) -> List[Dict]:
        """Получение горящих туров"""
        logger.info(f"🔍 Запрос туров: limit={limit}")
        
        session = await self.get_session()
        url = f'{self.base_url}/data/v2/search/advices'
        params = {
            'marker': TP_MARKER,
            'limit': limit,
            'currency': 'RUB',
            'origin': 'MOW',
        }
        
        logger.info(f"📡 URL: {url}")
        logger.info(f"📡 Params: {params}")
        
        try:
            async with session.get(url, params=params, timeout=30) as response:
                logger.info(f"📡 Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    deals = data.get('data', [])
                    logger.info(f"✅ API вернул {len(deals)} туров")
                    return self._filter_deals(deals)
                else:
                    logger.error(f"❌ API вернул статус {response.status}")
                    return []
        except Exception as e:
            logger.error(f"❌ Ошибка запроса: {type(e).__name__}: {e}")
            return []
    
    async def fetch_flight_deals(self, limit: int = 10) -> List[Dict]:
        """Получение выгодных авиабилетов"""
        logger.info(f"✈️ Запрос авиабилетов: limit={limit}")
        
        session = await self.get_session()
        url = f'{self.base_url}/aviasales/v1/prices/direct'
        params = {
            'origin': 'MOW',
            'currency': 'RUB',
            'limit': limit,
            'show_to_affiliates': 'true',
        }
        
        try:
            async with session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    flights = data.get('data', [])
                    logger.info(f"✅ API вернул {len(flights)} авиабилетов")
                    return self._filter_flights(flights)
                return []
        except Exception as e:
            logger.error(f"❌ Ошибка запроса авиа: {e}")
            return []
    
    def _filter_deals(self, deals: List[Dict]) -> List[Dict]:
        """Фильтрация туров по настройкам"""
        logger.info(f"🔎 Фильтрация {len(deals)} туров...")
        filtered = []
        
        for deal in deals:
            price = deal.get('price', 0)
            country = deal.get('country_name', '')
            rating = deal.get('hotel_rating', 5)
            nights = deal.get('nights', 7)
            
            if not (FILTERS['min_price'] <= price <= FILTERS['max_price']):
                continue
            if FILTERS['countries'] and country not in FILTERS['countries']:
                continue
            if rating < FILTERS['min_rating']:
                continue
            if not (FILTERS['nights_min'] <= nights <= FILTERS['nights_max']):
                continue
            
            if 'link' in deal:
                deal['affiliate_link'] = self._add_marker(deal['link'])
            
            filtered.append(deal)
        
        logger.info(f"✅ После фильтрации: {len(filtered)} туров")
        return filtered[:5]
    
    def _filter_flights(self, flights: List[Dict]) -> List[Dict]:
        """Фильтрация авиабилетов"""
        filtered = []
        
        for flight in flights:
            price = flight.get('price', 0)
            if FILTERS['min_price'] <= price <= FILTERS['max_price']:
                if 'link' in flight:
                    flight['affiliate_link'] = self._add_marker(flight['link'])
                filtered.append(flight)
        
        return filtered[:3]
    
    def _add_marker(self, url: str) -> str:
        """Добавление маркера партнёра в ссылку"""
        if not url or not TP_MARKER or TP_MARKER in url:
            return url
        separator = '&' if '?' in url else '?'
        return f"{url}{separator}marker={TP_MARKER}"
    
    def format_tour_post(self, tour: Dict) -> Dict:
        """Форматирование тура для поста"""
        from formatter import TourFormatter
        return TourFormatter.format(tour, post_type='tour')
    
    def format_flight_post(self, flight: Dict) -> Dict:
        """Форматирование авиабилета для поста"""
        from formatter import TourFormatter
        return TourFormatter.format(flight, post_type='flight')