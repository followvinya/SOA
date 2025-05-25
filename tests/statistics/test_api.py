import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from statistics_api.main import app
from statistics_api import schemas


class TestStatisticsAPI:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def mock_grpc_stub(self):
        with patch('statistics_api.main.statistics_pb2_grpc.StatisticsServiceStub') as mock:
            yield mock

    def test_get_post_statistics(self, client, mock_grpc_stub):
        """Тест получения статистики поста"""
        # Настраиваем мок
        mock_response = Mock()
        mock_response.post_id = 1
        mock_response.views_count = 100
        mock_response.likes_count = 50
        mock_response.comments_count = 25

        mock_stub_instance = Mock()
        mock_stub_instance.GetPostStats.return_value = mock_response
        mock_grpc_stub.return_value = mock_stub_instance

        # Делаем запрос
        response = client.get("/statistics/posts/1")

        # Проверяем результат
        assert response.status_code == 200
        data = response.json()
        assert data["post_id"] == 1
        assert data["views_count"] == 100
        assert data["likes_count"] == 50
        assert data["comments_count"] == 25

    def test_get_post_dynamics(self, client, mock_grpc_stub):
        """Тест получения динамики"""
        # Настраиваем мок
        mock_stat1 = Mock()
        mock_stat1.date = "2024-01-01"
        mock_stat1.count = 10

        mock_stat2 = Mock()
        mock_stat2.date = "2024-01-02"
        mock_stat2.count = 15

        mock_response = Mock()
        mock_response.daily_stats = [mock_stat1, mock_stat2]

        mock_stub_instance = Mock()
        mock_stub_instance.GetPostViewsDynamics.return_value = mock_response
        mock_grpc_stub.return_value = mock_stub_instance

        # Делаем запрос
        response = client.get("/statistics/posts/1/views/dynamics")

        # Проверяем результат
        assert response.status_code == 200
        data = response.json()
        assert len(data["daily_stats"]) == 2
        assert data["daily_stats"][0]["date"] == "2024-01-01"
        assert data["daily_stats"][0]["count"] == 10

    def test_get_top_posts(self, client, mock_grpc_stub):
        """Тест получения топ постов"""
        # Настраиваем мок
        mock_post1 = Mock()
        mock_post1.post_id = 1
        mock_post1.count = 100

        mock_post2 = Mock()
        mock_post2.post_id = 2
        mock_post2.count = 90

        mock_response = Mock()
        mock_response.posts = [mock_post1, mock_post2]

        mock_stub_instance = Mock()
        mock_stub_instance.GetTopPosts.return_value = mock_response
        mock_grpc_stub.return_value = mock_stub_instance

        # Делаем запрос
        response = client.get("/statistics/posts/top?metric=views")

        # Проверяем результат
        assert response.status_code == 200
        data = response.json()
        assert len(data["posts"]) == 2
        assert data["posts"][0]["post_id"] == 1
        assert data["posts"][0]["count"] == 100

    def test_get_top_users(self, client, mock_grpc_stub):
        """Тест получения топ пользователей"""
        # Настраиваем мок
        mock_user1 = Mock()
        mock_user1.user_id = 10
        mock_user1.count = 50

        mock_response = Mock()
        mock_response.users = [mock_user1]

        mock_stub_instance = Mock()
        mock_stub_instance.GetTopUsers.return_value = mock_response
        mock_grpc_stub.return_value = mock_stub_instance

        # Делаем запрос
        response = client.get("/statistics/users/top?metric=likes")

        # Проверяем результат
        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 1
        assert data["users"][0]["user_id"] == 10
        assert data["users"][0]["count"] == 50

    def test_invalid_metric(self, client):
        """Тест с невалидной метрикой"""
        response = client.get("/statistics/posts/top?metric=invalid")
        assert response.status_code == 422  # Unprocessable Entity

    def test_missing_metric(self, client):
        """Тест без метрики"""
        response = client.get("/statistics/posts/top")
        assert response.status_code == 422  # Unprocessable Entity