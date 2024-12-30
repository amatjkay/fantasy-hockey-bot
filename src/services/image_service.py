import logging
import requests
from PIL import Image, ImageDraw
from src.config.fonts import get_system_font
from src.config.settings import GRADE_COLORS, IMAGE_SETTINGS
import os

class ImageService:
    def __init__(self):
        self.player_img_width = IMAGE_SETTINGS['PLAYER']['WIDTH']
        self.player_img_height = IMAGE_SETTINGS['PLAYER']['HEIGHT']
        self.padding = IMAGE_SETTINGS['PADDING']
        self.text_padding = IMAGE_SETTINGS['TEXT_PADDING']
        self.line_height = self.player_img_height + self.text_padding + 30 + self.padding
        self.width = IMAGE_SETTINGS['COLLAGE_WIDTH']
        self.font = get_system_font()

    def create_week_collage(self, team, week_key, output_path):
        """Создание коллажа команды недели
        
        Args:
            team (dict): Словарь с игроками по позициям
            week_key (str): Ключ недели в формате 'YYYY-MM-DD_YYYY-MM-DD'
            output_path (Path): Путь для сохранения коллажа
            
        Returns:
            Path: Путь к созданному файлу коллажа
        """
        total_players = sum(len(players) for players in team.values())
        height = total_players * self.line_height + self.padding * 2

        image = Image.new("RGB", (self.width, height), "white")
        draw = ImageDraw.Draw(image)

        y_offset = self.padding
        
        # Заголовок
        start_date, end_date = week_key.split('_')
        title = f"Команда недели ({start_date} - {end_date})"
        try:
            title_width = draw.textlength(title, font=self.font)
        except AttributeError:
            title_width = self.font.getlength(title)
        draw.text(((self.width - title_width) // 2, y_offset), title, fill="black", font=self.font)
        y_offset += 40

        # Добавляем игроков по позициям
        for position, players in team.items():
            for player in players:
                y_offset = self._add_player_to_collage(
                    draw, image, player, position, y_offset
                )

        # Сохраняем коллаж
        image.save(str(output_path))
        logging.info(f"Коллаж сохранен: {output_path}")
        return output_path

    def _add_player_to_collage(self, draw, image, player, position, y_offset):
        """Добавление игрока в коллаж
        
        Args:
            draw (ImageDraw): Объект для рисования
            image (Image): Изображение коллажа
            player (dict): Информация об игроке
            position (str): Позиция игрока
            y_offset (int): Текущее смещение по вертикали
            
        Returns:
            int: Новое смещение по вертикали
        """
        name = player['name']
        grade = player['grade']
        color = GRADE_COLORS.get(grade, "black")
        cache_dir = "data/cache/player_images"

        # Проверяем кэш
        player_id = player['id']
        cache_file = os.path.join(cache_dir, f"{player_id}.jpg")
        
        if os.path.exists(cache_file):
            try:
                player_image = Image.open(cache_file).convert("RGB")
                logging.info(f"Изображение для {name} загружено из кэша")
            except Exception as e:
                logging.warning(f"Ошибка загрузки из кэша для {name}: {e}")
                os.remove(cache_file)  # Удаляем поврежденный файл
                player_image = None
        else:
            player_image = None

        if player_image is None:
            try:
                image_url = f"https://a.espncdn.com/combiner/i?img=/i/headshots/nhl/players/full/{player_id}.png&w=130&h=100"
                response = requests.get(image_url, stream=True, timeout=10)
                response.raise_for_status()
                player_image = Image.open(response.raw).convert("RGBA")
                bg = Image.new("RGBA", player_image.size, (255, 255, 255, 255))
                combined_image = Image.alpha_composite(bg, player_image)
                player_image = combined_image.convert("RGB")
                
                # Сохраняем в кэш
                os.makedirs(cache_dir, exist_ok=True)
                player_image.save(cache_file)
                logging.info(f"Изображение для {name} успешно загружено и сохранено в кэш")
            except Exception as e:
                logging.warning(f"Ошибка загрузки изображения для {name}: {e}")
                player_image = Image.new("RGB", (self.player_img_width, self.player_img_height), "gray")

        # Изменяем размер изображения
        player_image = player_image.resize(
            (self.player_img_width, self.player_img_height), 
            Image.LANCZOS
        )
        image_x = (self.width - self.player_img_width) // 2
        image.paste(player_image, (image_x, y_offset))

        # Формируем текст без total_points
        text = f"{position}: {name}"
        try:
            text_width = draw.textlength(text, font=self.font)
        except AttributeError:
            text_width = self.font.getlength(text)
        text_x = (self.width - text_width) // 2
        draw.text(
            (text_x, y_offset + self.player_img_height + self.text_padding),
            text,
            fill=color,
            font=self.font
        )
        
        return y_offset + self.line_height
