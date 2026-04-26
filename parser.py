import aiohttp
import asyncio
import logging
import random
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from config import TP_TOKEN, FILTERS, TEST_MODE

logger = logging.getLogger(__name__)

# ✅ ТЕСТОВЫЕ ДАННЫЕ: Москва ↔ Нячанг (Камрань)
# 🔗 Ваши рабочие ссылки:
# - Москва → Нячанг: https://aviasales.tpm.lv/jocJAnWm?erid=2VtzqvfYndD
# - Нячанг → Москва: https://aviasales.tpm.lv/YsBVke5L?erid=2VtzqvfYndD

TEST_FLIGHTS = [
    # ✅ МОСКВА → НЯЧАНГ
    {
        'origin': 'MOW',
        'destination': 'CXR',
        'price': 45900,
        'airline': 'Аэрофлот + Vietnam Airlines',
        'depart_date': '2026-11-15',
        'return_date': '2026-11-29',
        # ✅ Ваша ссылка №1: Москва → Нячанг
        'link': 'https://aviasales.tpm.lv/jocJAnWm?erid=2VtzqvfYndD',
        'country_name': 'Вьетнам',
        'city_name': 'Нячанг',
    },
    {
        'origin': 'MOW',
        'destination': 'CXR',
        'price': 48500,
        'airline': 'S7 + Vietnam Airlines',
        'depart_date': '2026-12-01',
        'return_date': '2026-12-15',
        # ✅ Ваша ссылка №1: Москва → Нячанг
        'link': 'https://aviasales.tpm.lv/jocJAnWm?erid=2VtzqvfYndD',
        'country_name': 'Вьетнам',
        'city_name': 'Нячанг',
    },
    {
        'origin': 'MOW',
        'destination': 'CXR',
        'price': 52300,
        'airline': 'Turkish Airlines + Vietnam Airlines',
        'depart_date': '2026-12-20',
        'return_date': '2027-01-10',
        # ✅ Ваша ссылка №1: Москва → Нячанг
        'link': 'https://aviasales.tpm.lv/jocJAnWm?erid=2VtzqvfYndD',
        'country_name': 'Вьетнам',
        'city_name': 'Нячанг',
    },
    {
        'origin': 'MOW',
        'destination': 'CXR',
        'price': 47800,
        'airline': 'China Southern + Vietnam Airlines',
        'depart_date': '2027-01-15',
        'return_date': '2027-01-29',
        # ✅ Ваша ссылка №1: Москва → Нячанг
        'link': 'https://aviasales.tpm.lv/jocJAnWm?erid=2VtzqvfYndD',
        'country_name': 'Вьетнам',
        'city_name': 'Нячанг',
    },
    
    # ✅ НЯЧАНГ → МОСКВА
    {
        'origin': 'CXR',
        'destination': 'MOW',
        'price': 47200,
        'airline': 'Vietnam Airlines + Аэрофлот',
        'depart_date': '2026-11-20',
        'return_date': '2026-12-05',
        # ✅ Ваша ссылка №2: Нячанг → Москва
        'link': 'https://aviasales.tpm.lv/YsBVke5L?erid=2VtzqvfYndD',
        'country_name': 'Россия',
        'city_name': 'Москва',
    },
    {
        'origin': 'CXR',
        'destination': 'MOW',
        'price': 49800,
        'airline': 'Vietnam Airlines + S7',
        'depart_date': '2026-12-10',
        'return_date': '2026-12-25',
        # ✅ Ваша ссылка №2: Нячанг → Москва
        'link': 'https://aviasales.tpm.lv/YsBVke5L?erid=2VtzqvfYndD',
        'country_name': 'Россия',
        'city_name': 'Москва',
    },
    {
        'origin': 'CXR',
        'destination': 'MOW',
        'price': 55600,
        'airline': 'Vietnam Airlines + Turkish Airlines',
        'depart_date': '2026-12-28',
        'return_date': '2027-01-15',
        # ✅ Ваша ссылка №2: Нячанг → Москва
        'link': 'https://aviasales.tpm.lv/YsBVke5L?erid=2VtzqvfYndD',
        'country_name': 'Россия',
        'city_name': 'Москва',
    },
    {
        'origin': 'CXR',
        'destination': 'MOW',
        'price': 51200,
        'airline': 'Vietnam Airlines + China Southern',
        'depart_date': '2027-01-20',
        'return_date': '2027-02-05',
        # ✅ Ваша ссылка №2: Нячанг → Москва
        'link': 'https://aviasales.tpm.lv/YsBVke5L?erid=2VtzqvfYndD',
        'country_name': 'Россия',
        'city_name': 'Москва',
    },
]

