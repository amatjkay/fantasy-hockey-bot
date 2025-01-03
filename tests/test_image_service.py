import os
import json
import pytest
import requests
from datetime import datetime
from unittest.mock import patch, Mock
from PIL import Image
from io import BytesIO

from src.services.image_service import ImageService

@pytest.fixture
def image_service():
    return ImageService()

@pytest.fixture
def test_team_data():
    return {
        'C': [{
            'id': '12345',
            'fullName': 'Test Player',
            'grade': 'A+'
        }]
    }

@pytest.fixture
def mock_image():
    # Создаем тестовое изображение
    img = Image.new('RGB', (100, 100), color='white')
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

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
        str(output_path)
    )

    assert result_path is not None
    assert os.path.exists(result_path)

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
    image_service.cache_dir = str(cache_dir)

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
        str(output_path)
    )

    # Проверяем, что файл был закэширован
    assert os.path.exists(cache_file)

    # Проверяем, что при повторном запросе используется кэш
    mock_get.reset_mock()
    image_service.create_week_collage(
        test_team_data,
        "2024-01-01_2024-01-07",
        str(output_path)
    )
    mock_get.assert_not_called() 