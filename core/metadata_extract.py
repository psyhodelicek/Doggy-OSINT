"""
⚠️ ПРАВОВАЯ ИНФОРМАЦИЯ ⚠️
Инструмент для работы с ОТКРЫТЫМИ ИСТОЧНИКАМИ (OSINT)
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from rich.console import Console

from .search_result import SearchResult


class MetadataExtractor:
    """Извлечение метаданных из изображений"""
    
    def __init__(self):
        self.console = Console()
    
    def extract(self, filepath: str) -> SearchResult:
        """
        Извлечение метаданных из изображения
        
        Поддерживаемые форматы: JPEG, PNG, TIFF, WEBP
        Извлекается: EXIF, GPS, информация о файле
        """
        
        results = {}
        
        # 1. Проверка существования файла
        path = Path(filepath)
        if not path.exists():
            return SearchResult(
                query=filepath,
                mode='metadata',
                found={'error': 'Файл не найден'},
                total_checked=0
            )
        
        # 2. Информация о файле
        file_info = self._get_file_info(path)
        results['file_info'] = file_info
        
        # 3. EXIF данные
        try:
            exif_data = self._get_exif_data(path)
            if exif_data:
                results['exif'] = exif_data
        except Exception as e:
            self.console.print(f"[dim]Ошибка чтения EXIF: {e}[/dim]")
        
        # 4. GPS данные
        try:
            gps_data = self._get_gps_data(path, results.get('exif', {}))
            if gps_data:
                results['gps'] = gps_data
        except Exception as e:
            self.console.print(f"[dim]Ошибка чтения GPS: {e}[/dim]")
        
        # 5. Дополнительная информация
        try:
            additional = self._get_additional_info(path)
            if additional:
                results['additional'] = additional
        except Exception as e:
            self.console.print(f"[dim]Ошибка чтения доп. информации: {e}[/dim]")
        
        return SearchResult(
            query=filepath,
            mode='metadata',
            found=results,
            total_checked=5
        )
    
    def _get_file_info(self, path: Path) -> Dict:
        """Основная информация о файле"""
        stat = path.stat()
        
        # Расширения изображений
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.heic', '.heif'}
        is_image = path.suffix.lower() in image_extensions
        
        # Размеры в человекочитаемом формате
        size_bytes = stat.st_size
        size_kb = size_bytes / 1024
        size_mb = size_kb / 1024
        
        if size_mb >= 1:
            size_human = f"{size_mb:.2f} MB"
        elif size_kb >= 1:
            size_human = f"{size_kb:.2f} KB"
        else:
            size_human = f"{size_bytes} bytes"
        
        return {
            'filename': path.name,
            'full_path': str(path.absolute()),
            'extension': path.suffix.lower(),
            'size_bytes': size_bytes,
            'size_human': size_human,
            'is_image': is_image,
            'created': self._format_timestamp(stat.st_ctime),
            'modified': self._format_timestamp(stat.st_mtime),
            'accessed': self._format_timestamp(stat.st_atime)
        }
    
    def _get_exif_data(self, path: Path) -> Optional[Dict]:
        """Извлечение EXIF данных"""
        exif = {}
        
        # Попытка использовать Pillow
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS, GPSTAGS
            
            with Image.open(path) as img:
                # Получаем EXIF данные
                exif_data = img._getexif()
                
                if exif_data:
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        
                        # Пропускаем GPS (обработаем отдельно)
                        if tag == 'GPSInfo':
                            continue
                        
                        # Обработка сложных значений
                        if isinstance(value, bytes):
                            try:
                                value = value.decode('utf-8', errors='ignore')
                            except:
                                value = str(value)
                        elif isinstance(value, tuple):
                            value = str(value)
                        
                        # Сопоставление популярных тегов
                        tag_mapping = {
                            'Make': 'camera_make',
                            'Model': 'camera_model',
                            'DateTime': 'date_time',
                            'DateTimeOriginal': 'date_time_original',
                            'DateTimeDigitized': 'date_time_digitized',
                            'ExposureTime': 'exposure_time',
                            'FNumber': 'f_number',
                            'ISO': 'iso',
                            'FocalLength': 'focal_length',
                            'LensModel': 'lens_model',
                            'LensMake': 'lens_make',
                            'Software': 'software',
                            'Artist': 'artist',
                            'Copyright': 'copyright',
                            'ImageDescription': 'description',
                            'Orientation': 'orientation',
                            'XResolution': 'x_resolution',
                            'YResolution': 'y_resolution',
                            'ResolutionUnit': 'resolution_unit',
                            'ColorSpace': 'color_space',
                            'PixelXDimension': 'pixel_x_dimension',
                            'PixelYDimension': 'pixel_y_dimension',
                            'Flash': 'flash',
                            'WhiteBalance': 'white_balance',
                            'ExposureMode': 'exposure_mode',
                            'MeteringMode': 'metering_mode',
                            'SceneCaptureType': 'scene_capture_type',
                            'GPSInfo': 'gps_info'
                        }
                        
                        mapped_tag = tag_mapping.get(tag, tag)
                        exif[mapped_tag] = value
                
                # Получаем размеры изображения
                exif['image_width'] = img.width
                exif['image_height'] = img.height
                exif['format'] = img.format
                exif['mode'] = img.mode
                
        except ImportError:
            self.console.print("[dim]Pillow не установлен, пропускаем EXIF[/dim]")
        except Exception as e:
            self.console.print(f"[dim]Ошибка чтения EXIF: {e}[/dim]")
        
        return exif if exif else None
    
    def _get_gps_data(self, path: Path, exif_data: Dict) -> Optional[Dict]:
        """Извлечение GPS данных"""
        gps = {}
        
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS, GPSTAGS
            
            with Image.open(path) as img:
                exif_data_raw = img._getexif()
                
                if not exif_data_raw:
                    return None
                
                gps_info = exif_data_raw.get(34853)  # GPSInfo tag ID
                
                if not gps_info:
                    return None
                
                for tag_id, value in gps_info.items():
                    tag = GPSTAGS.get(tag_id, tag_id)
                    
                    if isinstance(value, bytes):
                        try:
                            value = value.decode('utf-8', errors='ignore')
                        except:
                            value = str(value)
                    elif isinstance(value, tuple):
                        # Обработка GPS координат (градусы, минуты, секунды)
                        if len(value) == 3:
                            try:
                                degrees = value[0][0] / value[0][1] if value[0][1] != 0 else 0
                                minutes = value[1][0] / value[1][1] if value[1][1] != 0 else 0
                                seconds = value[2][0] / value[2][1] if value[2][1] != 0 else 0
                                value = degrees + minutes/60 + seconds/3600
                            except:
                                value = str(value)
                        else:
                            value = str(value)
                    
                    gps[tag] = value
                
                # Преобразование координат в десятичный формат
                if 'GPSLatitude' in gps and 'GPSLatitudeRef' in gps:
                    lat = gps['GPSLatitude']
                    lat_ref = gps['GPSLatitudeRef']
                    if isinstance(lat, (int, float)):
                        if lat_ref == 'S':
                            lat = -lat
                        gps['latitude'] = lat
                
                if 'GPSLongitude' in gps and 'GPSLongitudeRef' in gps:
                    lon = gps['GPSLongitude']
                    lon_ref = gps['GPSLongitudeRef']
                    if isinstance(lon, (int, float)):
                        if lon_ref == 'W':
                            lon = -lon
                        gps['longitude'] = lon
                
                # Добавляем ссылку на Google Maps если есть координаты
                if 'latitude' in gps and 'longitude' in gps:
                    gps['google_maps_url'] = f"https://www.google.com/maps?q={gps['latitude']},{gps['longitude']}"
                    
        except ImportError:
            pass
        except Exception as e:
            self.console.print(f"[dim]Ошибка чтения GPS: {e}[/dim]")
        
        return gps if gps else None
    
    def _get_additional_info(self, path: Path) -> Optional[Dict]:
        """Дополнительная информация"""
        additional = {}
        
        # Попытка использовать exifread
        try:
            import exifread
            
            with open(path, 'rb') as f:
                tags = exifread.process_file(f, stop_tag='thumbnail')
                
                for tag in tags.keys():
                    key = str(tag)
                    value = str(tags[tag])
                    
                    if key not in additional and len(value) < 200:
                        additional[key] = value
                        
        except ImportError:
            pass
        except Exception:
            pass
        
        # Проверка на наличие IPTC данных
        try:
            from PIL import Image
            from PIL import IptcImagePlugin
            
            with Image.open(path) as img:
                if hasattr(img, 'info'):
                    iptc = img.info.get('iptc')
                    if iptc:
                        additional['iptc'] = str(iptc)[:500]
        except:
            pass
        
        return additional if additional else None
    
    def _format_timestamp(self, timestamp: float) -> str:
        """Форматирование временной метки"""
        from datetime import datetime
        try:
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        except:
            return str(timestamp)
