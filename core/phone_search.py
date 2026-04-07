"""
⚠️ ПРАВОВАЯ ИНФОРМАЦИЯ ⚠️
Инструмент для работы с ОТКРЫТЫМИ ИСТОЧНИКАМИ (OSINT)
"""

import aiohttp
import re
import asyncio
from typing import Dict, Any, Optional, List
from rich.console import Console

from .search_result import SearchResult
from utils.proxy_manager import create_connector


class PhoneSearcher:
    """Поиск информации по номеру телефона"""
    
    def __init__(self, proxy: str = None, timeout: int = 15):
        self.proxy = proxy
        self.timeout = timeout
        self.console = Console()
    
    async def search(self, phone: str) -> SearchResult:
        """
        Поиск информации по номеру телефона
        
        Использует:
        - num.voxlink.ru - оператор, регион, страна
        - Проверка в мессенджерах
        - Определение региона по коду
        """
        
        # Нормализация номера
        original_phone = phone
        phone = self._normalize_phone(phone)
        
        results = {}
        
        # 1. Запрос к num.voxlink.ru (бесплатный, без ключа)
        voxlink_data = await self._check_voxlink(phone)
        if voxlink_data:
            results['voxlink'] = voxlink_data
        
        # 2. Проверка в мессенджерах
        messengers = self._check_messengers(phone)
        if messengers:
            results['messengers'] = messengers
        
        # 3. Информация о коде номера
        code_info = self._get_code_info(phone)
        if code_info:
            results['code_info'] = code_info
        
        # 4. Форматы номера
        results['formats'] = self._get_phone_formats(phone)
        
        return SearchResult(
            query=original_phone,
            mode='phone',
            found=results,
            total_checked=4
        )
    
    def _normalize_phone(self, phone: str) -> str:
        """Приведение номера к формату +7XXXXXXXXXX"""
        # Удаляем все нецифровые символы
        digits = re.sub(r'\D', '', phone)
        
        # Если начинается с 8, заменяем на 7
        if len(digits) == 11 and digits.startswith('8'):
            digits = '7' + digits[1:]
        
        # Если 10 цифр, добавляем 7
        if len(digits) == 10:
            digits = '7' + digits
        
        # Если 11 цифр и начинается с 7
        if len(digits) == 11 and digits.startswith('7'):
            return f"+{digits}"
        
        return f"+{digits}" if not phone.startswith('+') else phone
    
    async def _check_voxlink(self, phone: str) -> Optional[Dict]:
        """Запрос к num.voxlink.ru"""
        url = f"http://num.voxlink.ru/get/?num={phone}"
        
        try:
            connector = create_connector(self.proxy)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('result') == 'ok':
                            return {
                                'operator': data.get('operator', 'Неизвестно'),
                                'region': data.get('region', 'Неизвестно'),
                                'country': data.get('country', 'Неизвестно'),
                                'interested': data.get('interested', 0)
                            }
        except asyncio.TimeoutError:
            self.console.print("[dim]Таймаут при запросе к voxlink[/dim]")
        except Exception as e:
            self.console.print(f"[dim]Ошибка voxlink: {e}[/dim]")
        
        return None
    
    def _check_messengers(self, phone: str) -> Dict:
        """Генерация ссылок на мессенджеры"""
        clean_phone = phone.replace('+', '').replace(' ', '')
        return {
            'telegram': f"https://t.me/{clean_phone}",
            'whatsapp': f"https://wa.me/{clean_phone}",
            'viber': f"viber://chat?number=%2B{clean_phone}",
            'signal': f"https://signal.me/#p/%2B{clean_phone}"
        }
    
    def _get_code_info(self, phone: str) -> Optional[Dict]:
        """Определение информации по коду номера"""
        # Извлекаем код страны и оператора
        digits = re.sub(r'\D', '', phone)
        
        if len(digits) < 10:
            return None
        
        # Код страны
        country_code = digits[:-10] if len(digits) > 10 else '7'
        
        # Код оператора (первые 3 цифры после кода страны)
        operator_code = digits[-10:-7] if len(digits) >= 10 else digits[:3]
        
        # База кодов российских операторов
        russian_operators = {
            '900': 'МегаФон',
            '901': 'МегаФон',
            '902': 'МегаФон',
            '903': 'Билайн',
            '904': 'Билайн',
            '905': 'Билайн',
            '906': 'Билайн',
            '908': 'Билайн',
            '909': 'Билайн',
            '910': 'МТС',
            '911': 'МТС',
            '912': 'МТС',
            '913': 'МТС',
            '914': 'МТС',
            '915': 'МТС',
            '916': 'МТС',
            '917': 'МТС',
            '918': 'МТС',
            '919': 'МТС',
            '920': 'МегаФон',
            '921': 'МегаФон',
            '922': 'МегаФон',
            '923': 'МегаФон',
            '924': 'МегаФон',
            '925': 'МегаФон',
            '926': 'МегаФон',
            '927': 'МегаФон',
            '928': 'МегаФон',
            '929': 'МегаФон',
            '930': 'МегаФон',
            '931': 'МегаФон',
            '932': 'МегаФон',
            '933': 'МегаФон',
            '934': 'МегаФон',
            '936': 'МегаФон',
            '937': 'МегаФон',
            '938': 'МегаФон',
            '939': 'МегаФон',
            '941': 'МегаФон',
            '950': 'Tele2',
            '951': 'Tele2',
            '952': 'Tele2',
            '953': 'Tele2',
            '958': 'Tele2',
            '959': 'Tele2',
            '960': 'Билайн',
            '961': 'Билайн',
            '962': 'Билайн',
            '963': 'Билайн',
            '964': 'Билайн',
            '965': 'Билайн',
            '966': 'Билайн',
            '967': 'Билайн',
            '968': 'Билайн',
            '969': 'Билайн',
            '970': 'МТС',
            '971': 'МТС',
            '972': 'МТС',
            '973': 'МТС',
            '974': 'МТС',
            '975': 'МТС',
            '976': 'МТС',
            '977': 'МТС',
            '978': 'МТС',
            '979': 'МТС',
            '980': 'МТС',
            '981': 'МТС',
            '982': 'МТС',
            '983': 'МТС',
            '984': 'МТС',
            '985': 'МТС',
            '986': 'МТС',
            '987': 'МТС',
            '988': 'МТС',
            '989': 'МТС',
            '990': 'МегаФон',
            '991': 'МегаФон',
            '992': 'МегаФон',
            '993': 'МегаФон',
            '994': 'МегаФон',
            '995': 'МегаФон',
            '996': 'МегаФон',
            '997': 'МегаФон',
            '998': 'МегаФон',
            '999': 'МегаФон',
            '800': 'Бесплатный номер',
        }
        
        # Коды стран
        country_codes = {
            '7': 'Россия/Казахстан',
            '1': 'США/Канада',
            '380': 'Украина',
            '375': 'Беларусь',
            '998': 'Узбекистан',
            '996': 'Кыргызстан',
            '995': 'Грузия',
            '994': 'Азербайджан',
            '992': 'Таджикистан',
            '374': 'Армения',
            '373': 'Молдова',
            '372': 'Эстония',
            '371': 'Латвия',
            '370': 'Литва',
        }
        
        country = country_codes.get(country_code, 'Неизвестно')
        operator = russian_operators.get(operator_code, 'Неизвестно') if country_code == '7' else 'Неизвестно'
        
        return {
            'country_code': f"+{country_code}",
            'country': country,
            'operator_code': operator_code,
            'operator': operator,
            'number_length': len(digits)
        }
    
    def _get_phone_formats(self, phone: str) -> Dict:
        """Возвращает различные форматы номера"""
        digits = re.sub(r'\D', '', phone)
        
        formats = {
            'international': phone,
            'local': f"8{digits[-10:]}" if len(digits) >= 10 else digits,
            'e164': f"+{digits}",
            'digits_only': digits
        }
        
        # Форматирование для России
        if len(digits) == 11 and digits.startswith('7'):
            formats['russian'] = f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
        
        return formats
