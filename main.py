#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import os
import argparse

if sys.platform == 'win32':
    os.system('chcp 65001 >nul')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from pathlib import Path
from colorama import init, Fore
from pystyle import Colors, Colorate
from rich.console import Console
from rich.table import Table, box
from rich.panel import Panel

init()

sys.path.insert(0, str(Path(__file__).parent))

from core.username_search import UsernameSearcher
from core.email_search import EmailSearcher
from core.phone_search import PhoneSearcher
from core.ip_info import IPInfo
from core.domain_info import DomainInfo
from core.metadata_extract import MetadataExtractor
from utils.exporters import Exporter

console = Console()

BANNER = r"""
   _='`'=_
  //(@_@)\\
  |||(Y)|||    DoggyOSINT
  \\\\ ////      by
   / )`( \   @moralfuck_project
<\(  )'(  )
 (__w)_(w__)
"""

def print_banner():
    print(Fore.YELLOW + BANNER + Fore.RESET)

def print_legal():
    legal = """
!!! ПРАВОВОЕ ПРЕДУПРЕЖДЕНИЕ !!!
Инструмент для работы с ОТКРЫТЫМИ ИСТОЧНИКАМИ.
Используйте ТОЛЬКО в законных целях!
Разработчик: @moralfuck_project
"""
    print(Fore.YELLOW + legal + Fore.RESET)


async def search_username(username, depth="standard", threads=20, timeout=15, proxy=None, export=None):
    from core.sites_db import SITES
    site_count = len(SITES)
    
    print(Fore.GREEN + f"\n[*] Запуск поиска по нику '{username}'..." + Fore.RESET)
    print(Fore.YELLOW + f"[*] Глубина: {depth} | Сайтов: {site_count}+" + Fore.RESET)
    
    searcher = UsernameSearcher(proxy, threads, timeout)
    results = await searcher.search(username, depth=depth)
    
    if results and results.found:
        console.print()
        console.print(Panel(
            f"[bold green]Результаты поиска[/bold green]\n\n"
            f"[cyan]Запрос:[/cyan] {results.query}\n"
            f"[cyan]Режим:[/cyan] {results.mode}\n"
            f"[cyan]Найдено:[/cyan] [green]{results.found_count}[/green] из [yellow]{results.total_checked}[/yellow]",
            title="Сводка",
            border_style="green"
        ))
        console.print()

        table = Table(title="Найденные профили", show_header=True, header_style="bold cyan", box=box.DOUBLE_EDGE)
        table.add_column("Сайт", style="yellow")
        table.add_column("Категория", style="green")
        table.add_column("URL", style="blue")
        table.add_column("Статус", style="magenta")

        for item in results.found:
            table.add_row(
                item.get("name", "N/A"),
                item.get("category", "other"),
                item.get("uri", "N/A")[:50] + "..." if len(item.get("uri", "")) > 50 else item.get("uri", "N/A"),
                item.get("status", "unknown")
            )
        console.print(table)
        
        if export:
            exporter = Exporter(f"username_{username}")
            exporter.export(results, export)
            console.print(f"\n[green]Результаты экспортированы[/green]")
    else:
        console.print(Fore.YELLOW + "\nНичего не найдено" + Fore.RESET)


async def search_email(email, check_breaches=False, timeout=15, proxy=None, export=None):
    print(Fore.GREEN + f"\n[*] Запуск поиска по email '{email}'..." + Fore.RESET)
    
    searcher = EmailSearcher(proxy, timeout)
    results = await searcher.search(email, check_breaches)
    
    if results and results.found:
        console.print()
        console.print(Panel(
            f"[bold green]Результаты поиска[/bold green]\n\n"
            f"[cyan]Запрос:[/cyan] {results.query}\n"
            f"[cyan]Режим:[/cyan] {results.mode}\n"
            f"[cyan]Найдено:[/cyan] [green]{results.found_count}[/green]",
            title="Сводка",
            border_style="green"
        ))
        
        for key, value in results.found.items():
            if isinstance(value, dict):
                console.print(f"\n[yellow]{key}:[/yellow]")
                for k, v in value.items():
                    console.print(f"  [cyan]{k}:[/cyan] {v}")
            else:
                console.print(f"\n[yellow]{key}:[/yellow] {value}")
        
        if export:
            exporter = Exporter(f"email_{email.replace('@', '_at_')}")
            exporter.export(results, export)
            console.print(f"\n[green]Результаты экспортированы[/green]")
    else:
        console.print(Fore.YELLOW + "\nНичего не найдено" + Fore.RESET)


