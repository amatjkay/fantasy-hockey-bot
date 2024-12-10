import requests
import json
from datetime import datetime
import logging
from telegram import Bot
from dotenv import load_dotenv
import os
import asyncio
from PIL import Image, ImageDraw, ImageFont
import pytz

# Конфигурация
LOG_FILE = "/home/lex/dev/bot/fantasy-hockey-bot/log.txt"
PLAYER_STATS_FILE = "/home/lex/dev/bot/fantasy-hockey-bot/player_stats.json"
MOSCOW_TIMEZONE = pytz.timezone('Europe/Moscow')

# Грейды игроков и их цвета
GRADE_COLORS = {
    "common": "black",
    "uncommon": "green",
    "rare": "blue",
    "epic": "purple",
    "legend": "orange"
}

# Логирование
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Загрузка переменных окружения
load_dotenv('/home/lex/dev/bot/fantasy-hockey-bot/.env')

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

if not TELEGRAM_TOKEN or not CHAT_ID:
    logging.error("TELEGRAM_TOKEN или CHAT_ID не установлены в файле .env.")
    exit(1)

bot = Bot(token=TELEGRAM_TOKEN)


def load_player_stats():
    """Загружает статистику игроков из файла."""
    if os.path.exists(PLAYER_STATS_FILE):
        with open(PLAYER_STATS_FILE, "r") as f:
            return json.load(f)
    return {}


def get_top_players(stats):
    """Определяет лучших игроков недели по позициям."""
    positions = {'C': [], 'LW': [], 'RW': [], 'D': [], 'G': []}

    for name, player_data in stats.items():
        grade = player_data.get('grade', 'common')
        color = GRADE_COLORS.get(grade, 'black')
        last_position = player_data.get('last_position', None)

        if not last_position:
            logging.warning(f"Игрок {name} не имеет позиции 'last_position'. Пропускаем.")
            continue

        logging.info(f"Обрабатываем игрока: {name}, позиция: {last_position}, очки: {player_data['total_points']}")
        positions[last_position].append({
            'name': name,
            'total_points': player_data['total_points'],
            'appearances': player_data['appearances'],
            'grade': grade,
            'color': color,
        })

    team = {
        'C': sorted(positions['C'], key=lambda x: x['total_points'], reverse=True)[:1],
        'LW': sorted(positions['LW'], key=lambda x: x['total_points'], reverse=True)[:1],
        'RW': sorted(positions['RW'], key=lambda x: x['total_points'], reverse=True)[:1],
        'D': sorted(positions['D'], key=lambda x: x['total_points'], reverse=True)[:2],
        'G': sorted(positions['G'], key=lambda x: x['total_points'], reverse=True)[:1]
    }

    logging.info(f"Сформированная команда недели: {team}")
    return team



def create_collage(team):
    """Создает изображение коллажа для команды недели."""
    player_img_width, player_img_height = 130, 100
    padding = 20
    text_padding = 10
    line_height = player_img_height + text_padding + 30 + padding

    total_players = sum(len(players) for players in team.values())
    height = total_players * line_height + padding * 2

    width = 500
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    font_path = "/usr/share/fonts/ttf/dejavu/DejaVuSans.ttf"
    font = ImageFont.truetype(font_path, size=20)

    y_offset = padding
    for position, players in team.items():
        for player in players:
            name = player['name']
            points = player['total_points']
            color = player['color']

            # Формируем текст
            text = f"{position}: {name} ({points:.2f} ftps)"
            text_width = draw.textlength(text, font=font)
            text_x = (width - text_width) // 2

            # Рисуем текст
            draw.text((text_x, y_offset), text, fill=color, font=font)

            y_offset += line_height

    file_path = "/home/lex/dev/bot/fantasy-hockey-bot/team_week_collage.jpg"
    image.save(file_path)
    return file_path


async def send_collage(team):
    """Отправляет коллаж с командой в Telegram."""
    file_path = create_collage(team)
    try:
        with open(file_path, "rb") as photo:
            await bot.send_photo(chat_id=CHAT_ID, photo=photo, caption="🏒 <b>Команда недели</b>", parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка при отправке изображения: {e}")


async def main():
    logging.info("Запуск формирования команды недели.")
    stats = load_player_stats()

    if not stats:
        logging.error("Файл player_stats.json пуст или отсутствует.")
        return

    team = get_top_players(stats)
    await send_collage(team)


if __name__ == "__main__":
    asyncio.run(main())
