import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from system_api.main import app
from datetime import datetime

client = TestClient(app)


class TestSystemAPI:

    @patch('system_api.main.utils.make_request')
    def test_register_user(self, mock_make_request):
        """Тест регистрации пользователя"""
        # Мокаем полный ответ с датами
        mock_make_request.return_value = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "first_name": None,
            "last_name": None,
            "birth_date": None,
            "phone_number": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        response = client.post("/users", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass123"
        })

        assert response.status_code == 201
        assert response.json()["username"] == "testuser"
        assert response.json()["email"] == "test@example.com"

    @patch('system_api.main.post_service')
    @patch('system_api.main.utils.make_request')
    def test_create_post(self, mock_make_request, mock_post_service):
        """Тест создания поста"""
        # Мокаем получение user_id из токена
        mock_make_request.return_value = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "first_name": None,
            "last_name": None,
            "birth_date": None,
            "phone_number": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        # Мокаем создание поста
        mock_post_service.create_post.return_value = {
            "id": 1,
            "title": "Test Post",
            "description": "Test Description",
            "creator_id": 1,
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00",
            "is_private": False,
            "tags": ["test"]
        }

        response = client.post(
            "/posts",
            json={
                "title": "Test Post",
                "description": "Test Description",
                "is_private": False,
                "tags": ["test"]
            },
            headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 201
        assert response.json()["title"] == "Test Post"

    @patch('system_api.main.post_service')
    @patch('system_api.main.utils.make_request')
    def test_like_post(self, mock_make_request, mock_post_service):
        """Тест лайка поста"""
        # Мокаем получение user_id
        mock_make_request.return_value = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "first_name": None,
            "last_name": None,
            "birth_date": None,
            "phone_number": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        # Мокаем лайк
        mock_post_service.like_post.return_value = {
            "success": True,
            "like_id": 1
        }

        response = client.post(
            "/posts/1/like",
            headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 200
        assert response.json()["success"] == True
        assert response.json()["like_id"] == 1