async def search_phone(phone, timeout=15, proxy=None, export=None):
    print(Fore.GREEN + f"\n[*] Запуск поиска по номеру '{phone}'..." + Fore.RESET)
    
    searcher = PhoneSearcher(proxy, timeout)
    results = await searcher.search(phone)
    
    if results and results.found:
        console.print()
        console.print(Panel(
            f"[bold green]Результаты поиска[/bold green]\n\n"
            f"[cyan]Запрос:[/cyan] {results.query}\n"
            f"[cyan]Режим:[/cyan] {results.mode}",
            title="Сводка",
            border_style="green"
        ))
        
        for key, value in results.found.items():
            if isinstance(value, dict):
                console.print(f"\n[yellow]{key}:[/yellow]")
                for k, v in value.items():
                    console.print(f"  [cyan]{k}:[/cyan] {v}")
            else:
                console.print(f"\n[yellow]{key}:[/yellow] {value}")
        
        if export:
            exporter = Exporter(f"phone_{phone.replace('+', '')}")
            exporter.export(results, export)
            console.print(f"\n[green]Результаты экспортированы[/green]")
    else:
        console.print(Fore.YELLOW + "\nНичего не найдено" + Fore.RESET)


async def search_ip(ip, timeout=15, proxy=None, export=None):
    print(Fore.GREEN + f"\n[*] Запуск поиска по IP '{ip}'..." + Fore.RESET)
    
    searcher = IPInfo(proxy, timeout)
    results = await searcher.search(ip)
    
    if results and results.found:
        console.print()
        console.print(Panel(
            f"[bold green]Результаты поиска[/bold green]\n\n"
            f"[cyan]Запрос:[/cyan] {results.query}\n"
            f"[cyan]Режим:[/cyan] {results.mode}",
            title="Сводка",
            border_style="green"
        ))
        
        for key, value in results.found.items():
            if isinstance(value, dict):
                console.print(f"\n[yellow]{key}:[/yellow]")
                for k, v in value.items():
                    console.print(f"  [cyan]{k}:[/cyan] {v}")
            else:
                console.print(f"\n[yellow]{key}:[/yellow] {value}")
        
        if export:
            exporter = Exporter(f"ip_{ip}")
            exporter.export(results, export)
            console.print(f"\n[green]Результаты экспортированы[/green]")
    else:
        console.print(Fore.YELLOW + "\nНичего не найдено" + Fore.RESET)


async def search_domain(domain, whois=True, dns=True, ssl=True, timeout=15, export=None):
    print(Fore.GREEN + f"\n[*] Запуск поиска по домену '{domain}'..." + Fore.RESET)
    
    searcher = DomainInfo(timeout)
    results = await searcher.search(domain, whois, dns, ssl)
    
    if results and results.found:
        console.print()
        console.print(Panel(
            f"[bold green]Результаты поиска[/bold green]\n\n"
            f"[cyan]Запрос:[/cyan] {results.query}\n"
            f"[cyan]Режим:[/cyan] {results.mode}",
            title="Сводка",
            border_style="green"
        ))
        
        for key, value in results.found.items():
            if isinstance(value, dict):
                console.print(f"\n[yellow]{key}:[/yellow]")
                for k, v in value.items():
                    console.print(f"  [cyan]{k}:[/cyan] {str(v)[:100]}")
            elif isinstance(value, list):
                console.print(f"\n[yellow]{key}:[/yellow]")
                for item in value[:10]:
                    console.print(f"  [cyan]-[/cyan] {str(item)[:100]}")
            else:
                console.print(f"\n[yellow]{key}:[/yellow] {str(value)[:100]}")
        
        if export:
            exporter = Exporter(f"domain_{domain.replace('.', '_')}")
            exporter.export(results, export)
            console.print(f"\n[green]Результаты экспортированы[/green]")
    else:
        console.print(Fore.YELLOW + "\nНичего не найдено" + Fore.RESET)


