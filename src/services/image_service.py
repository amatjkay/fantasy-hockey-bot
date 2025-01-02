import logging
import requests
from PIL import Image, ImageDraw, ImageFont
from src.config.fonts import get_system_font
from src.config.settings import GRADE_COLORS, IMAGE_SETTINGS
import os
from io import BytesIO
from datetime import datetime

class ImageService:
    def __init__(self):
        """Инициализация сервиса для работы с изображениями"""
        self.logger = logging.getLogger(__name__)
        
        # Создаем директории для кэша и временных файлов
        os.makedirs("data/cache/player_images", exist_ok=True)
        os.makedirs("data/temp", exist_ok=True)
        
        # Загружаем шрифты
        try:
            self.font = ImageFont.truetype("data/fonts/Roboto-Bold.ttf", 24)
            self.stats_font = ImageFont.truetype("data/fonts/Roboto-Regular.ttf", 20)
        except Exception as e:
            self.logger.error(f"Ошибка загрузки шрифтов: {e}")
            # Используем дефолтный шрифт если не удалось загрузить Roboto
            self.font = ImageFont.load_default()
            self.stats_font = ImageFont.load_default()

    def create_team_collage(self, team, output_path, date=None):
        """Создает коллаж из изображений игроков
        
        Args:
            team (list): Список игроков
            output_path (str): Путь для сохранения коллажа
            date (datetime): Дата, за которую отображается команда
            
        Returns:
            bool: True если коллаж успешно создан, False в случае ошибки
        """
        try:
            # Загружаем шрифты
            font = get_system_font(24)
            title_font = get_system_font(32)
            
            # Рассчитываем размеры элементов
            title_height = 80  # Увеличиваем высоту для заголовка
            player_image_height = 120
            player_text_height = 30  # Уменьшаем высоту, так как убрали текст грейда
            padding = 15
            
            # Рассчитываем общую высоту контента
            total_content_height = (
                title_height +  # Заголовок
                (player_image_height + player_text_height + padding) * len(team) +  # Игроки
                padding * 2  # Отступы сверху и снизу
            )
            
            # Создаем белый фон
            collage = Image.new('RGB', (800, total_content_height), 'white')
            draw = ImageDraw.Draw(collage)
            
            # Добавляем дату в заголовок
            display_date = date.strftime("%d.%m.%Y") if date else datetime.now().strftime("%d.%m.%Y")
            title_text = f"Команда дня {display_date}"
            text_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = (800 - text_width) // 2
            text_y = padding
            draw.text((text_x, text_y), title_text, font=title_font, fill='black')
            
            # Добавляем игроков
            y_offset = title_height
            
            # Сначала добавляем вратаря (если есть)
            goalie = next((player for player in team if player.get('position') == 'G'), None)
            if goalie:
                team.remove(goalie)
                team.append(goalie)
            
            for player in team:
                try:
                    player_id = str(player.get('id', ''))
                    player_name = player.get('name', 'Unknown Player')
                    player_position = player.get('position', 'Unknown')
                    player_grade = player.get('grade', 'common').lower()
                    
                    # Получаем изображение игрока
                    player_image = self._get_player_image(player_id, player_name)
                    if player_image:
                        # Масштабируем изображение
                        player_image = player_image.resize((150, player_image_height), Image.Resampling.LANCZOS)
                        
                        # Центрируем изображение
                        x = (800 - 150) // 2
                        
                        # Добавляем изображение на белый фон
                        collage.paste(player_image, (x, y_offset))
                        
                        # Добавляем текст с позицией и именем игрока
                        text = f"{player_position}: {player_name}"
                        
                        # Проверяем длину текста
                        text_bbox = draw.textbbox((0, 0), text, font=font)
                        text_width = text_bbox[2] - text_bbox[0]
                        
                        # Если текст слишком длинный, уменьшаем шрифт
                        current_font = font
                        if text_width > 700:
                            current_font = get_system_font(20)
                            text_bbox = draw.textbbox((0, 0), text, font=current_font)
                            text_width = text_bbox[2] - text_bbox[0]
                        
                        # Центрируем текст
                        text_x = (800 - text_width) // 2
                        text_y = y_offset + player_image_height + 5
                        
                        # Определяем цвет текста на основе грейда
                        text_color = GRADE_COLORS.get(player_grade, 'black')
                        draw.text((text_x, text_y), text, font=current_font, fill=text_color)
                        
                        # Увеличиваем смещение для следующего игрока
                        y_offset += player_image_height + player_text_height + padding
                        
                        self.logger.info(f"Добавлен игрок: {player_name}")
                    else:
                        self.logger.warning(f"Не удалось получить изображение для игрока {player_name}")
                
                except Exception as e:
                    self.logger.error(f"Ошибка при добавлении игрока {player.get('name', 'Unknown')}: {e}")
                    continue
            
            # Сохраняем коллаж
            collage.save(output_path)
            self.logger.info(f"Коллаж успешно создан и сохранен в {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при создании коллажа: {e}")
            return False

    def create_week_collage(self, team, week_key, output_path):
        """Создает коллаж команды недели
        
        Args:
            team (dict): Словарь с игроками по позициям
            week_key (str): Ключ недели в формате YYYY-MM-DD_YYYY-MM-DD
            output_path (str): Путь для сохранения коллажа
            
        Returns:
            str: Путь к созданному коллажу или None в случае ошибки
        """
        try:
            # Загружаем шрифты
            font = get_system_font(24)
            title_font = get_system_font(32)
            
            # Рассчитываем размеры элементов
            title_height = 80
            player_image_height = 120
            player_text_height = 30
            padding = 15
            
            # Подсчитываем общее количество игроков
            total_players = sum(len(players) for players in team.values())
            
            # Рассчитываем общую высоту контента
            total_content_height = (
                title_height +  # Заголовок
                (player_image_height + player_text_height + padding) * total_players +  # Игроки
                padding * 2  # Отступы сверху и снизу
            )
            
            # Создаем белый фон с фиксированной шириной
            width = 800
            collage = Image.new('RGB', (width, total_content_height), 'white')
            draw = ImageDraw.Draw(collage)
            
            # Добавляем заголовок
            start_date, end_date = week_key.split('_')
            title_text = f"Команда недели {start_date} - {end_date}"
            text_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = (width - text_width) // 2
            text_y = padding
            draw.text((text_x, text_y), title_text, font=title_font, fill='black')
            
            # Добавляем игроков
            y_offset = title_height
            
            # Порядок позиций: C, LW, RW, D, D, G
            positions = ['C', 'LW', 'RW', 'D', 'G']
            
            # Обработка центральных нападающих
            for player in team.get('C', []):
                self._add_player_to_collage(player, 'C', collage, draw, font, width, y_offset, player_image_height, player_text_height, padding)
                y_offset += player_image_height + player_text_height + padding
            
            # Обработка левых нападающих
            for player in team.get('LW', []):
                self._add_player_to_collage(player, 'LW', collage, draw, font, width, y_offset, player_image_height, player_text_height, padding)
                y_offset += player_image_height + player_text_height + padding
            
            # Обработка правых нападающих
            for player in team.get('RW', []):
                self._add_player_to_collage(player, 'RW', collage, draw, font, width, y_offset, player_image_height, player_text_height, padding)
                y_offset += player_image_height + player_text_height + padding
            
            # Обработка защитников (должно быть два)
            defenders = team.get('D', [])
            for player in defenders:
                self._add_player_to_collage(player, 'D', collage, draw, font, width, y_offset, player_image_height, player_text_height, padding)
                y_offset += player_image_height + player_text_height + padding
            
            # Обработка вратаря (должен быть последним)
            goalies = team.get('G', [])
            if goalies:
                self._add_player_to_collage(goalies[0], 'G', collage, draw, font, width, y_offset, player_image_height, player_text_height, padding)
            
            # Сохраняем коллаж
            collage.save(output_path)
            self.logger.info(f"Коллаж успешно создан и сохранен в {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Ошибка при создании коллажа: {e}")
            return None

    def _add_player_to_collage(self, player, position, collage, draw, font, width, y_offset, player_image_height, player_text_height, padding):
        """Добавляет игрока в коллаж
        
        Args:
            player (dict): Информация об игроке
            position (str): Позиция игрока
            collage (Image): Объект коллажа
            draw (ImageDraw): Объект для рисования
            font (ImageFont): Шрифт для текста
            width (int): Ширина коллажа
            y_offset (int): Текущее смещение по вертикали
            player_image_height (int): Высота изображения игрока
            player_text_height (int): Высота текста
            padding (int): Отступ
        """
        try:
            player_id = str(player.get('id', ''))
            player_name = player.get('name', 'Unknown Player')
            player_grade = player.get('grade', 'common').lower()
            
            # Получаем изображение игрока
            player_image = self._get_player_image(player_id, player_name)
            if player_image:
                # Масштабируем изображение
                player_image = player_image.resize((150, player_image_height), Image.Resampling.LANCZOS)
                
                # Центрируем изображение
                x = (width - 150) // 2
                
                # Добавляем изображение на белый фон
                collage.paste(player_image, (x, y_offset))
                
                # Добавляем текст с позицией и именем игрока
                text = f"{position}: {player_name}"
                
                # Проверяем длину текста
                text_bbox = draw.textbbox((0, 0), text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                
                # Если текст слишком длинный, уменьшаем шрифт
                current_font = font
                if text_width > 700:
                    current_font = get_system_font(20)
                    text_bbox = draw.textbbox((0, 0), text, font=current_font)
                    text_width = text_bbox[2] - text_bbox[0]
                
                # Центрируем текст
                text_x = (width - text_width) // 2
                text_y = y_offset + player_image_height + 5
                
                # Определяем цвет текста на основе грейда
                text_color = GRADE_COLORS.get(player_grade, 'black')
                draw.text((text_x, text_y), text, font=current_font, fill=text_color)
                
                self.logger.info(f"Добавлен игрок: {player_name}")
            else:
                self.logger.warning(f"Не удалось получить изображение для игрока {player_name}")
        
        except Exception as e:
            self.logger.error(f"Ошибка при добавлении игрока {player.get('name', 'Unknown')}: {e}")

    def _get_player_image(self, player_id, player_name):
        """Получает изображение игрока
        
        Args:
            player_id (str): ID игрока
            player_name (str): Имя игрока
            
        Returns:
            Image: Объект изображения или None в случае ошибки
        """
        try:
            # Проверяем наличие изображения в кэше
            cache_path = f"data/cache/player_images/{player_id}.jpg"
            if os.path.exists(cache_path):
                img = Image.open(cache_path)
                # Конвертируем в RGBA для обработки прозрачности
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                return self._process_transparency(img)
            
            # Если изображения нет в кэше, загружаем его
            url = f"https://a.espncdn.com/i/headshots/nhl/players/full/{player_id}.png"
            response = requests.get(url)
            
            if response.status_code == 200:
                # Открываем изображение из байтов
                img = Image.open(BytesIO(response.content))
                # Конвертируем в RGBA для обработки прозрачности
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                # Обрабатываем прозрачность
                img = self._process_transparency(img)
                # Сохраняем в кэш
                img.save(cache_path, 'JPEG', quality=95)
                return img
            else:
                self.logger.error(f"Не удалось загрузить изображение для игрока {player_name}")
                return None
                
        except Exception as e:
            self.logger.error(f"Ошибка при получении изображения игрока {player_name}: {e}")
            return None

    def _process_transparency(self, img):
        """Обрабатывает прозрачность изображения
        
        Args:
            img (Image): Исходное изображение
            
        Returns:
            Image: Обработанное изображение с белым фоном
        """
        # Создаем новое изображение с белым фоном
        background = Image.new('RGBA', img.size, (255, 255, 255, 255))
        # Накладываем исходное изображение на белый фон
        return Image.alpha_composite(background, img).convert('RGB')
