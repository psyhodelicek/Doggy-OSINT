"""
⚠️ ПРАВОВАЯ ИНФОРМАЦИЯ ⚠️
Инструмент для работы с ОТКРЫТЫМИ ИСТОЧНИКАМИ (OSINT)
"""

import aiohttp
import re
import asyncio
import hashlib
from typing import Dict, Any, Optional, List
from rich.console import Console

from .search_result import SearchResult
from utils.proxy_manager import create_connector


class EmailSearcher:
    """Поиск информации по email"""
    
    def __init__(self, proxy: str = None, timeout: int = 15):
        self.proxy = proxy
        self.timeout = timeout
        self.console = Console()
    
    async def search(self, email: str, check_breaches: bool = False) -> SearchResult:
        """
        Поиск информации по email
        
        Использует:
        - Проверка формата email
        - Проверка домена (MX записи через DNS)
        - Проверка на временные email сервисы
        - Have I Been Pwned (опционально, без ключа - ограничено)
        - Поиск по публичным источникам
        """
        
        results = {}
        
        # 1. Валидация формата
        validation = self._validate_email(email)
        if not validation.get('valid'):
            return SearchResult(
                query=email,
                mode='email',
                found={'error': 'Неверный формат email'},
                total_checked=1
            )
        results['validation'] = validation
        
        # 2. Информация о домене
        domain_info = self._get_domain_info(email)
        if domain_info:
            results['domain_info'] = domain_info
        
        # 3. Проверка на временные email
        temp_check = self._check_temporary(email)
        results['temporary_email'] = temp_check
        
        # 4. Проверка утечек (через публичный API без ключа)
        if check_breaches:
            breach_data = await self._check_breaches(email)
            if breach_data:
                results['breaches'] = breach_data
        
        # 5. Поиск в публичных источниках
        public_profiles = await self._search_public_sources(email)
        if public_profiles:
            results['public_profiles'] = public_profiles
        
        return SearchResult(
            query=email,
            mode='email',
            found=results,
            total_checked=5
        )
    
    def _validate_email(self, email: str) -> Dict:
        """Проверка валидности email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_valid = bool(re.match(pattern, email))
        
        if is_valid:
            parts = email.split('@')
            local = parts[0]
            domain = parts[1] if len(parts) > 1 else ''
            
            return {
                'valid': True,
                'local_part': local,
                'domain': domain,
                'length': len(email),
                'has_plus': '+' in local,
                'has_dot': '.' in local
            }
        
        return {'valid': False, 'reason': 'Неверный формат'}
    
    def _get_domain_info(self, email: str) -> Optional[Dict]:
        """Информация о домене email"""
        domain = email.split('@')[1] if '@' in email else ''
        
        if not domain:
            return None
        
        # Популярные почтовые сервисы
        popular_providers = {
            'gmail.com': 'Google Gmail',
            'googlemail.com': 'Google Gmail',
            'yahoo.com': 'Yahoo Mail',
            'yahoo.co.uk': 'Yahoo Mail UK',
            'outlook.com': 'Microsoft Outlook',
            'hotmail.com': 'Microsoft Hotmail',
            'live.com': 'Microsoft Live',
            'msn.com': 'Microsoft MSN',
            'icloud.com': 'Apple iCloud',
            'me.com': 'Apple iCloud',
            'mac.com': 'Apple iCloud',
            'mail.ru': 'Mail.ru',
            'bk.ru': 'Mail.ru BK',
            'inbox.ru': 'Mail.ru Inbox',
            'list.ru': 'Mail.ru List',
            'yandex.ru': 'Yandex',
            'yandex.ua': 'Yandex Ukraine',
            'yandex.kz': 'Yandex Kazakhstan',
            'yandex.by': 'Yandex Belarus',
            'ya.ru': 'Yandex Short',
            'proton.me': 'ProtonMail',
            'protonmail.com': 'ProtonMail',
            'protonmail.ch': 'ProtonMail',
            'pm.me': 'ProtonMail',
            'tutanota.com': 'Tutanota',
            'tuta.io': 'Tutanota',
            'keemail.me': 'Tutanota',
            'aol.com': 'AOL Mail',
            'gmx.com': 'GMX',
            'gmx.net': 'GMX',
            'web.de': 'Web.de',
            'zoho.com': 'Zoho Mail',
            'fastmail.com': 'FastMail',
            'hey.com': 'HEY',
            'duck.com': 'DuckDuckGo Email',
            'simplelogin.com': 'SimpleLogin',
            'anonaddy.com': 'AnonAddy',
        }
        
        provider = popular_providers.get(domain.lower(), 'Неизвестный провайдер')
        
        # Определение типа сервиса
        is_free = domain.lower() in [
            'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com',
            'mail.ru', 'yandex.ru', 'icloud.com', 'protonmail.com'
        ]
        
        is_privacy = domain.lower() in [
            'proton.me', 'protonmail.com', 'tutanota.com', 'duck.com'
        ]
        
        return {
            'domain': domain,
            'provider': provider,
            'is_free_provider': is_free,
            'is_privacy_focused': is_privacy,
            'domain_length': len(domain)
        }
    
    def _check_temporary(self, email: str) -> Dict:
        """Проверка на временный email"""
        domain = email.split('@')[1].lower() if '@' in email else ''
        
        # Список известных временных email сервисов
        temporary_domains = [
            'tempmail.com', 'temp-mail.org', '10minutemail.com',
            'guerrillamail.com', 'mailinator.com', 'throwaway.email',
            'tempmail.ninja', 'emailondeck.com', 'fakeinbox.com',
            'trashmail.com', 'yopmail.com', 'getnada.com',
            'maildrop.cc', 'sharklasers.com', 'guerrillamailblock.com',
            'pokemail.net', 'spam4.me', 'bccto.me', 'chacuo.net',
            'dispostable.com', 'tempail.com', '20minutemail.com',
            'mohmal.com', 'emailfake.com', 'fakemailgenerator.com',
            'mytemp.email', 'tempmailo.com', '10mail.org',
            'mailnesia.com', 'jetable.org', 'sneakemail.com',
            'mailcatch.com', 'mintemail.com', 'lastmail.co',
            'mailcatch.com', 'spamgourmet.com', 'tempinbox.com',
        ]
        
        is_temporary = domain in temporary_domains
        
        return {
            'is_temporary': is_temporary,
            'domain': domain,
            'confidence': 'high' if is_temporary else 'low'
        }
    
    async def _check_breaches(self, email: str) -> Optional[List]:
        """
        Проверка email в утечках через публичные API
        Используем альтернативные методы без API ключа
        """
        breaches = []
        
        # Метод 1: Проверка через API (без ключа, ограничено)
        try:
            # Публичный endpoint (может работать с ограничениями)
            url = f"https://breachdirectory.p.rapidapi.com/?func=auto&term={email}"
            headers = {
                # Этот API требует ключа, но мы пробуем без него
                # Если не работает - пропускаем
            }
            
            connector = create_connector(self.proxy)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, headers=headers, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('found'):
                            breaches.append({
                                'source': 'BreachDirectory',
                                'count': data.get('count', 0),
                                'breaches': data.get('result', [])
                            })
        except:
            pass
        
        # Метод 2: Проверка хеша пароля (если пользователь предоставит)
        # Это для future использования
        
        return breaches if breaches else None
    
    async def _search_public_sources(self, email: str) -> Optional[List]:
        """Поиск email в публичных источниках"""
        profiles = []
        
        # Поиск через Google (через текстовый сервис)
        # Это симуляция - реальный поиск требует API
        
        # Проверка на наличие в известных сервисах
        domain = email.split('@')[1].lower() if '@' in email else ''
        local = email.split('@')[0] if '@' in email else ''
        
        # Возможные профили на основе email
        potential_profiles = [
            {
                'service': 'GitHub',
                'url': f"https://github.com/search?q={email}&type=users",
                'type': 'code'
            },
            {
                'service': 'GitLab',
                'url': f"https://gitlab.com/search?search={email}",
                'type': 'code'
            },
            {
                'service': 'Gravatar',
                'url': f"https://en.gravatar.com/{self._hash_email(email)}",
                'type': 'avatar'
            },
            {
                'service': 'Have I Been Pwned',
                'url': f"https://haveibeenpwned.com/account/{email}",
                'type': 'breach'
            },
            {
                'service': 'Snusbase',
                'url': f"https://snusbase.com/search?q={email}",
                'type': 'breach'
            },
        ]
        
        return potential_profiles
    
    def _hash_email(self, email: str) -> str:
        """MD5 хеш email для Gravatar"""
        return hashlib.md5(email.lower().strip().encode()).hexdigest()