def search_metadata(filepath, export=None):
    print(Fore.GREEN + f"\n[*] Извлечение метаданных из '{filepath}'..." + Fore.RESET)
    
    extractor = MetadataExtractor()
    results = extractor.extract(filepath)
    
    if results and results.found:
        console.print()
        console.print(Panel(
            f"[bold green]Результаты поиска[/bold green]\n\n"
            f"[cyan]Запрос:[/cyan] {results.query}\n"
            f"[cyan]Режим:[/cyan] {results.mode}",
            title="Сводка",
            border_style="green"
        ))
        
        for key, value in results.found.items():
            if isinstance(value, dict):
                console.print(f"\n[yellow]{key}:[/yellow]")
                for k, v in value.items():
                    console.print(f"  [cyan]{k}:[/cyan] {v}")
            else:
                console.print(f"\n[yellow]{key}:[/yellow] {value}")
        
        if export:
            exporter = Exporter(f"metadata_{Path(filepath).stem}")
            exporter.export(results, export)
            console.print(f"\n[green]Результаты экспортированы[/green]")
    else:
        console.print(Fore.YELLOW + "\nМетаданные не найдены" + Fore.RESET)


def main():
    parser = argparse.ArgumentParser(
        description="DoggyOSINT - универсальный поиск в открытых источниках",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{Fore.YELLOW}Примеры использования:{Fore.RESET}
  python main.py -n durov                    Поиск по нику
  python main.py -n durov -d deep            Поиск по нику (полная глубина)
  python main.py -e test@example.com         Поиск по email
  python main.py -p +79991234567             Поиск по телефону
  python main.py -i 8.8.8.8                  Поиск по IP
  python main.py -d google.com               Поиск по домену
  python main.py -m image.jpg                Метаданные изображения
  python main.py -n durov --export html      Экспорт в HTML
        """
    )
    
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("-n", "--username", help="Поиск по нику")
    mode_group.add_argument("-e", "--email", help="Поиск по email")
    mode_group.add_argument("-p", "--phone", help="Поиск по номеру телефона")
    mode_group.add_argument("-i", "--ip", help="Поиск по IP-адресу")
    mode_group.add_argument("-d", "--domain", help="Поиск по домену")
    mode_group.add_argument("-m", "--metadata", help="Метаданные изображения")
    
    parser.add_argument("--depth", choices=["quick", "standard", "deep"], default="standard", help="Глубина поиска по нику")
    parser.add_argument("--threads", "-t", type=int, default=20, help="Количество потоков")
    parser.add_argument("--timeout", type=int, default=15, help="Таймаут запросов (сек)")
    
    parser.add_argument("--no-whois", action="store_true", help="Не получать WHOIS")
    parser.add_argument("--no-dns", action="store_true", help="Не получать DNS")
    parser.add_argument("--no-ssl", action="store_true", help="Не получать SSL")
    
    parser.add_argument("--check-breaches", action="store_true", help="Проверить утечки")
    
    parser.add_argument("--export", choices=["html", "json", "csv", "all"], help="Экспорт результатов")
    parser.add_argument("--proxy", help="Прокси (socks5://user:pass@host:port)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Подробный вывод")
    
    args = parser.parse_args()
    
    print_banner()
    print_legal()
    
    if args.username:
        asyncio.run(search_username(
            args.username,
            depth=args.depth,
            threads=args.threads,
            timeout=args.timeout,
            proxy=args.proxy,
            export=args.export
        ))
    elif args.email:
        asyncio.run(search_email(
            args.email,
            check_breaches=args.check_breaches,
            timeout=args.timeout,
            proxy=args.proxy,
            export=args.export
        ))
    elif args.phone:
        asyncio.run(search_phone(
            args.phone,
            timeout=args.timeout,
            proxy=args.proxy,
            export=args.export
        ))
    elif args.ip:
        asyncio.run(search_ip(
            args.ip,
            timeout=args.timeout,
            proxy=args.proxy,
            export=args.export
        ))
    elif args.domain:
        asyncio.run(search_domain(
            args.domain,
            whois=not args.no_whois,
            dns=not args.no_dns,
            ssl=not args.no_ssl,
            timeout=args.timeout,
            export=args.export
        ))
    elif args.metadata:
        search_metadata(args.metadata, export=args.export)


if __name__ == "__main__":
    main()
