import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from config import TP_TOKEN, TP_MARKER, FILTERS

logger = logging.getLogger(__name__)

class TravelPayoutsParser:
    """Парсер предложений из API TravelPayouts"""
    
    def __init__(self):
        self.base_url = 'https://api.travelpayouts.com'
        # ✅ API-токен передаётся через заголовок или параметр
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
        """
        Получение выгодных авиабилетов (Aviasales API через TravelPayouts)
        ✅ Использует рабочий эндпоинт
        """
        logger.info(f"🔍 Запрос авиабилетов: limit={limit}, origin=MOW")
        
        session = await self.get_session()
        
        # ✅ РАБОЧИЙ эндпоинт для авиабилетов
        url = f'{self.base_url}/aviasales/v1/prices/direct'
        params = {
            'origin': 'MOW',  # Москва как точка вылета
            'currency': 'RUB',
            'limit': limit,
            'show_to_affiliates': 'true',
            'token': TP_TOKEN,  # ✅ Токен как параметр (надёжнее)
        }
        
        logger.info(f"📡 URL: {url}")
        logger.info(f"📡 Params: {params}")
        
        try:
            async with session.get(url, params=params, timeout=30) as response:
                logger.info(f"📡 Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    flights = data.get('data', [])
                    
                    # Преобразуем формат API в наш внутренний
                    deals = []
                    for key, flight in flights.items():
                        if isinstance(flight, dict) and 'price' in flight:
                            deal = {
                                'origin': flight.get('origin', 'MOW'),
                                'destination': flight.get('destination', ''),
                                'price': flight.get('price', 0),
                                'airline': flight.get('airline', ''),
                                'depart_date': flight.get('depart_date', ''),
                                'return_date': flight.get('return_date', ''),
                                'link': flight.get('link', ''),
                                'country_name': flight.get('destination', ''),
                                'city_name': '',
                                'hotel_name': '',
                                'nights': 7,
                                'hotel_rating': 0,
                                'departure_at': flight.get('depart_date', ''),
                            }
                            deals.append(deal)
                    
                    logger.info(f"✅ API вернул {len(deals)} авиабилетов")
                    return self._filter_deals(deals)
                else:
                    logger.error(f"❌ API вернул статус {response.status}")
                    # Попробуем альтернативный эндпоинт
                    return await self._fetch_fallback_deals(limit)
                    
        except aiohttp.ClientResponseError as e:
            logger.error(f"❌ HTTP ошибка: {e.status} {e.message}")
            return await self._fetch_fallback_deals(limit)
        except Exception as e:
            logger.error(f"❌ Ошибка запроса: {type(e).__name__}: {e}")
            return []
    
    async def _fetch_fallback_deals(self, limit: int) -> List[Dict]:
        """
        Альтернативный эндпоинт: популярные направления
        ✅ Работает как запасной вариант
        """
        logger.info("🔄 Пробуем альтернативный эндпоинт: popular_routes")
        
        session = await self.get_session()
        url = f'{self.base_url}/v1/subscription/popular_routes'
        params = {
            'origin': 'MOW',
            'currency': 'RUB',
            'limit': limit,
            'token': TP_TOKEN,
        }
        
        try:
            async with session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    routes = data.get('data', [])
                    
                    deals = []
                    for route in routes:
                        deal = {
                            'origin': route.get('origin', 'MOW'),
                            'destination': route.get('destination', ''),
                            'price': route.get('price', route.get('value', 0)),
                            'airline': '',
                            'depart_date': route.get('depart_date', ''),
                            'return_date': '',
                            'link': route.get('link', ''),
                            'country_name': route.get('destination', ''),
                            'city_name': '',
                            'hotel_name': '',
                            'nights': 7,
                            'hotel_rating': 0,
                            'departure_at': route.get('depart_date', ''),
                        }
                        deals.append(deal)
                    
                    logger.info(f"✅ Fallback вернул {len(deals)} предложений")
                    return self._filter_deals(deals)
        except Exception as e:
            logger.error(f"❌ Fallback ошибка: {e}")
        
        return []
    
    async def fetch_flight_deals(self, limit: int = 10) -> List[Dict]:
        """Получение авиабилетов (дублирует fetch_hot_deals для совместимости)"""
        return await self.fetch_hot_deals(limit)
    
    def _filter_deals(self, deals: List[Dict]) -> List[Dict]:
        """Фильтрация предложений по настройкам"""
        logger.info(f"🔎 Фильтрация {len(deals)} предложений...")
        filtered = []
        
        for deal in deals:
            price = deal.get('price', 0)
            destination = deal.get('destination', '')
            
            # Применяем фильтры
            if not (FILTERS['min_price'] <= price <= FILTERS['max_price']):
                continue
            
            # Фильтр по странам (если задан)
            if FILTERS['countries'] and destination not in FILTERS['countries']:
                continue
            
            # Добавляем маркер в ссылку
            if deal.get('link'):
                deal['affiliate_link'] = self._add_marker(deal['link'])
            
            filtered.append(deal)
        
        logger.info(f"✅ После фильтрации: {len(filtered)} предложений")
        return filtered[:5]  # Возвращаем топ-5
    
    def _add_marker(self, url: str) -> str:
        """Добавление маркера партнёра в ссылку"""
        if not url or not TP_MARKER or TP_MARKER in url:
            return url
        
        # Определяем разделитель
        separator = '&' if '?' in url else '?'
        
        # Некоторые программы используют subid вместо marker
        # Пробуем оба варианта
        return f"{url}{separator}marker={TP_MARKER}"
    
    def format_tour_post(self, item: Dict) -> Dict:
        """Форматирование предложения для поста (универсальное)"""
        from formatter import TourFormatter
        # Определяем тип: если есть hotel_name — тур, иначе авиа
        post_type = 'tour' if item.get('hotel_name') else 'flight'
        return TourFormatter.format(item, post_type=post_type)
    
    def format_flight_post(self, item: Dict) -> Dict:
        """Форматирование авиабилета для поста"""
        from formatter import TourFormatter
        return TourFormatter.format(item, post_type='flight')