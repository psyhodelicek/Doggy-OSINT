"""
Модуль для хранения результатов поиска
"""
from datetime import datetime
from typing import Any, Dict, List, Optional


class SearchResult:
    """Класс для хранения результатов поиска"""
    
    def __init__(
        self,
        query: str,
        mode: str,
        found: Optional[List[Dict]] = None,
        total_checked: int = 0
    ):
        self.query = query
        self.mode = mode
        self.found = found if found else []
        self.total_checked = total_checked
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    @property
    def found_count(self) -> int:
        """Количество найденных результатов"""
        return len(self.found)
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return {
            "query": self.query,
            "mode": self.mode,
            "timestamp": self.timestamp,
            "found_count": self.found_count,
            "total_checked": self.total_checked,
            "found": self.found
        }
    
    def format_text(self) -> str:
        """Текстовое представление результатов"""
        lines = [
            f"Результаты поиска для: {self.query}",
            f"Режим: {self.mode}",
            f"Дата: {self.timestamp}",
            f"Найдено: {self.found_count} из {self.total_checked}",
            ""
        ]
        
        if self.found:
            lines.append("Найденные результаты:")
            for item in self.found:
                if isinstance(item, dict):
                    for key, value in item.items():
                        lines.append(f"  {key}: {value}")
                else:
                    lines.append(f"  {item}")
                lines.append("")
        
        return "\n".join(lines)
