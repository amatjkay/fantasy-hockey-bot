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
        total_points: float
    ) -> Optional[str]:
        """Создает коллаж команды"""
        try:
            # Создаем базовое изображение с прозрачным фоном
            width = 800
            height = 600
            collage = Image.new('RGBA', (width, height), (255, 255, 255, 0))
            draw = ImageDraw.Draw(collage)
            
            # Загружаем шрифт
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            # Добавляем заголовок
            draw.text(
                (width//2, 30),
                f"Команда дня - {date}",
                font=font,
                fill='black',
                anchor='mm'
            )
            
            # Размещаем фото игроков
            photo_size = (130, 100)
            positions = self._get_photo_positions(width, height)
            
            # Сортируем игроков по позициям
            positions_order = ['C', 'LW', 'RW', 'D', 'G']
            sorted_players = []
            for pos in positions_order:
                for player_id, player in player_data.items():
                    if settings.PLAYER_POSITIONS[player['info']['primary_position']] == pos:
                        sorted_players.append((player_id, player))
            
            for (player_id, player), position in zip(sorted_players, positions):
                if player_id not in player_photos:
                    continue
                    
                # Добавляем фото с прозрачным фоном
                try:
                    photo = Image.open(player_photos[player_id])
                    photo = photo.convert('RGBA')
                    photo = photo.resize(photo_size)
                    
                    # Создаем маску для прозрачности
                    mask = Image.new('L', photo.size, 0)
                    draw_mask = ImageDraw.Draw(mask)
                    draw_mask.ellipse([0, 0, photo.size[0], photo.size[1]], fill=255)
                    
                    # Создаем новое изображение с прозрачным фоном
                    output = Image.new('RGBA', photo.size, (0, 0, 0, 0))
                    
                    # Для каждого пикселя
                    for x in range(photo.size[0]):
                        for y in range(photo.size[1]):
                            r, g, b, a = photo.getpixel((x, y))
                            # Если пиксель близок к черному или темно-серому, делаем его прозрачным
                            if r < 50 and g < 50 and b < 50:
                                output.putpixel((x, y), (0, 0, 0, 0))
                            else:
                                output.putpixel((x, y), (r, g, b, 255))
                    
                    # Применяем круглую маску
                    output.putalpha(mask)
                    
                    # Вставляем фото с прозрачностью
                    collage.paste(output, position, output)
                    
                    # Добавляем информацию об игроке
                    text_position = (
                        position[0] + photo_size[0]//2,
                        position[1] + photo_size[1] + 10
                    )
                    
                    # Получаем позицию игрока
                    player_pos = player['info']['position']

                    draw.text(
                        text_position,
                        f"{player['info']['name']}\n{player_pos} - {player['stats']['total_points']}",
                        font=font,
                        fill='black',
                        anchor='mm'
                    )
                except Exception as e:
                    logger.error(f"Ошибка при добавлении фото игрока {player_id}: {e}")
                    continue
            
            # Добавляем общие очки
            draw.text(
                (width//2, height - 30),
                f"Общие очки: {total_points}",
                font=font,
                fill='black',
                anchor='mm'
            )
            
            # Сохраняем коллаж с прозрачным фоном
            output_path = os.path.join(
                self.collage_dir,
                f"team_of_day_{date}.png"
            )
            collage.save(output_path, "PNG")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Ошибка при создании коллажа: {e}")
            return None
            
    def _get_photo_positions(self, width: int, height: int) -> List[Tuple[int, int]]:
        """Возвращает позиции для фото игроков"""
        # Размер фото игрока
        photo_size = (130, 100)
        
        # Позиции для 6 игроков (3-2-1)
        # Первый ряд: C, LW, RW
        row1_y = 100
        row1_x = [width//4, width//2, 3*width//4]
        
        # Второй ряд: D, D
        row2_y = 250
        row2_x = [width//3, 2*width//3]
        
        # Третий ряд: G
        row3_y = 400
        row3_x = [width//2]
        
        positions = []
        
        # Добавляем позиции в порядке: C, LW, RW, D, D, G
        positions.extend([(x - photo_size[0]//2, row1_y) for x in row1_x])
        positions.extend([(x - photo_size[0]//2, row2_y) for x in row2_x])
        positions.extend([(x - photo_size[0]//2, row3_y) for x in row3_x])
        
        return positions
        
    def _get_player_photo_url(self, player_id: str) -> Optional[str]:
        """Получает URL фото игрока"""
        return f"https://a.espncdn.com/i/headshots/nhl/players/full/{player_id}.png"
