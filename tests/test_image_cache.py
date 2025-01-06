import pytest
import os
from PIL import Image
import requests
from unittest.mock import patch, MagicMock
from src.services.image_service import ImageService

@pytest.fixture
def image_service():
    return ImageService()

@pytest.fixture
def sample_image(tmp_path):
    """Создает тестовое изображение"""
    image_path = tmp_path / "test.png"
    image = Image.new('RGB', (130, 100), color='white')
    image.save(image_path, 'PNG')
    return image_path

def test_image_download(image_service, tmp_path):
    """Тест загрузки изображения"""
    player_id = "1234"
    
    # Мокаем запрос к API
    with patch('requests.get') as mock_get:
        # Создаем фейковый ответ с изображением
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = Image.new('RGB', (130, 100), color='white').tobytes()
        mock_get.return_value = mock_response
        
        # Загружаем изображение
        image_path = image_service._download_player_image(player_id)
        
        # Проверяем, что файл создан
        assert os.path.exists(image_path)
        
        # Проверяем формат и размер
        with Image.open(image_path) as img:
            assert img.format == 'PNG'
            assert img.size == (130, 100)

def test_image_cache(image_service, sample_image):
    """Тест кеширования изображений"""
    player_id = "1234"
    
    # Первая загрузка
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        with open(sample_image, 'rb') as f:
            mock_response.content = f.read()
        mock_get.return_value = mock_response
        
        path1 = image_service._download_player_image(player_id)
    
    # Вторая загрузка (должна использовать кеш)
    with patch('requests.get') as mock_get:
        path2 = image_service._download_player_image(player_id)
        
        # Проверяем, что второй запрос не был выполнен
        mock_get.assert_not_called()
        
        # Проверяем, что пути одинаковые
        assert path1 == path2

def test_image_format_conversion(image_service, tmp_path):
    """Тест конвертации форматов изображений"""
    # Создаем тестовое JPEG изображение
    jpeg_path = tmp_path / "test.jpg"
    image = Image.new('RGB', (130, 100), color='white')
    image.save(jpeg_path, 'JPEG')
    
    player_id = "1234"
    
    # Мокаем загрузку JPEG
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        with open(jpeg_path, 'rb') as f:
            mock_response.content = f.read()
        mock_get.return_value = mock_response
        
        # Загружаем изображение
        image_path = image_service._download_player_image(player_id)
        
        # Проверяем, что изображение сохранено в PNG
        with Image.open(image_path) as img:
            assert img.format == 'PNG'
            assert img.mode == 'RGBA'  # Проверяем наличие альфа-канала

def test_image_resize(image_service, tmp_path):
    """Тест изменения размера изображения"""
    # Создаем большое тестовое изображение
    large_image_path = tmp_path / "large.png"
    image = Image.new('RGB', (260, 200), color='white')
    image.save(large_image_path, 'PNG')
    
    player_id = "1234"
    
    # Мокаем загрузку большого изображения
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        with open(large_image_path, 'rb') as f:
            mock_response.content = f.read()
        mock_get.return_value = mock_response
        
        # Загружаем изображение
        image_path = image_service._download_player_image(player_id)
        
        # Проверяем, что размер изменен до стандартного
        with Image.open(image_path) as img:
            assert img.size == (130, 100)

def test_image_quality(image_service, sample_image):
    """Тест качества изображения"""
    player_id = "1234"
    
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        with open(sample_image, 'rb') as f:
            mock_response.content = f.read()
        mock_get.return_value = mock_response
        
        # Загружаем изображение
        image_path = image_service._download_player_image(player_id)
        
        # Проверяем размер файла (не должен быть слишком большим)
        file_size = os.path.getsize(image_path)
        assert file_size < 50000  # Максимальный размер 50KB
        
        # Проверяем качество изображения
        with Image.open(image_path) as img:
            # Проверяем, что изображение не размыто
            assert img.size == (130, 100)
            # Проверяем глубину цвета
            assert img.mode in ['RGB', 'RGBA'] 