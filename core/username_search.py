"""
⚠️ ПРАВОВАЯ ИНФОРМАЦИЯ ⚠️
Инструмент для работы с ОТКРЫТЫМИ ИСТОЧНИКАМИ (OSINT)
"""

import aiohttp
import asyncio
import json
from typing import List, Dict, Any, Optional
from urllib.parse import quote
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from .search_result import SearchResult
from utils.proxy_manager import create_connector

# Путь к базе данных
DATA_DIR = Path(__file__).parent.parent / "data"
WMN_DATA_PATH = DATA_DIR / "wmn-data.json"

# Импорт большой базы сайтов
from .sites_db import SITES as DEFAULT_SITES


class UsernameSearcher:
    """Поиск по никнейму на множестве сайтов (500+)"""
    
    def __init__(self, proxy: str = None, max_concurrent: int = 30, timeout: int = 15):
        self.proxy = proxy
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.console = Console()
        self.sites_db = self._load_sites_db()
    
    def _load_sites_db(self) -> List[Dict]:
        """Загружает базу сайтов"""
        sites = DEFAULT_SITES.copy()
        
        # Попытка загрузить расширенную базу
        if WMN_DATA_PATH.exists():
            try:
                with open(WMN_DATA_PATH, 'r', encoding='utf-8') as f:
                    wmn_data = json.load(f)
                    wmn_sites = wmn_data.get('sites', [])
                    # Добавляем только уникальные сайты
                    existing_names = {s['name'] for s in sites}
                    for site in wmn_sites:
                        if site.get('name') not in existing_names:
                            sites.append(site)
                            existing_names.add(site.get('name'))
                self.console.print(f"[green]Загружено {len(sites)} сайтов из базы[/green]")
            except Exception as e:
                self.console.print(f"[dim]Ошибка загрузки базы: {e}[/dim]")
        
        return sites
    
    async def check_site(
        self, 
        session: aiohttp.ClientSession, 
        site: Dict, 
        username: str,
        semaphore: asyncio.Semaphore
    ) -> Optional[Dict]:
        """Проверяет наличие username на одном сайте"""
        async with semaphore:
            uri_check = site.get('uri_check', '').replace('{username}', quote(username))
            
            if not uri_check or uri_check == site.get('uri_check'):
                return None
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            try:
                connector = create_connector(self.proxy)
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get(
                        uri_check,
                        headers=headers,
                        timeout=self.timeout,
                        allow_redirects=True,
                        ssl=False
                    ) as response:
                        text = await response.text()
                        status = response.status
                        
                        # Проверка наличия профиля
                        m_string = site.get('m_string', '')
                        not_found = False
                        
                        if m_string and m_string in text:
                            not_found = True
                        elif status == 404:
                            not_found = True
                        
                        if not not_found:
                            return {
                                'name': site.get('name'),
                                'category': site.get('cat', 'other'),
                                'uri': site.get('uri_pretty', uri_check).replace('{username}', username),
                                'checked_uri': uri_check,
                                'status': 'found',
                                'status_code': status
                            }
                        
            except asyncio.TimeoutError:
                pass
            except Exception:
                pass
            
            return None
    
    async def search(
        self, 
        username: str, 
        specific_sites: List[str] = None,
        exclude_categories: List[str] = None, 
        depth: str = "standard"
    ) -> SearchResult:
        """
        Основной метод поиска по нику
        
        Args:
            username: Никнейм для поиска
            specific_sites: Список конкретных сайтов
            exclude_categories: Категории для исключения
            depth: Глубина поиска (quick, standard, deep)
        
        Returns:
            SearchResult с найденными профилями
        """
        # Фильтрация сайтов
        sites_to_check = self.sites_db.copy()
        
        if specific_sites:
            sites_to_check = [
                s for s in sites_to_check 
                if s.get('name', '').lower() in [ss.lower() for ss in specific_sites]
            ]
        
        if exclude_categories:
            sites_to_check = [
                s for s in sites_to_check 
                if s.get('cat', 'other') not in exclude_categories
            ]
        
        # Ограничение по глубине
        if depth == "quick":
            sites_to_check = sites_to_check[:100]
        elif depth == "standard":
            sites_to_check = sites_to_check[:300]
        # deep - все сайты
        
        self.console.print(f"[cyan]Проверяю {len(sites_to_check)} сайтов для пользователя '{username}'[/cyan]")
        
        semaphore = asyncio.Semaphore(self.max_concurrent)
        results = []
        
        connector = create_connector(self.proxy)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            for site in sites_to_check:
                task = self.check_site(session, site, username, semaphore)
                tasks.append(task)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[cyan]{task.completed}/{task.total}"),
                console=self.console
            ) as progress:
                task = progress.add_task("[cyan]Поиск...", total=len(tasks))
                
                for coro in asyncio.as_completed(tasks):
                    result = await coro
                    if result:
                        results.append(result)
                    progress.update(task, advance=1)
        
        return SearchResult(
            query=username,
            mode='username',
            found=results,
            total_checked=len(sites_to_check)
        )
