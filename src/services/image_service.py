from typing import Dict, List, Optional, Tuple
import os
import logging
import requests
from PIL import Image, ImageDraw, ImageFont
from ..config import settings
import time

logger = logging.getLogger(__name__)

class ImageService:
    """Сервис для работы с изображениями"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.collage_dir = os.path.join(settings.DATA_DIR, 'collages')
        self.photos_dir = os.path.join(settings.DATA_DIR, 'photos')
        os.makedirs(self.collage_dir, exist_ok=True)
        os.makedirs(self.photos_dir, exist_ok=True)
        
        # Создаем директорию для шрифтов
        self.fonts_dir = os.path.join(settings.ASSETS_DIR, 'fonts')
        os.makedirs(self.fonts_dir, exist_ok=True)
        
        # Путь к шрифту
        self.font_path = os.path.join(self.fonts_dir, 'Roboto-Regular.ttf')
        if not os.path.exists(self.font_path):
            self._download_font()
            
    def _download_font(self):
        """Скачивание шрифта Roboto"""
        try:
            font_url = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf"
            response = requests.get(font_url)
            response.raise_for_status()
            
            with open(self.font_path, 'wb') as f:
                f.write(response.content)
                
            self.logger.info(f"Шрифт Roboto успешно скачан: {self.font_path}")
            
        except Exception as e:
            self.logger.error(f"Ошибка при скачивании шрифта: {e}")
            raise
            
    def get_player_photo(self, player_id: str, player_name: str) -> Optional[str]:
        """Получение фотографии игрока
        
        Args:
            player_id (str): ID игрока
            player_name (str): Имя игрока
            
        Returns:
            Optional[str]: Путь к фотографии игрока
        """
        try:
            # Проверяем наличие фото в кэше
            photo_path = os.path.join(self.photos_dir, f"{player_id}.png")
            if os.path.exists(photo_path):
                return photo_path
                
            # Получаем URL фото
            photo_url = self._get_player_photo_url(player_id)
            if not photo_url:
                self.logger.warning(f"Не удалось получить URL фото для игрока {player_name} (ID: {player_id})")
                return None
                
            # Скачиваем фото
            response = requests.get(photo_url)
            if response.status_code != 200:
                self.logger.warning(f"Не удалось скачать фото для игрока {player_name} (ID: {player_id})")
                return None
                
            # Сохраняем фото
            with open(photo_path, 'wb') as f:
                f.write(response.content)
                
            self.logger.info(f"Фото игрока {player_name} успешно скачано")
            return photo_path
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении фото игрока {player_name}: {e}")
            return None
            
    def create_collage(
        self,
        player_photos: Dict[str, str],
        player_data: Dict,
        date: str,
        total_points: Optional[float]
    ) -> Optional[str]:
        """Создание коллажа из фотографий игроков"""
        try:
            self.logger.info(f"Начинаем создание коллажа для даты {date}")
            self.logger.info(f"Получено фотографий: {len(player_photos)}")
            self.logger.info(f"Данные игроков: {list(player_data.keys())}")
            
            # Размеры фото и коллажа
            photo_size = (130, 100)  # Ширина больше высоты
            padding = 10
            collage_width = photo_size[0] * 3 + padding * 4
            collage_height = photo_size[1] * 3 + padding * 4  # Увеличиваем высоту для вратаря
            positions = self._get_photo_positions(collage_width, collage_height)
            
            # Создаем новое изображение с прозрачным фоном
            collage_size = (collage_width, collage_height)
            collage = Image.new('RGBA', collage_size, (255, 255, 255, 0))
            
            # Добавляем фото игроков в порядке: LW, C, RW, D1, D2, G
            for pos in ['LW', 'C', 'RW', 'D1', 'D2', 'G']:
                if pos not in player_data:
                    self.logger.warning(f"Нет данных для позиции {pos}")
                    continue
                    
                player = player_data[pos]
                player_id = str(player['info']['id'])
                
                if player_id not in player_photos:
                    self.logger.warning(f"Нет фото для игрока {player['info']['name']} (ID: {player_id})")
                    continue
                    
                photo_path = player_photos[player_id]
                if not os.path.exists(photo_path):
                    self.logger.warning(f"Файл фото не существует: {photo_path}")
                    continue
                    
                # Открываем и изменяем размер фото
                photo = Image.open(photo_path)
                photo = photo.resize(photo_size, Image.Resampling.LANCZOS)
                
                # Определяем позицию для фото
                position = positions.get(pos)
                if not position:
                    self.logger.warning(f"Нет позиции для {pos}")
                    continue
                    
                self.logger.info(f"Добавляем фото игрока {player['info']['name']} на позицию {pos}")
                
                # Вставляем фото
                collage.paste(photo, position)
            
            # Сохраняем коллаж
            collage_path = os.path.join(self.collage_dir, f'team_{int(time.time())}.png')
            collage.save(collage_path)
            
            return collage_path
            
        except Exception as e:
            self.logger.error(f"Ошибка при создании коллажа: {e}")
            return None
            
    def _get_photo_positions(self, width: int, height: int) -> Dict[str, Tuple[int, int]]:
        """Возвращает позиции для фото игроков
        
        Args:
            width: Ширина коллажа
            height: Высота коллажа
            
        Returns:
            Dict[str, Tuple[int, int]]: Словарь позиций для каждой позиции игрока
        """
        # Размер фото игрока
        photo_size = (130, 100)  # Ширина больше высоты
        padding = 10
        
        # Первый ряд: LW, C, RW
        row1_y = padding
        row1_x = [padding, width//2, width - padding - photo_size[0]]  # LW слева, C по центру, RW справа
        
        # Второй ряд: D1, D2
        row2_y = photo_size[1] + padding * 2
        row2_x = [width//3, 2*width//3]
        
        # Третий ряд: G (значительно ниже)
        row3_y = (photo_size[1] + padding) * 2
        row3_x = width//2
        
        positions = {}
        
        # Добавляем позиции для каждой позиции игрока
        positions['LW'] = (row1_x[0], row1_y)  # Левый нападающий слева
        positions['C'] = (row1_x[1] - photo_size[0]//2, row1_y)  # Центральный по центру
        positions['RW'] = (row1_x[2], row1_y)  # Правый нападающий справа
        positions['D1'] = (row2_x[0] - photo_size[0]//2, row2_y)
        positions['D2'] = (row2_x[1] - photo_size[0]//2, row2_y)
        positions['G'] = (row3_x - photo_size[0]//2, row3_y)
        
        return positions
        
    def _get_player_photo_url(self, player_id: str) -> Optional[str]:
        """Получает URL фото игрока"""
        return f"https://a.espncdn.com/i/headshots/nhl/players/full/{player_id}.png"

    def create_team_collage(self, player_photos: dict, team: dict, title: str) -> str:
        """Создание коллажа команды недели
        
        Args:
            player_photos (dict): Словарь с путями к фотографиям игроков
            team (dict): Словарь с информацией об игроках
            title (str): Заголовок коллажа
            
        Returns:
            str: Путь к созданному коллажу
        """
        try:
            # Создаем пустое изображение для коллажа
            collage = Image.new('RGB', (1200, 800), 'white')
            draw = ImageDraw.Draw(collage)
            
            # Загружаем шрифт
            title_font = ImageFont.truetype(self.font_path, 36)
            stats_font = ImageFont.truetype(self.font_path, 24)
            
            # Добавляем заголовок
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            draw.text(((1200 - title_width) // 2, 20), title, font=title_font, fill='black')
            
            # Позиции для фотографий игроков
            positions = {
                'G': (500, 150),
                'D1': (200, 300),
                'D2': (800, 300),
                'LW': (200, 500),
                'C': (500, 500),
                'RW': (800, 500)
            }
            
            # Размер фотографии игрока
            photo_size = (200, 200)
            
            # Добавляем фотографии и статистику игроков
            for pos, coords in positions.items():
                if pos in team:
                    player = team[pos]
                    player_id = str(player['info']['id'])
                    
                    if player_id in player_photos:
                        # Загружаем и изменяем размер фото
                        photo = Image.open(player_photos[player_id])
                        photo = photo.resize(photo_size, Image.Resampling.LANCZOS)
                        
                        # Вычисляем позицию для фото (центрируем относительно заданных координат)
                        photo_x = coords[0] - photo_size[0] // 2
                        photo_y = coords[1] - photo_size[1] // 2
                        
                        # Вставляем фото
                        collage.paste(photo, (photo_x, photo_y))
                        
                        # Добавляем имя игрока и очки
                        player_text = f"{player['info']['name']}\n{player['stats']['total_points']} pts"
                        text_bbox = draw.textbbox((0, 0), player_text, font=stats_font)
                        text_width = text_bbox[2] - text_bbox[0]
                        text_x = coords[0] - text_width // 2
                        text_y = photo_y + photo_size[1] + 10
                        draw.text((text_x, text_y), player_text, font=stats_font, fill='black', align='center')
            
            # Сохраняем коллаж
            collage_path = os.path.join(self.collage_dir, f'team_of_week_{int(time.time())}.png')
            collage.save(collage_path)
            
            return collage_path
            
        except Exception as e:
            self.logger.error(f"Ошибка при создании коллажа команды недели: {e}")
            return None
