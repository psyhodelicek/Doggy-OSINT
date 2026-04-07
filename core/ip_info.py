"""
⚠️ ПРАВОВАЯ ИНФОРМАЦИЯ ⚠️
Инструмент для работы с ОТКРЫТЫМИ ИСТОЧНИКАМИ (OSINT)
"""

import aiohttp
import asyncio
import ipaddress
from typing import Dict, Any, Optional
from rich.console import Console

from .search_result import SearchResult
from utils.proxy_manager import create_connector


class IPInfo:
    """Получение информации по IP-адресу"""
    
    def __init__(self, proxy: str = None, timeout: int = 15):
        self.proxy = proxy
        self.timeout = timeout
        self.console = Console()
    
    async def search(self, ip: str) -> SearchResult:
        """
        Поиск информации по IP-адресу
        
        Использует:
        - ip-api.com (бесплатный, 45 запросов/мин)
        - ipinfo.io (альтернативный)
        - Определение типа IP
        """
        
        results = {}
        
        # 1. Валидация IP
        validation = self._validate_ip(ip)
        if not validation.get('valid'):
            return SearchResult(
                query=ip,
                mode='ip',
                found={'error': 'Неверный формат IP-адреса'},
                total_checked=1
            )
        results['validation'] = validation
        
        # 2. Основная информация через ip-api.com
        ip_api_data = await self._check_ip_api(ip)
        if ip_api_data:
            results['ip_api'] = ip_api_data
        
        # 3. Дополнительная информация (ipinfo.io)
        ipinfo_data = await self._check_ipinfo(ip)
        if ipinfo_data:
            results['ipinfo'] = ipinfo_data
        
        # 4. Определение типа IP
        ip_type = self._get_ip_type(ip)
        results['ip_type'] = ip_type
        
        # 5. Обратный DNS (если доступен)
        reverse_dns = await self._get_reverse_dns(ip)
        if reverse_dns:
            results['reverse_dns'] = reverse_dns
        
        return SearchResult(
            query=ip,
            mode='ip',
            found=results,
            total_checked=5
        )
    
    def _validate_ip(self, ip: str) -> Dict:
        """Проверка валидности IP-адреса"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            return {
                'valid': True,
                'version': f"IPv{ip_obj.version}",
                'is_private': ip_obj.is_private,
                'is_loopback': ip_obj.is_loopback,
                'is_multicast': ip_obj.is_multicast,
                'is_unspecified': ip_obj.is_unspecified,
                'is_reserved': ip_obj.is_reserved,
                'is_link_local': ip_obj.is_link_local,
                'compressed': ip_obj.compressed
            }
        except ValueError:
            return {'valid': False, 'reason': 'Неверный формат IP'}
    
    async def _check_ip_api(self, ip: str) -> Optional[Dict]:
        """Запрос к ip-api.com (бесплатный API без ключа)"""
        url = f"http://ip-api.com/json/{ip}?fields=status,message,continent,continentCode,country,countryCode,region,regionName,city,district,zip,lat,lon,timezone,currency,isp,org,as,asname,reverse,mobile,proxy,hosting,query"
        
        try:
            connector = create_connector(self.proxy)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == 'success':
                            return {
                                'ip': data.get('query'),
                                'continent': data.get('continent'),
                                'country': data.get('country'),
                                'country_code': data.get('countryCode'),
                                'region': data.get('regionName'),
                                'city': data.get('city'),
                                'district': data.get('district'),
                                'zip': data.get('zip'),
                                'latitude': data.get('lat'),
                                'longitude': data.get('lon'),
                                'timezone': data.get('timezone'),
                                'currency': data.get('currency'),
                                'isp': data.get('isp'),
                                'org': data.get('org'),
                                'as': data.get('as'),
                                'asname': data.get('asname'),
                                'reverse_dns': data.get('reverse'),
                                'mobile': data.get('mobile', False),
                                'proxy': data.get('proxy', False),
                                'hosting': data.get('hosting', False)
                            }
        except asyncio.TimeoutError:
            self.console.print("[dim]Таймаут при запросе к ip-api[/dim]")
        except Exception as e:
            self.console.print(f"[dim]Ошибка ip-api: {e}[/dim]")
        
        return None
    
    async def _check_ipinfo(self, ip: str) -> Optional[Dict]:
        """Запрос к ipinfo.io (бесплатный лимит)"""
        url = f"https://ipinfo.io/{ip}/json"
        
        try:
            connector = create_connector(self.proxy)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'ip': data.get('ip'),
                            'city': data.get('city'),
                            'region': data.get('region'),
                            'country': data.get('country'),
                            'postal': data.get('postal'),
                            'org': data.get('org'),
                            'timezone': data.get('timezone'),
                            'asn': data.get('asn'),
                            'company': data.get('company', {}).get('name') if data.get('company') else None
                        }
        except:
            pass
        
        return None
    
    def _get_ip_type(self, ip: str) -> Dict:
        """Определение типа IP-адреса"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            
            # Определение типа
            if ip_obj.is_private:
                ip_type = "Частный (Private)"
                description = "IP используется во внутренней сети"
            elif ip_obj.is_loopback:
                ip_type = "Loopback"
                description = "Локальный хост (127.0.0.1)"
            elif ip_obj.is_link_local:
                ip_type = "Link-local"
                description = "Локальный адрес канала"
            elif ip_obj.is_multicast:
                ip_type = "Multicast"
                description = "Групповая рассылка"
            elif ip_obj.is_global:
                ip_type = "Публичный (Global)"
                description = "Глобальный IP-адрес"
            else:
                ip_type = "Неизвестный тип"
                description = ""
            
            # Версия IP
            version = "IPv4" if ip_obj.version == 4 else "IPv6"
            
            return {
                'type': ip_type,
                'description': description,
                'version': version,
                'is_global': ip_obj.is_global,
                'is_private': ip_obj.is_private
            }
        except:
            return {'type': 'Unknown', 'description': 'Ошибка определения типа'}
    
    async def _get_reverse_dns(self, ip: str) -> Optional[str]:
        """Обратный DNS запрос"""
        try:
            loop = asyncio.get_event_loop()
            hostname = await loop.run_in_executor(
                None, 
                lambda: asyncio.get_event_loop().run_until_complete(
                    self._resolve_reverse(ip)
                )
            )
            return hostname
        except:
            return None
    
    async def _resolve_reverse(self, ip: str) -> str:
        """Асинхронный reverse DNS"""
        import socket
        try:
            return socket.gethostbyaddr(ip)[0]
        except:
            return None
