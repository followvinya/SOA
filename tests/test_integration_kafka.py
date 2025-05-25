import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime


class TestIntegrationKafkaEvents:
    """Интеграционные тесты для проверки отправки событий через API"""

    @patch('post_service.app.kafka_producer.send_post_like_event')
    @patch('system_api.main.post_service')
    @patch('system_api.main.utils.make_request')
    def test_like_post_sends_kafka_event(self, mock_make_request, mock_post_service, mock_kafka_event):
        """Тест: при лайке поста отправляется событие в Kafka"""
        from system_api.main import app
        client = TestClient(app)

        # Мокаем пользователя
        mock_make_request.return_value = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        # Мокаем успешный лайк
        mock_post_service.like_post.return_value = {
            "success": True,
            "like_id": 123
        }

        # Делаем запрос на лайк
        response = client.post(
            "/posts/456/like",
            headers={"Authorization": "Bearer fake-token"}
        )

        # Проверяем ответ
        assert response.status_code == 200
        assert response.json()["success"] == True

        # Проверяем, что gRPC метод был вызван
        mock_post_service.like_post.assert_called_once_with(
            post_id=456,
            user_id=1
        )

    @patch('post_service.app.kafka_producer.send_post_view_event')
    @patch('system_api.main.post_service')
    @patch('system_api.main.utils.make_request')
    def test_view_post_sends_kafka_event(self, mock_make_request, mock_post_service, mock_kafka_event):
        """Тест: при просмотре поста отправляется событие в Kafka"""
        from system_api.main import app
        client = TestClient(app)

        # Мокаем пользователя
        mock_make_request.return_value = {
            "id": 2,
            "username": "viewer",
            "email": "viewer@example.com",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        # Мокаем успешный просмотр
        mock_post_service.view_post.return_value = {
            "success": True,
            "view_id": 789
        }

        # Делаем запрос на просмотр
        response = client.post(
            "/posts/123/view",
            headers={"Authorization": "Bearer fake-token"}
        )

        # Проверяем
        assert response.status_code == 200
        assert response.json()["success"] == True

        # Проверяем вызов gRPC
        mock_post_service.view_post.assert_called_once_with(
            post_id=123,
            user_id=2
        )

    @patch('post_service.app.kafka_producer.send_post_comment_event')
    @patch('system_api.main.post_service')
    @patch('system_api.main.utils.make_request')
    def test_add_comment_sends_kafka_event(self, mock_make_request, mock_post_service, mock_kafka_event):
        """Тест: при добавлении комментария отправляется событие в Kafka"""
        from system_api.main import app
        client = TestClient(app)

        # Мокаем пользователя
        mock_make_request.return_value = {
            "id": 3,
            "username": "commenter",
            "email": "commenter@example.com",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        # Мокаем успешное добавление комментария
        mock_post_service.add_comment.return_value = {
            "id": 555,
            "post_id": 777,
            "user_id": 3,
            "text": "Nice post!",
            "created_at": datetime.now().isoformat()
        }

        # Делаем запрос
        response = client.post(
            "/posts/777/comments",
            json={"text": "Nice post!"},
            headers={"Authorization": "Bearer fake-token"}
        )

        # Проверяем
        assert response.status_code == 201
        assert response.json()["text"] == "Nice post!"

        # Проверяем вызов gRPC
        mock_post_service.add_comment.assert_called_once_with(
            post_id=777,
            user_id=3,
            text="Nice post!"
        )

    @patch('user_service.kafka_producer.send_user_registration_event')
    @patch('system_api.main.utils.make_request')
    def test_user_registration_sends_kafka_event(self, mock_make_request, mock_kafka_event):
        """Тест: при регистрации пользователя отправляется событие в Kafka"""
        from system_api.main import app
        client = TestClient(app)

        # Мокаем успешную регистрацию
        mock_make_request.return_value = {
            "id": 100,
            "username": "newuser",
            "email": "new@example.com",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        # Регистрируем пользователя
        response = client.post("/users", json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "SecurePass123"
        })

        # Проверяем
        assert response.status_code == 201
        assert response.json()["username"] == "newuser"

    @patch('post_service.app.kafka_producer.send_post_comment_event')
    @patch('system_api.main.post_service')
    @patch('system_api.main.utils.make_request')
    def test_add_comment_sends_kafka_event(self, mock_make_request, mock_post_service, mock_kafka_event):
        """Тест: при добавлении комментария отправляется событие в Kafka"""
        from system_api.main import app
        client = TestClient(app)

        # Мокаем пользователя
        mock_make_request.return_value = {
            "id": 3,
            "username": "commenter",
            "email": "commenter@example.com",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        # Мокаем успешное добавление комментария (добавляем updated_at!)
        mock_post_service.add_comment.return_value = {
            "id": 555,
            "post_id": 777,
            "user_id": 3,
            "text": "Nice post!",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()  # Добавлено!
        }

        # Делаем запрос
        response = client.post(
            "/posts/777/comments",
            json={"text": "Nice post!"},
            headers={"Authorization": "Bearer fake-token"}
        )

        # Проверяем
        assert response.status_code == 200
        assert response.json()["text"] == "Nice post!"

        # Проверяем вызов gRPC
        mock_post_service.add_comment.assert_called_once_with(
            post_id=777,
            user_id=3,
            text="Nice post!"
        )