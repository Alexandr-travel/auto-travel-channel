import aiohttp
import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from config import TP_TOKEN, FILTERS, TEST_MODE

logger = logging.getLogger(__name__)

# ✅ ТЕСТОВЫЕ ДАННЫЕ: авиабилеты с ВАШИМИ рабочими ссылками
TEST_FLIGHTS = [
    {
        'origin': 'MOW', 'destination': 'DXB', 'price': 25400,
        'airline': 'Аэрофлот', 'depart_date': '2026-05-15',
        'return_date': '2026-05-22',
        'link': 'https://aviasales.tpm.lv/DC4QzJuS?erid=2VtzqvfYndD',
        'country_name': 'ОАЭ', 'city_name': 'Дубай',
    },
    {
        'origin': 'MOW', 'destination': 'IST', 'price': 18900,
        'airline': 'Turkish Airlines', 'depart_date': '2026-05-20',
        'return_date': '2026-05-27',
        'link': 'https://aviasales.tpm.lv/XGqJNaBP?erid=2VtzqvfYndD',
        'country_name': 'Турция', 'city_name': 'Стамбул',
    },
    {
        'origin': 'MOW', 'destination': 'BKK', 'price': 32100,
        'airline': 'S7', 'depart_date': '2026-06-01',
        'return_date': '2026-06-14',
        'link': 'https://aviasales.tpm.lv/DC4QzJuS?erid=2VtzqvfYndD',
        'country_name': 'Таиланд', 'city_name': 'Бангкок',
    },
    {
        'origin': 'LED', 'destination': 'AER', 'price': 8900,
        'airline': 'Победа', 'depart_date': '2026-05-25',
        'return_date': '2026-06-01',
        'link': 'https://aviasales.tpm.lv/XGqJNaBP?erid=2VtzqvfYndD',
        'country_name': 'Россия', 'city_name': 'Сочи',
    },
    {
        'origin': 'MOW', 'destination': 'TBS', 'price': 12300,
        'airline': 'Georgian Airways', 'depart_date': '2026-06-10',
        'return_date': '2026-06-17',
        'link': 'https://aviasales.tpm.lv/DC4QzJuS?erid=2VtzqvfYndD',
        'country_name': 'Грузия', 'city_name': 'Тбилиси',
    },
    {
        'origin': 'SVX', 'destination': 'HKT', 'price': 38900,
        'airline': 'Azur Air', 'depart_date': '2026-06-15',
        'return_date': '2026-06-29',
        'link': 'https://aviasales.tpm.lv/XGqJNaBP?erid=2VtzqvfYndD',
        'country_name': 'Таиланд', 'city_name': 'Пхукет',
    },
    {
        'origin': 'KZN', 'destination': 'GOA', 'price': 28900,
        'airline': 'Air India', 'depart_date': '2026-07-01',
        'return_date': '2026-07-14',
        'link': 'https://aviasales.tpm.lv/DC4QzJuS?erid=2VtzqvfYndD',
        'country_name': 'Индия', 'city_name': 'Гоа',
    },
    {
        'origin': 'MOW', 'destination': 'EVN', 'price': 15600,
        'airline': 'Armenian Airlines', 'depart_date': '2026-05-28',
        'return_date': '2026-06-04',
        'link': 'https://aviasales.tpm.lv/XGqJNaBP?erid=2VtzqvfYndD',
        'country_name': 'Армения', 'city_name': 'Ереван',
    },
]

CITY_NAMES = {
    'MOW': 'Москва', 'LED': 'Санкт-Петербург', 'SVX': 'Екатеринбург',
    'KZN': 'Казань', 'DXB': 'Дубай', 'IST': 'Стамбул', 'BKK': 'Бангкок',
    'HKT': 'Пхукет', 'AER': 'Сочи', 'TBS': 'Тбилиси', 'EVN': 'Ереван',
    'GOA': 'Гоа', 'AYT': 'Анталья', 'SSH': 'Шарм-эль-Шейх',
}


class FlightParser:
    """Парсер авиабилетов"""
    
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
    
    async def fetch_flights(self, limit: int = 10) -> List[Dict]:
        logger.info(f"✈️ Запрос авиабилетов: limit={limit}, TEST_MODE={TEST_MODE}")
        
        if TEST_MODE:
            logger.info("🧪 TEST_MODE: используем тестовые авиабилеты")
            return self._get_test_flights(limit)
        
        return self._get_test_flights(limit)  # Заглушка
    
    def _get_test_flights(self, limit: int) -> List[Dict]:
        """Возвращает тестовые авиабилеты"""
        shuffled = TEST_FLIGHTS.copy()
        random.shuffle(shuffled)
        
        for flight in shuffled:
            if flight.get('link'):
                flight['affiliate_link'] = flight['link']
        
        return self._filter_flights(shuffled)[:limit]
    
    def _filter_flights(self, flights: List[Dict]) -> List[Dict]:
        """Фильтрация с ДЕТАЛЬНЫМ ЛОГИРОВАНИЕМ"""
        logger.info(f"🔎 Фильтрация {len(flights)} авиабилетов...")
        logger.debug(f"🔧 Фильтры: {FILTERS}")
        
        filtered = []
        
        for i, flight in enumerate(flights):
            price = flight.get('price', 0)
            origin = flight.get('origin', '')
            destination = flight.get('destination', '')
            airline = flight.get('airline', '')
            
            logger.debug(f"  [{i}] {origin}→{destination} | {airline} | {price}₽")
            
            # Фильтр по цене
            if not (FILTERS['min_price'] <= price <= FILTERS['max_price']):
                logger.debug(f"      ❌ Отброшен по цене: {price}₽ не в [{FILTERS['min_price']}, {FILTERS['max_price']}]")
                continue
            
            # Фильтр по городам вылета (если задан)
            if FILTERS['origins'] and origin not in FILTERS['origins']:
                logger.debug(f"      ❌ Отброшен по origin: {origin} не в {FILTERS['origins']}")
                continue
            
            # Фильтр по направлениям (если задан)
            if FILTERS['destinations'] and destination not in FILTERS['destinations']:
                logger.debug(f"      ❌ Отброшен по destination: {destination} не в {FILTERS['destinations']}")
                continue
            
            # Фильтр по авиакомпаниям (если задан)
            if FILTERS['airlines'] and airline not in FILTERS['airlines']:
                logger.debug(f"      ❌ Отброшен по airline: {airline} не в {FILTERS['airlines']}")
                continue
            
            logger.debug(f"      ✅ Прошёл фильтрацию")
            filtered.append(flight)
        
        logger.info(f"✅ После фильтрации: {len(filtered)} из {len(flights)} авиабилетов")
        return filtered
    
    def format_flight_post(self, flight: Dict) -> Dict:
        from formatter import FlightFormatter
        return FlightFormatter.format(flight)