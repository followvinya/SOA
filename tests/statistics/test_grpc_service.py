import pytest
from unittest.mock import Mock, MagicMock
import grpc
from statistics_service.app.service import StatisticsServicer
from statistics_service.generated import statistics_pb2


class TestStatisticsServicer:
    @pytest.fixture
    def mock_clickhouse_client(self):
        mock = Mock()
        return mock

    @pytest.fixture
    def servicer(self, mock_clickhouse_client):
        return StatisticsServicer(mock_clickhouse_client)

    @pytest.fixture
    def mock_context(self):
        context = Mock()
        context.set_code = Mock()
        context.set_details = Mock()
        return context

    def test_get_post_stats(self, servicer, mock_clickhouse_client, mock_context):
        """Тест получения статистики поста"""
        # Настраиваем мок
        mock_clickhouse_client.get_post_stats.return_value = {
            'views_count': 100,
            'likes_count': 50,
            'comments_count': 25
        }

        # Создаем запрос
        request = statistics_pb2.PostStatsRequest(post_id=1)

        # Вызываем метод
        response = servicer.GetPostStats(request, mock_context)

        # Проверяем результат
        assert response.post_id == 1
        assert response.views_count == 100
        assert response.likes_count == 50
        assert response.comments_count == 25

        # Проверяем что метод был вызван
        mock_clickhouse_client.get_post_stats.assert_called_once_with(1)

    def test_get_post_dynamics(self, servicer, mock_clickhouse_client, mock_context):
        """Тест получения динамики"""
        # Настраиваем мок
        mock_clickhouse_client.get_post_dynamics.return_value = [
            {'date': '2024-01-01', 'count': 10},
            {'date': '2024-01-02', 'count': 15}
        ]

        # Создаем запрос
        request = statistics_pb2.PostDynamicsRequest(
            post_id=1,
            start_date='2024-01-01',
            end_date='2024-01-02'
        )

        # Вызываем метод для просмотров
        response = servicer.GetPostViewsDynamics(request, mock_context)

        # Проверяем результат
        assert len(response.daily_stats) == 2
        assert response.daily_stats[0].date == '2024-01-01'
        assert response.daily_stats[0].count == 10
        assert response.daily_stats[1].date == '2024-01-02'
        assert response.daily_stats[1].count == 15

    def test_get_top_posts(self, servicer, mock_clickhouse_client, mock_context):
        """Тест получения топ постов"""
        # Настраиваем мок
        mock_clickhouse_client.get_top_posts.return_value = [
            {'post_id': 1, 'count': 100},
            {'post_id': 2, 'count': 90},
            {'post_id': 3, 'count': 80}
        ]

        # Создаем запрос
        request = statistics_pb2.TopRequest(metric_type='views', limit=3)

        # Вызываем метод
        response = servicer.GetTopPosts(request, mock_context)

        # Проверяем результат
        assert len(response.posts) == 3
        assert response.posts[0].post_id == 1
        assert response.posts[0].count == 100
        assert response.posts[1].post_id == 2
        assert response.posts[1].count == 90

    def test_get_top_users(self, servicer, mock_clickhouse_client, mock_context):
        """Тест получения топ пользователей"""
        # Настраиваем мок
        mock_clickhouse_client.get_top_users.return_value = [
            {'user_id': 10, 'count': 50},
            {'user_id': 20, 'count': 40}
        ]

        # Создаем запрос
        request = statistics_pb2.TopRequest(metric_type='likes', limit=2)

        # Вызываем метод
        response = servicer.GetTopUsers(request, mock_context)

        # Проверяем результат
        assert len(response.users) == 2
        assert response.users[0].user_id == 10
        assert response.users[0].count == 50

    def test_error_handling(self, servicer, mock_clickhouse_client, mock_context):
        """Тест обработки ошибок"""
        # Настраиваем мок для выброса исключения
        mock_clickhouse_client.get_post_stats.side_effect = Exception("Database error")

        # Создаем запрос
        request = statistics_pb2.PostStatsRequest(post_id=1)

        # Вызываем метод
        response = servicer.GetPostStats(request, mock_context)

        # Проверяем что контекст был установлен с ошибкой
        mock_context.set_code.assert_called_once_with(grpc.StatusCode.INTERNAL)
        mock_context.set_details.assert_called_once()
        assert "Database error" in mock_context.set_details.call_args[0][0]