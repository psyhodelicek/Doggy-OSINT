"""
⚠️ ПРАВОВАЯ ИНФОРМАЦИЯ ⚠️
Инструмент для работы с ОТКРЫТЫМИ ИСТОЧНИКАМИ (OSINT)
"""

from typing import Optional
import aiohttp


def create_connector(proxy: Optional[str] = None) -> Optional[aiohttp.BaseConnector]:
    """
    Создание коннектора для aiohttp с поддержкой прокси
    
    Args:
        proxy: Строка прокси в формате socks5://user:pass@host:port или http://host:port
    
    Returns:
        Коннектор или None
    """
    if not proxy:
        return None
    
    try:
        # Проверка на SOCKS прокси
        if proxy.startswith('socks5://') or proxy.startswith('socks4://'):
            from aiohttp_socks import ProxyConnector
            return ProxyConnector.from_url(proxy, ssl=False)
        # HTTP/HTTPS прокси
        elif proxy.startswith('http://') or proxy.startswith('https://'):
            return aiohttp.TCPConnector(ssl=False)
        else:
            # Пытаемся определить автоматически
            if 'socks' in proxy:
                from aiohttp_socks import ProxyConnector
                return ProxyConnector.from_url(proxy, ssl=False)
            else:
                return aiohttp.TCPConnector(ssl=False)
    except ImportError:
        # Если aiohttp_socks не установлен, возвращаем обычный коннектор
        return aiohttp.TCPConnector(ssl=False)
    except Exception:
        return aiohttp.TCPConnector(ssl=False)


class ProxyManager:
    """Менеджер прокси для ротации и проверки"""
    
    def __init__(self, proxy: str = None, proxy_file: str = None):
        self.proxy = proxy
        self.proxy_list = []
        self.current_index = 0
        
        if proxy_file:
            self._load_proxy_file(proxy_file)
        elif proxy:
            self.proxy_list = [proxy]
    
    def _load_proxy_file(self, filename: str):
        """Загрузка списка прокси из файла"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.proxy_list.append(line)
        except Exception as e:
            print(f"Ошибка загрузки прокси: {e}")
    
    def get_proxy(self) -> Optional[str]:
        """Получение случайного прокси из списка"""
        if self.proxy:
            return self.proxy
        if self.proxy_list:
            import random
            return random.choice(self.proxy_list)
        return None
    
    async def test_proxy(self, proxy: str) -> bool:
        """Тестирование работоспособности прокси"""
        try:
            connector = create_connector(proxy)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get('http://httpbin.org/ip', timeout=10) as resp:
                    return resp.status == 200
        except:
            return False
    
    def get_next_proxy(self) -> Optional[str]:
        """Получение следующего прокси (ротация)"""
        if not self.proxy_list:
            return self.proxy
        
        if self.current_index >= len(self.proxy_list):
            self.current_index = 0
        
        proxy = self.proxy_list[self.current_index]
        self.current_index += 1
        return proxy