# Названия городов
CITY_NAMES = {
    'MOW': 'Москва',
    'CXR': 'Нячанг (Камрань)',
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


class FlightParser:
    """Парсер авиабилетов Москва ↔ Нячанг"""
    
    def __init__(self):
        self.base_url = 'https://api.travelpayouts.com'
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Получение или создание сессии"""
        if self.session is None or self.session.closed:
            headers = {'X-API-Token': TP_TOKEN} if TP_TOKEN else {}
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session
    
    async def close(self):
        """Закрытие сессии"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def fetch_flights(self, limit: int = 10) -> List[Dict]:
        """Получение списка авиабилетов"""
        logger.info(f"✈️ Запрос авиабилетов: limit={limit}, TEST_MODE={TEST_MODE}")
        
        # ✅ В тестовом режиме возвращаем тестовые данные с вашими ссылками
        if TEST_MODE:
            logger.info("🧪 TEST_MODE: используем тестовые авиабилеты Москва ↔ Нячанг")
            return self._get_test_flights(limit)
        
        # ✅ Реальный API (раскомментируйте, когда заработает)
        # return await self._fetch_from_api(limit)
        return self._get_test_flights(limit)
    
    async def _fetch_from_api(self, limit: int) -> List[Dict]:
        """Реальный запрос к API Aviasales (заглушка)"""
        logger.info("📡 Запрос к реальному API...")
        # Пока возвращаем тестовые данные
        return self._get_test_flights(limit)
    
    def _get_test_flights(self, limit: int) -> List[Dict]:
        """Возвращает тестовые авиабилеты с вашими рабочими ссылками"""
        shuffled = TEST_FLIGHTS.copy()
        random.shuffle(shuffled)
        
        # ✅ Ссылки уже содержат трекинг — просто копируем в affiliate_link
        for flight in shuffled:
            if flight.get('link'):
                flight['affiliate_link'] = flight['link']
        
        return self._filter_flights(shuffled)[:limit]
    
    def _filter_flights(self, flights: List[Dict]) -> List[Dict]:
        """Фильтрация авиабилетов по настройкам"""
        logger.info(f"🔎 Фильтрация {len(flights)} авиабилетов...")
        filtered = []
        
        for flight in flights:
            price = flight.get('price', 0)
            origin = flight.get('origin', '')
            destination = flight.get('destination', '')
            airline = flight.get('airline', '')
            
            # Фильтр по цене
            if not (FILTERS['min_price'] <= price <= FILTERS['max_price']):
                continue
            
            # Фильтр по городам вылета
            if FILTERS['origins'] and origin not in FILTERS['origins']:
                continue
            
            # Фильтр по направлениям
            if FILTERS['destinations'] and destination not in FILTERS['destinations']:
                continue
            
            # Фильтр по авиакомпаниям
            if FILTERS['airlines'] and airline not in FILTERS['airlines']:
                continue
            
            filtered.append(flight)
        
        logger.info(f"✅ После фильтрации: {len(filtered)} из {len(flights)} авиабилетов")
        return filtered
    
    def format_flight_post(self, flight: Dict) -> Dict:
        """Форматирование авиабилета для поста"""
        from formatter import FlightFormatter
        return FlightFormatter.format(flight)