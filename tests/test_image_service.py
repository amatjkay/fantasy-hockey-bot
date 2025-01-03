import pytest
from PIL import Image
import os
from src.services.image_service import ImageService
from pathlib import Path
from unittest.mock import patch
from io import BytesIO
import requests

@pytest.fixture
def image_service():
    return ImageService()

@pytest.fixture
def test_team_data():
    return {
        "C": [{
            "name": "Test Player",
            "id": "12345",
            "grade": "A+"
        }]
    }

@pytest.fixture
def mock_image():
    # Создаем тестовое изображение
    img = Image.new('RGB', (130, 100), color='white')
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def test_image_service_initialization(image_service):
    assert image_service is not None
    assert image_service.player_img_width > 0
    assert image_service.player_img_height > 0

@patch('requests.get')
def test_create_week_collage(mock_get, image_service, test_team_data, tmp_path, mock_image):
    # Настраиваем мок для requests.get
    mock_response = requests.Response()
    mock_response.raw = mock_image
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    output_path = tmp_path / "test_collage.jpg"
    result_path = image_service.create_week_collage(
        test_team_data,
        "2024-01-01_2024-01-07",
        output_path
    )
    
    assert os.path.exists(result_path)
    with Image.open(result_path) as img:
        assert img.size[0] == image_service.width
        assert img.size[1] > 0

@patch('requests.get')
def test_player_image_caching(mock_get, image_service, test_team_data, tmp_path, mock_image):
    # Создаем временную директорию для кэша
    cache_dir = tmp_path / "cache/player_images"
    os.makedirs(cache_dir, exist_ok=True)

    # Настраиваем мок для requests.get
    mock_response = requests.Response()
    mock_response.raw = mock_image
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    # Устанавливаем путь к кэшу в сервисе
    image_service.cache_dir = cache_dir

    # Проверяем, что изображения кэшируются
    player_id = test_team_data["C"][0]["id"]
    cache_file = os.path.join(cache_dir, f"{player_id}.jpg")

    # Удаляем кэш если существует
    if os.path.exists(cache_file):
        os.remove(cache_file)

    output_path = tmp_path / "test_collage.jpg"
    image_service.create_week_collage(
        test_team_data,
        "2024-01-01_2024-01-07",
        output_path
    )

    assert os.path.exists(cache_file)
    
    # Проверяем, что второй запрос использует кэш
    mock_get.reset_mock()
    image_service.create_week_collage(
        test_team_data,
        "2024-01-01_2024-01-07",
        output_path
    )
    
    assert mock_get.call_count == 0  # Запрос не должен быть выполнен 