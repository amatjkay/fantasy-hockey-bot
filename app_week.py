import json
import logging
from datetime import datetime, timedelta
import pytz
import os
import platform
from pathlib import Path
from telegram import Bot
from telegram.constants import ParseMode
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import asyncio
import requests

# Определение базовой директории проекта
BASE_DIR = Path(__file__).resolve().parent

# Конфигурация
LOG_FILE = BASE_DIR / "log.txt"
PLAYER_STATS_FILE = BASE_DIR / "player_stats.json"
ESPN_TIMEZONE = pytz.timezone('US/Eastern')

# Определение путей к шрифтам для разных ОС
FONT_PATHS = {
    'Windows': [
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
    ],
    'Linux': [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ],
    'Darwin': [  # macOS
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/SFNSText.ttf",
    ]
}

POSITION_MAP = {
    'C': 1,
    'LW': 1,
    'RW': 1,
    'D': 2,
    'G': 1
}

GRADE_COLORS = {
    "common": "black",
    "uncommon": "green",
    "rare": "blue",
    "epic": "purple",
    "legend": "orange"
}

def setup_logging():
    """Настройка логирования с учетом кроссплатформенности"""
    log_dir = BASE_DIR
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        filename=str(LOG_FILE),
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        encoding='utf-8'
    )

def get_system_font():
    """Получение системного шрифта в зависимости от ОС"""
    system = platform.system()
    font_paths = FONT_PATHS.get(system, [])
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, size=20)
                logging.info(f"Используется шрифт: {font_path}")
                return font
            except Exception as e:
                logging.warning(f"Не удалось загрузить шрифт {font_path}: {e}")
    
    logging.warning("Используется дефолтный шрифт, так как не найдены системные шрифты")
    return ImageFont.load_default()

# Настройка логирования
setup_logging()

# Загрузка переменных окружения
env_path = BASE_DIR / '.env'
load_dotenv(env_path)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

if not TELEGRAM_TOKEN or not CHAT_ID:
    logging.error("TELEGRAM_TOKEN или CHAT_ID не установлены в файле .env")
    exit(1)

bot = Bot(token=TELEGRAM_TOKEN)

def get_previous_week_dates():
    """Получение дат предыдущей недели"""
    espn_now = datetime.now(ESPN_TIMEZONE)
    days_since_tuesday = (espn_now.weekday() - 1) % 7
    current_tuesday = espn_now - timedelta(days=days_since_tuesday)
    current_tuesday = current_tuesday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    previous_tuesday = current_tuesday - timedelta(days=7)
    previous_monday = previous_tuesday + timedelta(days=6)
    previous_monday = previous_monday.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return previous_tuesday, previous_monday

def get_week_team(week_key):
    """Получение лучшей команды за неделю"""
    try:
        with open(PLAYER_STATS_FILE, 'r') as f:
            data = json.load(f)
            
        week_data = data.get("weeks", {}).get(week_key, {}).get("players", {})
        if not week_data:
            logging.error(f"Нет данных для недели {week_key}")
            return None
            
        positions = {'C': [], 'LW': [], 'RW': [], 'D': [], 'G': []}
        
        for player_id, player_info in week_data.items():
            total_points = player_info.get("total_points", 0)
            name = player_info.get("name", "Unknown")
            grade = player_info.get("grade", "common")
            
            for position in player_info.get("positions", []):
                if position in positions:
                    positions[position].append({
                        'id': player_id,
                        'name': name,
                        'total_points': total_points,
                        'grade': grade,
                        'image_url': f"https://a.espncdn.com/combiner/i?img=/i/headshots/nhl/players/full/{player_id}.png&w=130&h=100"
                    })
        
        # Сортируем игроков по очкам и выбираем лучших для каждой позиции
        team = {}
        for position, count in POSITION_MAP.items():
            sorted_players = sorted(positions[position], key=lambda x: x['total_points'], reverse=True)
            team[position] = sorted_players[:count]
            
        return team
    except Exception as e:
        logging.error(f"Ошибка при получении команды недели: {str(e)}")
        return None

