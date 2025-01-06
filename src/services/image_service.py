from typing import Dict, List, Optional, Tuple
import os
import logging
import requests
from PIL import Image, ImageDraw, ImageFont
from ..config import settings

logger = logging.getLogger(__name__)

class ImageService:
    def __init__(self):
        self.cache_dir = os.path.join(settings.CACHE_DIR, "player_images")
        self.collage_dir = os.path.join("data", "collages")
        self.font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"  # Стандартный системный шрифт
        self._ensure_dirs()
        
    def _ensure_dirs(self):
        """Создает необходимые директории"""
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.collage_dir, exist_ok=True)
        
    def get_player_photo(self, player_id: str, player_name: str) -> Optional[str]:
        """Получает фото игрока (из кэша или загружает)"""
        cache_path = os.path.join(self.cache_dir, f"{player_id}.png")
        
        # Проверяем кэш
        if os.path.exists(cache_path):
            return cache_path
            
        # Загружаем фото
        photo_url = self._get_player_photo_url(player_id)
        if not photo_url:
            logger.warning(f"Не найдено фото для игрока {player_name}")
            return None
            
        try:
            response = requests.get(photo_url, timeout=settings.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            with open(cache_path, 'wb') as f:
                f.write(response.content)
                
            return cache_path
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке фото игрока {player_name}: {e}")
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
            logger = logging.getLogger(__name__)
            logger.info(f"Начинаем создание коллажа для даты {date}")
            logger.info(f"Получено фотографий: {len(player_photos)}")
            logger.info(f"Данные игроков: {list(player_data.keys())}")
            
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
                try:
                    player = player_data[pos]
                    player_id = str(player['info']['id'])
                    if player_id not in player_photos:
                        logger.warning(f"Нет фото для игрока {player['info']['name']} (ID: {player_id})")
                        continue
                        
                    photo_path = player_photos[player_id]
                    if not os.path.exists(photo_path):
                        logger.warning(f"Файл фото не существует: {photo_path}")
                        continue
                        
                    # Открываем и изменяем размер фото
                    photo = Image.open(photo_path)
                    photo = photo.resize(photo_size, Image.Resampling.LANCZOS)
                    
                    # Определяем позицию для фото
                    position = positions.get(pos)
                    if not position:
                        logger.warning(f"Нет позиции для {pos}")
                        continue
                        
                    logger.info(f"Добавляем фото игрока {player['info']['name']} на позицию {pos}")
                    
                    # Вставляем фото
                    collage.paste(photo, position)
                    
                except Exception as e:
                    logger.error(f"Ошибка при добавлении фото игрока {player_id}: {e}")
                    continue
            
            # Сохраняем коллаж
            output_path = os.path.join(
                self.collage_dir,
                f"team_of_day_{date}.png"
            )
            collage.save(output_path, "PNG")
            logger.info(f"Коллаж сохранен: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Ошибка при создании коллажа: {e}")
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
