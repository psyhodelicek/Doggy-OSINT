"""
⚠️ ПРАВОВАЯ ИНФОРМАЦИЯ ⚠️
Инструмент для работы с ОТКРЫТЫМИ ИСТОЧНИКАМИ (OSINT)
"""

import asyncio
import socket
import ssl
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from rich.console import Console

from .search_result import SearchResult


class DomainInfo:
    """Получение информации о домене"""
    
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.console = Console()
    
    async def search(
        self, 
        domain: str, 
        check_whois: bool = True,
        check_dns: bool = True,
        check_ssl: bool = True
    ) -> SearchResult:
        """
        Поиск информации по домену
        
        Использует:
        - WHOIS информация
        - DNS записи
        - SSL сертификат
        """
        
        results = {}
        
        # 1. Валидация домена
        validation = self._validate_domain(domain)
        if not validation.get('valid'):
            return SearchResult(
                query=domain,
                mode='domain',
                found={'error': 'Неверный формат домена'},
                total_checked=1
            )
        results['validation'] = validation
        
        # 2. WHOIS информация
        if check_whois:
            whois_data = await self._get_whois(domain)
            if whois_data:
                results['whois'] = whois_data
        
        # 3. DNS записи
        if check_dns:
            dns_data = await self._get_dns_records(domain)
            if dns_data:
                results['dns'] = dns_data
        
        # 4. SSL сертификат
        if check_ssl:
            ssl_data = await self._get_ssl_info(domain)
            if ssl_data:
                results['ssl'] = ssl_data
        
        # 5. Общая информация
        general_info = self._get_general_info(domain)
        results['general'] = general_info
        
        return SearchResult(
            query=domain,
            mode='domain',
            found=results,
            total_checked=5
        )
    
    def _validate_domain(self, domain: str) -> Dict:
        """Проверка валидности домена"""
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$'
        is_valid = bool(re.match(pattern, domain))
        
        if is_valid:
            parts = domain.split('.')
            tld = parts[-1] if parts else ''
            
            return {
                'valid': True,
                'domain': domain,
                'tld': tld,
                'subdomain': '.'.join(parts[:-2]) if len(parts) > 2 else '',
                'registered_domain': '.'.join(parts[-2:]) if len(parts) >= 2 else domain,
                'length': len(domain)
            }
        
        return {'valid': False, 'reason': 'Неверный формат домена'}
    
    async def _get_whois(self, domain: str) -> Optional[Dict]:
        """Получение WHOIS информации"""
        try:
            # Попытка использовать библиотеку whois
            try:
                import whois
                loop = asyncio.get_event_loop()
                w_data = await loop.run_in_executor(
                    None,
                    lambda: whois.whois(domain)
                )
                
                return {
                    'domain_name': w_data.domain_name if w_data.domain_name else 'N/A',
                    'registrar': w_data.registrar if w_data.registrar else 'N/A',
                    'creation_date': str(w_data.creation_date) if w_data.creation_date else 'N/A',
                    'expiration_date': str(w_data.expiration_date) if w_data.expiration_date else 'N/A',
                    'updated_date': str(w_data.updated_date) if w_data.updated_date else 'N/A',
                    'name_servers': w_data.name_servers if w_data.name_servers else [],
                    'status': w_data.status if w_data.status else [],
                    'emails': w_data.emails if w_data.emails else [],
                    'dnssec': w_data.dnssec if w_data.dnssec else 'N/A',
                    'org': w_data.org if w_data.org else 'N/A',
                    'country': w_data.country if w_data.country else 'N/A'
                }
            except ImportError:
                # Если библиотека не установлена, используем сокет
                return await self._whois_socket(domain)
                
        except Exception as e:
            self.console.print(f"[dim]Ошибка WHOIS: {e}[/dim]")
        
        return None
    
    async def _whois_socket(self, domain: str) -> Optional[Dict]:
        """WHOIS через сокет (альтернативный метод)"""
        try:
            whois_server = "whois.iana.org"
            
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(whois_server, 43),
                timeout=self.timeout
            )
            
            writer.write(f"{domain}\r\n".encode())
            await writer.drain()
            
            response = await asyncio.wait_for(reader.read(), timeout=self.timeout)
            writer.close()
            await writer.wait_closed()
            
            text = response.decode('utf-8', errors='ignore')
            
            # Парсинг базовой информации
            data = {'raw': text[:2000]}  # Ограничиваем размер
            
            # Извлечение ключевых полей
            for line in text.split('\n'):
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace(' ', '_')
                    value = value.strip()
                    if key not in data:
                        data[key] = value
            
            return data
            
        except Exception as e:
            self.console.print(f"[dim]Ошибка WHOIS сокета: {e}[/dim]")
            return None
    
    async def _get_dns_records(self, domain: str) -> Optional[Dict]:
        """Получение DNS записей"""
        dns_records = {}
        
        record_types = [
            ('A', socket.AF_INET),
            ('AAAA', socket.AF_INET6),
        ]
        
        for record_type, family in record_types:
            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda d=domain, f=family: socket.getaddrinfo(d, None, f, socket.SOCK_STREAM)
                )
                
                ips = list(set([r[4][0] for r in result]))
                dns_records[record_type.lower()] = ips[:10]  # Ограничиваем количество
            except:
                pass
        
        # MX записи через сокет
        try:
            mx_records = await self._get_mx_records(domain)
            if mx_records:
                dns_records['mx'] = mx_records
        except:
            pass
        
        # NS записи
        try:
            ns_records = await self._get_ns_records(domain)
            if ns_records:
                dns_records['ns'] = ns_records
        except:
            pass
        
        return dns_records if dns_records else None
    
    async def _get_mx_records(self, domain: str) -> List[str]:
        """Получение MX записей"""
        # Упрощённый метод - пробуем получить почтовые серверы
        mx_hosts = []
        
        # Популярные почтовые сервисы
        mail_providers = {
            'gmail.com': ['gmail-smtp-in.l.google.com'],
            'yahoo.com': ['mta5.am0.yahoodns.net'],
            'outlook.com': ['outlook-com.olc.protection.outlook.com'],
            'mail.ru': ['mxs.mail.ru'],
            'yandex.ru': ['mx.yandex.ru'],
        }
        
        if domain.lower() in mail_providers:
            return mail_providers[domain.lower()]
        
        # Попытка получить через DNS
        try:
            import dns.resolver
            answers = dns.resolver.resolve(domain, 'MX')
            mx_hosts = [str(r.exchange) for r in answers]
        except ImportError:
            pass
        except:
            pass
        
        return mx_hosts
    
    async def _get_ns_records(self, domain: str) -> List[str]:
        """Получение NS записей"""
        try:
            import dns.resolver
            answers = dns.resolver.resolve(domain, 'NS')
            return [str(r.target) for r in answers]
        except ImportError:
            pass
        except:
            pass
        
        return []
    
    async def _get_ssl_info(self, domain: str) -> Optional[Dict]:
        """Получение информации о SSL сертификате"""
        try:
            loop = asyncio.get_event_loop()
            
            def get_cert():
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                with socket.create_connection((domain, 443), timeout=self.timeout) as sock:
                    with context.wrap_socket(sock, server_hostname=domain) as ssock:
                        cert = ssock.getpeercert()
                        return cert
            
            cert = await loop.run_in_executor(None, get_cert)
            
            if cert:
                # Обработка дат
                not_before = cert.get('notBefore', '')
                not_after = cert.get('notAfter', '')
                
                # Парсинг дат
                try:
                    from datetime import datetime
                    not_before_date = datetime.strptime(not_before, '%b %d %H:%M:%S %Y %Z') if not_before else 'N/A'
                    not_after_date = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z') if not_after else 'N/A'
                except:
                    not_before_date = not_before
                    not_after_date = not_after
                
                # Извлечение информации
                subject = dict(x[0] for x in cert.get('subject', []))
                issuer = dict(x[0] for x in cert.get('issuer', []))
                
                return {
                    'subject': subject.get('commonName', 'N/A'),
                    'issuer': issuer.get('commonName', 'N/A'),
                    'version': cert.get('version', 'N/A'),
                    'serial_number': cert.get('serialNumber', 'N/A'),
                    'not_before': str(not_before_date),
                    'not_after': str(not_after_date),
                    'san': cert.get('subjectAltName', []),
                    'ocsp': cert.get('OCSP', []),
                    'ca_issuers': cert.get('caIssuers', [])
                }
                
        except Exception as e:
            self.console.print(f"[dim]Ошибка SSL: {e}[/dim]")
        
        return None
    
    def _get_general_info(self, domain: str) -> Dict:
        """Общая информация о домене"""
        parts = domain.split('.')
        
        # Определение типа домена
        tld = parts[-1] if parts else ''
        
        tld_types = {
            'com': 'Коммерческий',
            'org': 'Организация',
            'net': 'Сеть',
            'edu': 'Образование',
            'gov': 'Правительство',
            'mil': 'Военный',
            'int': 'Международный',
            'info': 'Информация',
            'biz': 'Бизнес',
            'name': 'Персональный',
            'pro': 'Профессиональный',
            'ru': 'Россия',
            'rf': 'Россия (кириллица)',
            'su': 'СССР',
            'ua': 'Украина',
            'by': 'Беларусь',
            'kz': 'Казахстан',
            'uz': 'Узбекистан',
            'uk': 'Великобритания',
            'de': 'Германия',
            'fr': 'Франция',
            'cn': 'Китай',
            'jp': 'Япония',
            'io': 'Британская территория в Индийском океане (популярен у стартапов)',
            'co': 'Колумбия (популярен как альтернатива .com)',
            'me': 'Черногория (популярен для персональных сайтов)',
            'tv': 'Тувалу (популярен у видео-сервисов)',
            'app': 'Приложения',
            'dev': 'Разработчики',
            'tech': 'Технологии',
            'online': 'Онлайн',
            'site': 'Сайт',
            'store': 'Магазин',
            'shop': 'Магазин',
            'blog': 'Блог',
            'news': 'Новости',
            'xyz': 'Общий',
        }
        
        # Популярные домены второго уровня
        second_level = {
            'co.uk': 'Великобритания коммерческий',
            'ac.uk': 'Великобритания академический',
            'gov.uk': 'Великобритания правительственный',
            'com.ru': 'Россия коммерческий',
            'org.ru': 'Россия организация',
            'net.ru': 'Россия сеть',
            'pp.ru': 'Россия персональный',
            'msk.ru': 'Россия Москва',
            'spb.ru': 'Россия Санкт-Петербург',
        }
        
        registered_domain = '.'.join(parts[-2:]) if len(parts) >= 2 else domain
        domain_type = second_level.get(registered_domain, tld_types.get(tld, 'Неизвестный тип'))
        
        return {
            'full_domain': domain,
            'registered_domain': registered_domain,
            'tld': tld,
            'tld_type': domain_type,
            'subdomain_count': len(parts) - 2 if len(parts) > 2 else 0,
            'domain_length': len(domain),
            'has_www': domain.startswith('www.')
        }
