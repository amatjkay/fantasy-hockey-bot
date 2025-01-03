import os
from typing import Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont
from src.utils.logging import setup_logging

class ImageService:
    """Сервис для работы с изображениями"""

    def __init__(self):
        """Инициализация сервиса"""
        self.logger = setup_logging(__name__)
        
        # Пути к директориям
        self.PHOTOS_DIR = os.path.join('data', 'photos')
        self.COLLAGES_DIR = os.path.join('data', 'collages')
        
        # Создаем директории если не существуют
        os.makedirs(self.PHOTOS_DIR, exist_ok=True)
        os.makedirs(self.COLLAGES_DIR, exist_ok=True)
        
        # Загружаем системный шрифт
        self.font_path = self._load_system_font()
        if not self.font_path:
            raise Exception("Не удалось загрузить системный шрифт")
            
        # Размеры коллажа
        self.COLLAGE_WIDTH = 1200
        self.COLLAGE_HEIGHT = 800
        
        # Размеры элементов
        self.player_img_width = 200
        self.player_img_height = 200
        self.TITLE_FONT_SIZE = 36
        self.NAME_FONT_SIZE = 24
        self.STATS_FONT_SIZE = 20
        self.GRADE_FONT_SIZE = 24
        
        # Координаты заголовка
        self.TITLE_Y = 30
        
        # Координаты позиций игроков
        self.POSITION_COORDS = {
            'G': (500, 100),   # Вратарь
            'D': (200, 300),   # Защитник
            'C': (500, 300),   # Центральный
            'LW': (800, 300),  # Левый крайний
            'RW': (500, 500)   # Правый крайний
        }
        
        # Цвета грейдов
        self.GRADE_COLORS = {
            'common': 'black',
            'rare': 'blue',
            'epic': 'purple',
            'legendary': 'gold'
        }
        
    def create_team_collage(self, players: Dict[str, List[Dict]], title: str) -> str:
        """Создание коллажа команды
        
        Args:
            players (Dict[str, List[Dict]]): Словарь игроков по позициям
            title (str): Заголовок коллажа
            
        Returns:
            str: Путь к созданному коллажу
        """
        try:
            # Создаем базовое изображение
            collage = Image.new('RGB', (self.COLLAGE_WIDTH, self.COLLAGE_HEIGHT), 'white')
            draw = ImageDraw.Draw(collage)
            
            # Добавляем заголовок
            title_font = ImageFont.truetype(self.font_path, self.TITLE_FONT_SIZE)
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (self.COLLAGE_WIDTH - title_width) // 2
            draw.text((title_x, self.TITLE_Y), title, font=title_font, fill='black')
            
            # Добавляем игроков
            for position, position_players in players.items():
                if not position_players:
                    continue
                    
                # Берем лучшего игрока на позиции
                player = position_players[0]
                
                # Получаем координаты для позиции
                if position not in self.POSITION_COORDS:
                    self.logger.warning(f"Неизвестная позиция: {position}")
                    continue
                    
                x, y = self.POSITION_COORDS[position]
                
                # Добавляем фото игрока
                player_id = player['id']
                player_name = player.get('fullName') or player.get('name', 'Unknown Player')
                player_grade = player.get('grade', 'N/A')
                
                # Загружаем фото игрока
                player_photo = self._get_player_photo(player_id)
                if player_photo:
                    collage.paste(player_photo, (x, y))
                
                # Добавляем имя игрока
                name_font = ImageFont.truetype(self.font_path, self.NAME_FONT_SIZE)
                name_bbox = draw.textbbox((0, 0), player_name, font=name_font)
                name_width = name_bbox[2] - name_bbox[0]
                name_x = x + (self.player_img_width - name_width) // 2
                draw.text((name_x, y + self.player_img_height + 10), player_name, font=name_font, fill='black')
                
                # Добавляем грейд
                grade_font = ImageFont.truetype(self.font_path, self.GRADE_FONT_SIZE)
                grade_bbox = draw.textbbox((0, 0), player_grade, font=grade_font)
                grade_width = grade_bbox[2] - grade_bbox[0]
                grade_x = x + (self.player_img_width - grade_width) // 2
                draw.text((grade_x, y + self.player_img_height + 40), player_grade, font=grade_font, fill='black')
            
            # Сохраняем коллаж
            output_path = os.path.join(self.COLLAGES_DIR, f"{title.replace(' ', '_')}.jpg")
            collage.save(output_path)
            return output_path
            
        except Exception as e:
            self.logger.error(f"Ошибка при создании коллажа: {str(e)}")
            return None
            
    def create_week_collage(self, players: Dict[str, List[Dict]], week: str, output_path: str) -> str:
        """Создание коллажа команды недели
        
        Args:
            players (Dict[str, List[Dict]]): Словарь игроков по позициям
            week (str): Неделя в формате YYYY-MM-DD_YYYY-MM-DD
            output_path (str): Путь для сохранения коллажа
            
        Returns:
            str: Путь к созданному коллажу
        """
        title = f"Team of the Week ({week})"
        return self.create_team_collage(players, title)
            
    def _format_stats(self, position: str, stats: Dict) -> str:
        """Форматирование статистики игрока
        
        Args:
            position (str): Позиция игрока
            stats (Dict): Статистика игрока
            
        Returns:
            str: Отформатированная строка статистики
        """
        try:
            if position == 'G':
                # Статистика вратаря
                saves = stats.get('saves', 0)
                goals_against = stats.get('goalsAgainst', 0)
                shutouts = stats.get('shutouts', 0)
                return f"Saves: {saves} GA: {goals_against} SO: {shutouts}"
            else:
                # Статистика полевого игрока
                goals = stats.get('goals', 0)
                assists = stats.get('assists', 0)
                points = goals + assists
                return f"G: {goals} A: {assists} P: {points}"
                
        except Exception as e:
            self.logger.error(f"Ошибка форматирования статистики: {e}")
            return ""
            
    def _load_system_font(self) -> Optional[str]:
        """Загрузка системного шрифта
        
        Returns:
            Optional[str]: Путь к шрифту или None в случае ошибки
        """
        try:
            # Список путей к системным шрифтам
            font_paths = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',
                '/Library/Fonts/Arial.ttf',
                'C:\\Windows\\Fonts\\Arial.ttf'
            ]
            
            # Ищем первый доступный шрифт
            for path in font_paths:
                if os.path.exists(path):
                    self.logger.info(f"Используется системный шрифт: {path}")
                    return path
                    
            self.logger.error("Не найден подходящий системный шрифт")
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке системного шрифта: {e}")
            return None
