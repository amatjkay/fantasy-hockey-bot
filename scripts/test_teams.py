#!/usr/bin/env python3

from src.services.stats_service import StatsService
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('src.services.stats_service')
logger.setLevel(logging.DEBUG)

def print_player_stats(player):
    """Выводит статистику игрока"""
    stats = player["stats"]
    print(f'  - {player["info"]["name"]}:')
    print(f'    Очки: {stats["total_points"]}')
    print(f'    Голы: {stats["goals"]}')
    print(f'    Передачи: {stats["assists"]}')
    print(f'    Броски: {stats["shots"]}')
    if stats["saves"] > 0:  # Статистика вратаря
        print(f'    Сэйвы: {stats["saves"]}')
        print(f'    Пропущенные голы: {stats["goals_against"]}')

def main():
    service = StatsService()
    today = datetime.now()
    
    print(f'\nПолучаем статистику за {today.strftime("%Y-%m-%d")}')
    
    # Получаем команду дня
    team_of_day = service.get_team_of_the_day(today)
    
    if team_of_day and team_of_day["forwards"]:
        print('\nКоманда дня:')
        print('Форварды:')
        for player in team_of_day["forwards"]:
            print_player_stats(player)
            
        print('\nЗащитники:')
        for player in team_of_day["defense"]:
            print_player_stats(player)
            
        if team_of_day["goalie"]:
            print('\nВратарь:')
            print_player_stats(team_of_day["goalie"])
            
        print(f'\nВсего очков: {team_of_day["total_points"]}')
    else:
        print('\nНе удалось получить команду дня')
    
    print(f'\nПолучаем статистику за неделю ({(today - timedelta(days=6)).strftime("%Y-%m-%d")} - {today.strftime("%Y-%m-%d")})')
    
    # Получаем команду недели
    team_of_week = service.get_team_of_the_week(today)
    
    if team_of_week and team_of_week["forwards"]:
        print('\nКоманда недели:')
        print('Форварды:')
        for player in team_of_week["forwards"]:
            print_player_stats(player)
            
        print('\nЗащитники:')
        for player in team_of_week["defense"]:
            print_player_stats(player)
            
        if team_of_week["goalie"]:
            print('\nВратарь:')
            print_player_stats(team_of_week["goalie"])
            
        print(f'\nВсего очков за неделю: {team_of_week["total_points"]}')
    else:
        print('\nНе удалось получить команду недели')

if __name__ == '__main__':
    main() 