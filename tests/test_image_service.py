import pytest
import os
from PIL import Image
import requests
from src.services.image_service import ImageService
from src.config import settings
from .fixtures.test_data import TEST_TEAM_OF_DAY

@pytest.fixture
def image_service():
    return ImageService()

def test_image_service_initialization(image_service):
    """Тест инициализации сервиса"""
    assert os.path.exists(image_service.cache_dir)
    assert os.path.exists(image_service.collage_dir)

def test_get_player_photo_caching(image_service, mocker):
    """Тест кэширования фото игроков"""
    player_id = "test123"
    player_name = "Test Player"
    cache_path = os.path.join(image_service.cache_dir, f"{player_id}.png")
    
    # Создаем тестовое фото в кэше
    with open(cache_path, 'wb') as f:
        f.write(b'test')
        
    # Проверяем что фото берется из кэша
    photo_path = image_service.get_player_photo(player_id, player_name)
    assert photo_path == cache_path
    
    # Очищаем после теста
    os.remove(cache_path)

@pytest.mark.vcr()
def test_get_player_photo_download(image_service, mocker):
    """Тест загрузки фото игроков"""
    player_id = "test123"
    player_name = "Test Player"
    
    # Мокаем запрос к API
    mock_response = mocker.Mock()
    mock_response.content = b'test'
    mock_response.status_code = 200
    mocker.patch.object(requests, 'get', return_value=mock_response)
    
    photo_path = image_service.get_player_photo(player_id, player_name)
    assert photo_path is not None
    assert os.path.exists(photo_path)
    
    # Очищаем после теста
    os.remove(photo_path)

def test_get_photo_positions(image_service):
    """Тест получения позиций для фото"""
    width = 800
    height = 600
    positions = image_service._get_photo_positions(width, height)
    
    assert len(positions) == 6  # 6 игроков
    assert all(isinstance(pos, tuple) and len(pos) == 2 for pos in positions)
    assert all(0 <= x <= width and 0 <= y <= height for x, y in positions)

@pytest.mark.vcr()
def test_create_collage(image_service):
    """Тест создания коллажа"""
    # Создаем тестовые фото
    player_photos = {}
    for player_id in TEST_TEAM_OF_DAY["players"]:
        photo_path = os.path.join(image_service.cache_dir, f"{player_id}.png")
        # Создаем тестовое изображение
        img = Image.new('RGB', (130, 100), color='white')
        img.save(photo_path)
        player_photos[player_id] = photo_path
        
    # Создаем коллаж
    collage_path = image_service.create_collage(
        player_photos,
        TEST_TEAM_OF_DAY["players"],
        TEST_TEAM_OF_DAY["date"],
        TEST_TEAM_OF_DAY["total_points"]
    )
    
    assert collage_path is not None
    assert os.path.exists(collage_path)
    
    # Проверяем размеры коллажа
    with Image.open(collage_path) as img:
        assert img.size == (800, 600)
        
    # Очищаем после теста
    for photo_path in player_photos.values():
        os.remove(photo_path)
    os.remove(collage_path)

def test_photo_url_generation(image_service):
    """Тест генерации URL для фото"""
    player_id = "123456"
    url = image_service._get_player_photo_url(player_id)
    assert url == f"https://a.espncdn.com/i/headshots/nhl/players/full/{player_id}.png"

@pytest.mark.vcr()
def test_error_handling(image_service, mocker):
    """Тест обработки ошибок"""
    player_id = "test123"
    player_name = "Test Player"
    
    # Мокаем ошибку сети
    mocker.patch.object(requests, 'get', side_effect=requests.RequestException)
    
    photo_path = image_service.get_player_photo(player_id, player_name)
    assert photo_path is None 