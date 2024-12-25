import os
import platform
import logging
from PIL import ImageFont

# Пути к шрифтам для разных ОС
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

def get_system_font(size=20):
    """Получение системного шрифта в зависимости от ОС
    
    Args:
        size (int): Размер шрифта
        
    Returns:
        PIL.ImageFont: Объект шрифта
    """
    system = platform.system()
    font_paths = FONT_PATHS.get(system, [])
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, size=size)
                logging.info(f"Используется шрифт: {font_path}")
                return font
            except Exception as e:
                logging.warning(f"Не удалось загрузить шрифт {font_path}: {e}")
    
    logging.warning("Используется дефолтный шрифт, так как не найдены системные шрифты")
    return ImageFont.load_default()
