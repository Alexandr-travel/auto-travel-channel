import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from config import TP_TOKEN, TP_MARKER, FILTERS

class TravelPayoutsParser:
    """Парсер горящих туров из API TravelPayouts"""
    
    def __init__(self):
        self.base_url = 'https://api.travelpayouts.com'
        self.headers = {'X-API-Token': TP_TOKEN}
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def fetch_hot_deals(self, limit: int = 10) -> List[Dict]:
        """Получение горящих туров (Level.Travel / Travelata)"""
        session = await self.get_session()
        
        # API для поиска туров
        url = f'{self.base_url}/data/v2/search/advices'
        params = {
            'marker': TP_MARKER,
            'limit': limit,
            'currency': 'RUB',
            'origin': 'MOW',  # Москва как точка вылета
        }
        
        try:
            async with session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    deals = data.get('data', [])
                    return self._filter_deals(deals)
                return []
        except Exception as e:
            print(f"❌ Ошибка парсинга туров: {e}")
            return []
    
    async def fetch_flight_deals(self, limit: int = 10) -> List[Dict]:
        """Получение выгодных авиабилетов (Aviasales)"""
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
                    return self._filter_flights(flights)
                return []
        except Exception as e:
            print(f"❌ Ошибка парсинга авиа: {e}")
            return []
    
    def _filter_deals(self, deals: List[Dict]) -> List[Dict]:
        """Фильтрация туров по настройкам"""
        filtered = []
        
        for deal in deals:
            price = deal.get('price', 0)
            country = deal.get('country_name', '')
            rating = deal.get('hotel_rating', 5)
            nights = deal.get('nights', 7)
            
            # Применяем фильтры
            if not (FILTERS['min_price'] <= price <= FILTERS['max_price']):
                continue
            if country and country not in FILTERS['countries']:
                continue
            if rating < FILTERS['min_rating']:
                continue
            if not (FILTERS['nights_min'] <= nights <= FILTERS['nights_max']):
                continue
            
            # Добавляем маркер в ссылку
            if 'link' in deal:
                deal['affiliate_link'] = self._add_marker(deal['link'])
            
            filtered.append(deal)
        
        return filtered[:5]  # Возвращаем топ-5
    
    def _filter_flights(self, flights: List[Dict]) -> List[Dict]:
        """Фильтрация авиабилетов"""
        filtered = []
        
        for flight in flights:
            price = flight.get('price', 0)
            if FILTERS['min_price'] <= price <= FILTERS['max_price']:
                if 'link' in flight:
                    flight['affiliate_link'] = self._add_marker(flight['link'])
                filtered.append(flight)
        
        return filtered[:3]  # Топ-3 авиа
    
    def _add_marker(self, url: str) -> str:
        """Добавление маркера партнёра в ссылку"""
        if not url or TP_MARKER in url:
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