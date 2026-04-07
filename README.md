# 🐕 DoggyOSINT

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/OSINT-Tool-green.svg?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Legal-Use%20Only%20for%20Lawful%20Purposes-red.svg?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Version-1.0.0-orange.svg?style=for-the-badge"/>
</p>

**DoggyOSINT** — мощный инструмент командной строки для сбора информации из открытых источников (OSINT). Позволяет выполнять поиск по никнеймам, email-адресам, номерам телефонов, IP-адресам, доменам, а также извлекать метаданные из изображений.

> ⚠️ **Правовое предупреждение:** Данный инструмент предназначен **ТОЛЬКО** для законного использования (тестирование на проникновение с разрешения владельца, розыск пропавших людей, анализ собственной безопасности). Использование в противоправных целях преследуется по закону. Автор ( @moralfuck_project ) не несет ответственности за ваши действия.

---

## ✨ Возможности

| Режим | Описание | Источники / Методы |
| :--- | :--- | :--- |
| **👤 Поиск по нику** | Проверка наличия username на **500+** сайтах | VK, FB, IG, GitHub, Telegram, TikTok, Steam, Spotify, соц. сети, форумы, криптобиржи и др. |
| **📧 Поиск по Email** | Анализ email адреса | Валидация, привязка к домену, временные сервисы, утечки (HIBP), Gravatar |
| **📞 Поиск по телефону** | Информация о номере | Оператор, регион (РФ), ссылки на мессенджеры (TG, WA, Viber) |
| **🌐 Информация об IP** | Геолокация и данные | Публичные API (ip-api, ipinfo), тип IP (VPN/Proxy/Hosting), Reverse DNS |
| **🏠 Информация о домене** | WHOIS, DNS, SSL | WHOIS-сервера, DNS записи (A, MX, NS), SSL сертификаты |
| **🖼️ Метаданные фото** | EXIF, GPS, заголовки | Координаты, камера, дата съемки, софт (требуется Pillow) |

---

## 🚀 Быстрый старт

### 1. Клонирование репозитория
```bash
git clone https://github.com/moralfuck_project/DoggyOSINT.git
cd DoggyOSINT
pip install -r requirements.txt
python main.py [режим] [опции]
start.bat -n username


# Быстрый поиск (первые 100 сайтов)
python main.py -n durov --depth quick

# Стандартный поиск (300 сайтов)
python main.py -n durov --depth standard

# Полный поиск (все 500+ сайтов)
python main.py -n durov --depth deep --threads 30

# Экспорт в HTML
python main.py -n durov --export html
Поиск по Email
bash
python main.py -e test@example.com --check-breaches
Поиск по телефону
bash
python main.py -p +79991234567
IP адрес
bash
python main.py -i 8.8.8.8
Домен
bash
python main.py -d google.com
Метаданные изображения
bash
python main.py -m photo.jpg
Экспорт результатов
bash
python main.py -n username --export json    # JSON формат
python main.py -n username --export csv     # CSV таблица
python main.py -n username --export html    # Красивый HTML отчет
python main.py -n username --export all     # Все форматы сразу  
