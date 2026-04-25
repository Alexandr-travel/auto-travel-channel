import aiohttp
import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from config import TP_TOKEN, FILTERS, TEST_MODE

logger = logging.getLogger(__name__)

# ✅ ТЕСТОВЫЕ ДАННЫЕ: авиабилеты с ВАШИМИ рабочими короткими ссылками
# 🔗 Ваши ссылки:
# - https://aviasales.tpm.lv/DC4QzJuS?erid=2VtzqvfYndD
# - https://aviasales.tpm.lv/XGqJNaBP?erid=2VtzqvfYndD

TEST_FLIGHTS = [
    {
        'origin': 'MOW',
        'destination': 'DXB',
        'price': 25400,
        'airline': 'Аэрофлот',
        'depart_date': '2026-05-15',
        'return_date': '2026-05-22',
        # ✅ Ваша ссылка №1
        'link': 'https://aviasales.tpm.lv/DC4QzJuS?erid=2VtzqvfYndD',
        'country_name': 'ОАЭ',
        'city_name': 'Дубай',
    },
    {
        'origin': 'MOW',
        'destination': 'IST',
        'price': 18900,
        'airline': 'Turkish Airlines',
        'depart_date': '2026-05-20',
        'return_date': '2026-05-27',
        # ✅ Ваша ссылка №2
        'link': 'https://aviasales.tpm.lv/XGqJNaBP?erid=2VtzqvfYndD',
        'country_name': 'Турция',
        'city_name': 'Стамбул',
    },
    {
        'origin': 'MOW',
        'destination': 'BKK',
        'price': 32100,
        'airline': 'S7',
        'depart_date': '2026-06-01',
        'return_date': '2026-06-14',
        # ✅ Ваша ссылка №1 (повтор для разнообразия)
        'link': 'https://aviasales.tpm.lv/DC4QzJuS?erid=2VtzqvfYndD',
        'country_name': 'Таиланд',
        'city_name': 'Бангкок',
    },
    {
        'origin': 'LED',
        'destination': 'AER',
        'price': 8900,
        'airline': 'Победа',
        'depart_date': '2026-05-25',
        'return_date': '2026-06-01',
        # ✅ Ваша ссылка №2 (повтор)
        'link': 'https://aviasales.tpm.lv/XGqJNaBP?erid=2VtzqvfYndD',
        'country_name': 'Россия',
        'city_name': 'Сочи',
    },
    {
        'origin': 'MOW',
        'destination': 'TBS',
        'price': 12300,
        'airline': 'Georgian Airways',
        'depart_date': '2026-06-10',
        'return_date': '2026-06-17',
        # ✅ Ваша ссылка №1
        'link': 'https://aviasales.tpm.lv/DC4QzJuS?erid=2VtzqvfYndD',
        'country_name': 'Грузия',
        'city_name': 'Тбилиси',
    },
    {
        'origin': 'SVX',
        'destination': 'HKT',
        'price': 38900,
        'airline': 'Azur Air',
        'depart_date': '2026-06-15',
        'return_date': '2026-06-29',
        # ✅ Ваша ссылка №2
        'link': 'https://aviasales.tpm.lv/XGqJNaBP?erid=2VtzqvfYndD',
        'country_name': 'Таиланд',
        'city_name': 'Пхукет',
    },
    {
        'origin': 'KZN',
        'destination': 'GOA',
        'price': 28900,
        'airline': 'Air India',
        'depart_date': '2026-07-01',
        'return_date': '2026-07-14',
        # ✅ Ваша ссылка №1
        'link': 'https://aviasales.tpm.lv/DC4QzJuS?erid=2VtzqvfYndD',
        'country_name': 'Индия',
        'city_name': 'Гоа',
    },
    {
        'origin': 'MOW',
        'destination': 'EVN',
        'price': 15600,
        'airline': 'Armenian Airlines',
        'depart_date': '2026-05-28',
        'return_date': '2026-06-04',
        # ✅ Ваша ссылка №2
        'link': 'https://aviasales.tpm.lv/XGqJNaBP?erid=2VtzqvfYndD',
        'country_name': 'Армения',
        'city_name': 'Ереван',
    },
]

# Названия городов для отображения
CITY_NAMES = {
    'MOW': 'Москва',
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
    'AYT': 'Анталья',
    'SSH': 'Шарм-эль-Шейх',
}


class FlightParser:
    """Парсер авиабилетов для авто-канала"""
    
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
            logger.info("🧪 TEST_MODE: используем тестовые авиабилеты")
            return self._get_test_flights(limit)
        
        # ✅ Реальный API (заглушка — раскомментируйте, когда заработает)
        # return await self._fetch_from_api(limit)
        return self._get_test_flights(limit)
    
    async def _fetch_from_api(self, limit: int) -> List[Dict]:
        """Реальный запрос к API Aviasales (заглушка)"""
        logger.info("📡 Запрос к реальному API...")
        # Пока возвращаем тестовые данные
        return self._get_test_flights(limit)
    
    def _get_test_flights(self, limit: int) -> List[Dict]:
        """Возвращает тестовые авиабилеты с вашими ссылками"""
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
            
            # Фильтр по цене
            if not (FILTERS['min_price'] <= price <= FILTERS['max_price']):
                continue
            
            # Фильтр по городам вылета
            if FILTERS['origins'] and origin not in FILTERS['origins']:
                continue
            
            # Фильтр по направлениям (если задан)
            if FILTERS['destinations'] and destination not in FILTERS['destinations']:
                continue
            
            # Фильтр по авиакомпаниям (если задан)
            if FILTERS['airlines'] and flight.get('airline') not in FILTERS['airlines']:
                continue
            
            filtered.append(flight)
        
        logger.info(f"✅ После фильтрации: {len(filtered)} авиабилетов")
        return filtered
    
    def format_flight_post(self, flight: Dict) -> Dict:
        """Форматирование авиабилета для поста"""
        from formatter import FlightFormatter
        return FlightFormatter.format(flight)