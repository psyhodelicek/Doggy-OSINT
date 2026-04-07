"""
⚠️ ПРАВОВАЯ ИНФОРМАЦИЯ ⚠️
Инструмент для работы с ОТКРЫТЫМИ ИСТОЧНИКАМИ (OSINT)
"""

import re
import ipaddress
from typing import Tuple


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Проверка валидности email
    
    Returns:
        (valid, message) - кортеж с результатом и сообщением
    """
    if not email:
        return False, "Email пуст"
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, "Неверный формат email"
    
    # Проверка длины
    if len(email) > 254:
        return False, "Email слишком длинный"
    
    # Проверка локальной части
    local_part = email.split('@')[0]
    if len(local_part) > 64:
        return False, "Локальная часть слишком длинная"
    
    # Проверка на последовательные точки
    if '..' in email:
        return False, "Последовательные точки не допускаются"
    
    return True, "Email валиден"


def validate_phone(phone: str) -> Tuple[bool, str]:
    """
    Проверка валидности номера телефона
    
    Returns:
        (valid, message) - кортеж с результатом и сообщением
    """
    if not phone:
        return False, "Номер пуст"
    
    # Удаляем все нецифровые символы кроме +
    digits = re.sub(r'[^\d+]', '', phone)
    
    # Проверка на наличие + в начале
    has_plus = digits.startswith('+')
    digits_only = re.sub(r'\D', '', digits)
    
    # Проверка длины
    if len(digits_only) < 10:
        return False, "Номер слишком короткий"
    
    if len(digits_only) > 15:
        return False, "Номер слишком длинный"
    
    # Проверка кода страны
    country_codes = ['1', '7', '20', '27', '30', '31', '32', '33', '34', '36', 
                     '39', '40', '41', '43', '44', '45', '46', '47', '48', '49',
                     '51', '52', '53', '54', '55', '56', '57', '58', '60', '61',
                     '62', '63', '64', '65', '66', '81', '82', '84', '86', '90',
                     '91', '92', '93', '94', '95', '98', '212', '213', '216',
                     '218', '220', '221', '222', '223', '224', '225', '226',
                     '227', '228', '229', '230', '231', '232', '233', '234',
                     '235', '236', '237', '238', '239', '240', '241', '242',
                     '243', '244', '245', '246', '247', '248', '249', '250',
                     '251', '252', '253', '254', '255', '256', '257', '258',
                     '260', '261', '262', '263', '264', '265', '266', '267',
                     '268', '269', '290', '291', '297', '298', '299', '350',
                     '351', '352', '353', '354', '355', '356', '357', '358',
                     '359', '370', '371', '372', '373', '374', '375', '376',
                     '377', '378', '379', '380', '381', '382', '383', '385',
                     '386', '387', '389', '390', '391', '392', '393', '420',
                     '421', '423', '500', '501', '502', '503', '504', '505',
                     '506', '507', '508', '509', '590', '591', '592', '593',
                     '594', '595', '596', '597', '598', '599', '670', '672',
                     '673', '674', '675', '676', '677', '678', '679', '680',
                     '681', '682', '683', '685', '686', '687', '688', '689',
                     '690', '691', '692', '850', '852', '853', '855', '856',
                     '880', '886', '960', '961', '962', '963', '964', '965',
                     '966', '967', '968', '970', '971', '972', '973', '974',
                     '975', '976', '977', '992', '993', '994', '995', '996',
                     '998']
    
    # Проверка на популярные коды
    if digits_only.startswith('8') and len(digits_only) == 11:
        return True, "Российский номер (формат 8)"
    
    if digits_only.startswith('7') and len(digits_only) == 11:
        return True, "Российский/Казахстан номер"
    
    return True, "Номер валиден"


def validate_ip(ip: str) -> Tuple[bool, str]:
    """
    Проверка валидности IP-адреса
    
    Returns:
        (valid, message) - кортеж с результатом и сообщением
    """
    if not ip:
        return False, "IP пуст"
    
    try:
        ip_obj = ipaddress.ip_address(ip)
        
        if ip_obj.version == 4:
            return True, f"IPv4 адрес ({ip_obj})"
        elif ip_obj.version == 6:
            return True, f"IPv6 адрес ({ip_obj})"
        
    except ValueError:
        pass
    
    return False, "Неверный формат IP"


def validate_domain(domain: str) -> Tuple[bool, str]:
    """
    Простая проверка домена
    
    Returns:
        (valid, message) - кортеж с результатом и сообщением
    """
    if not domain:
        return False, "Домен пуст"
    
    # Базовая проверка
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$'
    
    if not re.match(pattern, domain):
        return False, "Неверный формат домена"
    
    # Проверка длины
    if len(domain) > 253:
        return False, "Домен слишком длинный"
    
    # Проверка на наличие поддомена
    parts = domain.split('.')
    if len(parts) < 2:
        return False, "Домен должен иметь как минимум домен и TLD"
    
    # Проверка TLD
    tld = parts[-1]
    if len(tld) < 2:
        return False, "Неверный TLD"
    
    return True, f"Домен валиден (TLD: .{tld})"


def normalize_phone(phone: str) -> str:
    """
    Нормализация номера телефона к формату +7XXXXXXXXXX
    
    Returns:
        Нормализованный номер
    """
    # Удаляем все нецифровые символы
    digits = re.sub(r'\D', '', phone)
    
    # Если начинается с 8, заменяем на 7
    if len(digits) == 11 and digits.startswith('8'):
        digits = '7' + digits[1:]
    
    # Если 10 цифр, добавляем 7
    if len(digits) == 10:
        digits = '7' + digits
    
    return f"+{digits}"


def extract_domain_from_email(email: str) -> str:
    """Извлечение домена из email"""
    if '@' in email:
        return email.split('@')[1]
    return ''


def get_domain_without_www(domain: str) -> str:
    """Удаление www. из домена"""
    if domain.startswith('www.'):
        return domain[4:]
    return domain