def create_week_collage(team, week_key):
    """Создание коллажа команды недели"""
    player_img_width, player_img_height = 130, 100
    padding = 20
    text_padding = 10
    line_height = player_img_height + text_padding + 30 + padding

    total_players = sum(len(players) for players in team.values())
    height = total_players * line_height + padding * 2
    width = 500

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    # Получение системного шрифта
    font = get_system_font()

    y_offset = padding
    
    # Заголовок
    start_date, end_date = week_key.split('_')
    title = f"Команда недели ({start_date} - {end_date})"
    try:
        title_width = draw.textlength(title, font=font)
    except AttributeError:
        title_width = font.getlength(title)
    draw.text(((width - title_width) // 2, y_offset), title, fill="black", font=font)
    y_offset += 40

    for position, players in team.items():
        for player in players:
            name = player['name']
            points = player['total_points']
            image_url = player['image_url']
            grade = player['grade']
            color = GRADE_COLORS.get(grade, "black")

            try:
                response = requests.get(image_url, stream=True, timeout=10)
                response.raise_for_status()
                player_image = Image.open(response.raw).convert("RGBA")
                bg = Image.new("RGBA", player_image.size, (255, 255, 255, 255))
                combined_image = Image.alpha_composite(bg, player_image)
                player_image = combined_image.convert("RGB").resize((player_img_width, player_img_height), Image.LANCZOS)
                image_x = (width - player_img_width) // 2
                image.paste(player_image, (image_x, y_offset))
            except Exception as e:
                logging.warning(f"Ошибка загрузки изображения для {name}: {e}")
                empty_img = Image.new("RGB", (player_img_width, player_img_height), "gray")
                image_x = (width - player_img_width) // 2
                image.paste(empty_img, (image_x, y_offset))

            text = f"{position}: {name} ({points:.2f} ftps)"
            try:
                text_width = draw.textlength(text, font=font)
            except AttributeError:
                text_width = font.getlength(text)
            text_x = (width - text_width) // 2
            draw.text((text_x, y_offset + player_img_height + text_padding), text, fill=color, font=font)
            y_offset += line_height

    file_path = BASE_DIR / f"team_week_collage_{week_key}.jpg"
    image.save(str(file_path))
    return file_path

async def send_week_collage(team, week_key):
    """Отправка коллажа команды недели в Telegram"""
    try:
        file_path = create_week_collage(team, week_key)
        
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                with open(file_path, 'rb') as photo:
                    await bot.send_photo(chat_id=CHAT_ID, photo=photo, parse_mode=ParseMode.HTML)
                logging.info(f"Коллаж команды недели успешно отправлен для {week_key}")
                break
            except Exception as e:
                if attempt < max_attempts:
                    logging.warning(f"Попытка {attempt} из {max_attempts} не удалась: {str(e)}")
                    await asyncio.sleep(1)
                else:
                    logging.error(f"Не удалось отправить коллаж после {max_attempts} попыток: {str(e)}")
                    await send_week_text(team, week_key)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        logging.error(f"Ошибка при создании/отправке коллажа недели: {str(e)}")
        await send_week_text(team, week_key)

async def send_week_text(team, week_key):
    """Отправка текстового сообщения с командой недели"""
    try:
        start_date, end_date = week_key.split('_')
        message = f"\U0001F3D2 Команда недели ({start_date} - {end_date})\n\n"
        for position, players in team.items():
            for player in players:
                message += f"{position}: {player['name']} ({player['total_points']:.2f} ftps)\n"
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=ParseMode.HTML)
        logging.info(f"Текстовое сообщение команды недели успешно отправлено для {week_key}")
    except Exception as e:
        logging.error(f"Не удалось отправить текстовое сообщение команды недели: {str(e)}")

async def main():
    try:
        # Получаем даты предыдущей недели
        previous_tuesday, previous_monday = get_previous_week_dates()
        week_key = f"{previous_tuesday.strftime('%Y-%m-%d')}_{previous_monday.strftime('%Y-%m-%d')}"
        
        logging.info(f"Обработка команды недели: {week_key}")
        
        # Получаем команду недели
        team = get_week_team(week_key)
        if team:
            # Отправляем коллаж
            await send_week_collage(team, week_key)
        else:
            logging.error("Не удалось получить команду недели")
            
    except Exception as e:
        logging.error(f"Ошибка при выполнении скрипта: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 