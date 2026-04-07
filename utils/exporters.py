"""
⚠️ ПРАВОВАЯ ИНФОРМАЦИЯ ⚠️
Инструмент для работы с ОТКРЫТЫМИ ИСТОЧНИКАМИ (OSINT)
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from rich.console import Console

console = Console()


class Exporter:
    """Экспорт результатов в различные форматы"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.reports_dir = Path(__file__).parent.parent / "reports"
        self.reports_dir.mkdir(exist_ok=True)
    
    def export(self, results: Any, formats: str):
        """
        Экспорт результатов в указанные форматы
        
        Args:
            results: Объект SearchResult
            formats: строка с форматами через запятую или 'all'
        """
        format_list = ['json', 'csv', 'html'] if formats == 'all' else formats.split(',')
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_path = self.reports_dir / f"{self.filename}_{timestamp}"
        
        exported = []
        
        if 'json' in format_list:
            if self._export_json(results, f"{base_path}.json"):
                exported.append('JSON')
        
        if 'csv' in format_list:
            if self._export_csv(results, f"{base_path}.csv"):
                exported.append('CSV')
        
        if 'html' in format_list:
            if self._export_html(results, f"{base_path}.html"):
                exported.append('HTML')
        
        if exported:
            console.print(f"\n[green]✓ Экспортировано: {', '.join(exported)}[/green]")
            console.print(f"[dim]Папка: {self.reports_dir}[/dim]")
    
    def _export_json(self, results: Any, filepath: str) -> bool:
        """Экспорт в JSON"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results.to_dict(), f, ensure_ascii=False, indent=2)
            console.print(f"[green]JSON сохранён: {filepath.name}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Ошибка экспорта JSON: {e}[/red]")
            return False
    
    def _export_csv(self, results: Any, filepath: str) -> bool:
        """Экспорт в CSV"""
        try:
            data = results.to_dict()
            
            # Плоская структура для CSV
            flat_data = []
            
            if results.mode == 'username':
                for item in data.get('found', []):
                    flat_data.append({
                        'site': item.get('name', ''),
                        'category': item.get('category', ''),
                        'url': item.get('uri', ''),
                        'status': item.get('status', ''),
                        'status_code': item.get('status_code', '')
                    })
            
            elif results.mode == 'phone':
                for key, value in data.get('found', {}).items():
                    if isinstance(value, dict):
                        for k, v in value.items():
                            flat_data.append({'source': key, 'field': k, 'value': str(v)})
                    else:
                        flat_data.append({'source': key, 'field': '', 'value': str(value)})
            
            elif results.mode == 'email':
                for key, value in data.get('found', {}).items():
                    if isinstance(value, dict):
                        for k, v in value.items():
                            flat_data.append({'source': key, 'field': k, 'value': str(v)})
                    else:
                        flat_data.append({'source': key, 'field': '', 'value': str(value)})
            
            elif results.mode == 'ip':
                for key, value in data.get('found', {}).items():
                    if isinstance(value, dict):
                        for k, v in value.items():
                            flat_data.append({'source': key, 'field': k, 'value': str(v)})
                    else:
                        flat_data.append({'source': key, 'field': '', 'value': str(value)})
            
            elif results.mode == 'domain':
                for key, value in data.get('found', {}).items():
                    if isinstance(value, dict):
                        for k, v in value.items():
                            flat_data.append({'source': key, 'field': k, 'value': str(v)[:200]})
                    elif isinstance(value, list):
                        for item in value[:20]:
                            flat_data.append({'source': key, 'field': '', 'value': str(item)[:200]})
                    else:
                        flat_data.append({'source': key, 'field': '', 'value': str(value)[:200]})
            
            elif results.mode == 'metadata':
                for key, value in data.get('found', {}).items():
                    if isinstance(value, dict):
                        for k, v in value.items():
                            flat_data.append({'source': key, 'field': k, 'value': str(v)[:200]})
                    else:
                        flat_data.append({'source': key, 'field': '', 'value': str(value)[:200]})
            
            if flat_data:
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=flat_data[0].keys())
                    writer.writeheader()
                    writer.writerows(flat_data)
                console.print(f"[green]CSV сохранён: {filepath.name}[/green]")
                return True
            
            return False
            
        except Exception as e:
            console.print(f"[red]Ошибка экспорта CSV: {e}[/red]")
            return False
    
    def _export_html(self, results: Any, filepath: str) -> bool:
        """Экспорт в HTML с красивым оформлением"""
        try:
            html_content = self._generate_html(results)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            console.print(f"[green]HTML сохранён: {filepath.name}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]Ошибка экспорта HTML: {e}[/red]")
            return False
    
    def _generate_html(self, results: Any) -> str:
        """Генерация HTML отчёта"""
        data = results.to_dict()
        
        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DoggyOSINT Report - {results.query}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 20px;
            color: #fff;
        }}
        .container {{ 
            max-width: 1200px; 
            margin: auto; 
            background: rgba(255, 255, 255, 0.95); 
            padding: 30px; 
            border-radius: 15px; 
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            color: #333;
        }}
        h1 {{ 
            color: #1a1a2e; 
            border-bottom: 3px solid #00d9ff; 
            padding-bottom: 15px;
            margin-bottom: 20px;
            font-size: 2em;
        }}
        .banner {{
            background: linear-gradient(135deg, #00d9ff 0%, #0099cc 100%);
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            font-family: monospace;
            white-space: pre;
            font-size: 10px;
            line-height: 1.2;
        }}
        .summary {{ 
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
            padding: 20px; 
            border-radius: 10px; 
            margin: 20px 0;
            border-left: 4px solid #00d9ff;
        }}
        .summary p {{ margin: 8px 0; }}
        .summary strong {{ color: #1a1a2e; }}
        .found {{ color: #28a745; font-weight: bold; }}
        .not-found {{ color: #dc3545; }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin: 20px 0;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        th {{ 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
            color: white; 
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        td {{ 
            padding: 12px 15px; 
            border-bottom: 1px solid #dee2e6; 
        }}
        tr:hover {{ 
            background: #f8f9fa; 
        }}
        tr:last-child td {{ border-bottom: none; }}
        .footer {{ 
            margin-top: 30px; 
            text-align: center; 
            color: #6c757d; 
            font-size: 0.9em;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
        }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        .badge-found {{ background: #28a745; color: white; }}
        .badge-potential {{ background: #ffc107; color: #333; }}
        .badge-other {{ background: #6c757d; color: white; }}
        a {{ color: #007bff; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .section {{ margin: 25px 0; }}
        .section-title {{
            color: #1a1a2e;
            font-size: 1.3em;
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 2px solid #00d9ff;
        }}
        .info-card {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }}
        .info-card h4 {{ color: #1a1a2e; margin-bottom: 10px; }}
        .info-card p {{ margin: 5px 0; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="banner">
    _='`'=_
  //( @_@)\\
  |||(Y)|||    DoggyOSINT
  \\\\ ////      by
   / )`( \\   @moralfuck_project
<\(  )'(  )
 (__w)_(w__)
        </div>
        
        <h1>🔍 OSINT Report</h1>
        
        <div class="summary">
            <p><strong>📝 Запрос:</strong> <code>{results.query}</code></p>
            <p><strong>📂 Тип:</strong> {results.mode}</p>
            <p><strong>📅 Дата:</strong> {results.timestamp}</p>
            <p><strong>✅ Найдено:</strong> <span class="found">{results.found_count}</span> из <strong>{results.total_checked}</strong></p>
        </div>
        
        {self._generate_content(data)}
        
        <div class="footer">
            <p>⚠️ Инструмент для работы с ОТКРЫТЫМИ ИСТОЧНИКАМИ (OSINT)</p>
            <p>Используйте ТОЛЬКО в законных целях</p>
            <p style="margin-top: 10px;">
                <strong>DoggyOSINT</strong> by @moralfuck_project | 
                Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def _generate_content(self, data: Dict) -> str:
        """Генерация контента отчёта"""
        content = []
        mode = data.get('mode', '')
        found = data.get('found', {})
        
        if mode == 'username' and isinstance(found, list) and found:
            content.append('<div class="section">')
            content.append('<h2 class="section-title">📍 Найденные профили</h2>')
            content.append('<table><thead><tr><th>Сайт</th><th>Категория</th><th>URL</th><th>Статус</th></tr></thead><tbody>')
            
            for item in found:
                name = item.get('name', 'N/A')
                category = item.get('category', 'other')
                uri = item.get('uri', '#')
                status = item.get('status', 'unknown')
                
                badge_class = f'badge-{status}' if status in ['found', 'potential'] else 'badge-other'
                
                content.append(f'<tr>')
                content.append(f'<td><strong>{name}</strong></td>')
                content.append(f'<td><span class="badge badge-{category}">{category}</span></td>')
                content.append(f'<td><a href="{uri}" target="_blank">{uri[:60]}...</a></td>')
                content.append(f'<td><span class="badge {badge_class}">{status}</span></td>')
                content.append(f'</tr>')
            
            content.append('</tbody></table></div>')
        
        elif mode in ['phone', 'email', 'ip', 'metadata'] and isinstance(found, dict):
            for source, info in found.items():
                content.append('<div class="section">')
                content.append(f'<h2 class="section-title">📋 {source.replace("_", " ").title()}</h2>')
                
                if isinstance(info, dict):
                    content.append('<div class="info-card">')
                    for key, value in info.items():
                        content.append(f'<p><strong>{key.replace("_", " ").title()}:</strong> {value}</p>')
                    content.append('</div>')
                else:
                    content.append(f'<p>{info}</p>')
                
                content.append('</div>')
        
        elif mode == 'domain' and isinstance(found, dict):
            for source, info in found.items():
                content.append('<div class="section">')
                content.append(f'<h2 class="section-title">📋 {source.replace("_", " ").title()}</h2>')
                
                if isinstance(info, dict):
                    content.append('<div class="info-card">')
                    for key, value in info.items():
                        if isinstance(value, list):
                            value = ', '.join(str(v) for v in value[:10])
                        content.append(f'<p><strong>{key.replace("_", " ").title()}:</strong> {str(value)[:150]}</p>')
                    content.append('</div>')
                else:
                    content.append(f'<p>{info}</p>')
                
                content.append('</div>')
        
        return '\n'.join(content)
