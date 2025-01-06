import argparse
import asyncio
import logging
from datetime import datetime
from src.services.team_service import TeamService
from src.services.telegram_service import TelegramService
from src.config.settings import PLAYER_POSITIONS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def format_telegram_message(team: dict) -> str:
    """Форматирует сообщение для Telegram"""
    message = [
        f"🏒 *Команда дня - {team['date']}*\n",
        "\n*Состав команды:*"
    ]
    
    # Сортируем игроков по позициям
    positions_order = ['C', 'LW', 'RW', 'D', 'G']
    players_by_pos = {pos: [] for pos in positions_order}
    
    for player_id, player in team['players'].items():
        position = PLAYER_POSITIONS[player['info']['primary_position']]
        players_by_pos[position].append(player)
        
    # Добавляем игроков в сообщение
    for pos in positions_order:
        for player in players_by_pos[pos]:
            message.append(
                f"\n{pos}: {player['info']['name']} - {player['stats']['total_points']} очков"
            )
            
    message.append(f"\n\n*Общие очки команды:* {team['total_points']}")
    
    return ''.join(message)

async def main():
    parser = argparse.ArgumentParser(description='Формирование команды дня')
    parser.add_argument('--date', type=str, help='Дата в формате YYYY-MM-DD')
    parser.add_argument('--no-send', action='store_true', help='Не отправлять в Telegram')
    args = parser.parse_args()
    
    # Определяем дату
    if args.date:
        date = datetime.strptime(args.date, '%Y-%m-%d')
    else:
        date = datetime.now()
        
    logger.info(f"Запуск сбора статистики за {date.strftime('%Y-%m-%d')}")
    
    # Создаем команду дня
    team_service = TeamService()
    team = team_service.get_team_of_day(date)
    
    if not team:
        logger.error("Не удалось сформировать команду дня")
        return
        
    logger.info(f"Команда дня сформирована, общие очки: {team['total_points']}")
    
    # Создаем коллаж
    collage_path = team_service.create_team_collage(team)
    if not collage_path:
        logger.error("Не удалось создать коллаж")
        return
        
    logger.info(f"Коллаж создан: {collage_path}")
    
    # Отправляем в Telegram
    if not args.no_send:
        telegram = TelegramService()
        message = format_telegram_message(team)
        sent = await telegram.send_team_of_day(message, collage_path)
        if sent:
            logger.info("Результаты успешно отправлены в Telegram")
        else:
            logger.error("Ошибка при отправке в Telegram")

if __name__ == '__main__':
    asyncio.run(main())
