import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from statistics_service.app.clickhouse_client import ClickHouseClient


class TestClickHouseClient:
    @pytest.fixture
    def mock_client(self):
        with patch('statistics_service.app.clickhouse_client.Client') as mock:
            yield mock

    @pytest.fixture
    def clickhouse_client(self, mock_client):
        # Мокаем init_database чтобы не создавать реальные таблицы
        with patch.object(ClickHouseClient, 'init_database'):
            return ClickHouseClient()

    def test_insert_event(self, clickhouse_client, mock_client):
        """Тест вставки события"""
        # Настраиваем мок
        mock_instance = mock_client.return_value
        clickhouse_client.client = mock_instance

        # Вызываем метод
        timestamp = datetime.now()
        clickhouse_client.insert_event(
            event_type='view',
            user_id=1,
            post_id=2,
            timestamp=timestamp
        )

        # Проверяем что execute был вызван
        mock_instance.execute.assert_called_once()
        call_args = mock_instance.execute.call_args

        # Проверяем SQL запрос
        assert "INSERT INTO events" in call_args[0][0]

        # Проверяем данные
        data = call_args[0][1][0]
        assert data[0] == 'view'
        assert data[1] == 1
        assert data[2] == 2
        assert data[4] == timestamp

    def test_get_post_stats(self, clickhouse_client, mock_client):
        """Тест получения статистики поста"""
        # Настраиваем мок для возврата данных
        mock_instance = mock_client.return_value
        clickhouse_client.client = mock_instance
        mock_instance.execute.return_value = [(10, 5, 3)]

        # Вызываем метод
        result = clickhouse_client.get_post_stats(post_id=1)

        # Проверяем результат
        assert result['views_count'] == 10
        assert result['likes_count'] == 5
        assert result['comments_count'] == 3

        # Проверяем SQL запрос
        call_args = mock_instance.execute.call_args
        assert "SELECT" in call_args[0][0]
        assert "countIf(event_type = 'view')" in call_args[0][0]
        assert call_args[0][1]['post_id'] == 1

    def test_get_post_dynamics(self, clickhouse_client, mock_client):
        """Тест получения динамики"""
        # Настраиваем мок
        mock_instance = mock_client.return_value
        clickhouse_client.client = mock_instance

        # Мокаем результат
        test_date = datetime.now().date()
        mock_instance.execute.return_value = [
            (test_date, 10),
            (test_date + timedelta(days=1), 15)
        ]

        # Вызываем метод
        result = clickhouse_client.get_post_dynamics(
            post_id=1,
            event_type='view',
            start_date='2024-01-01',
            end_date='2024-01-31'
        )

        # Проверяем результат
        assert len(result) == 2
        assert result[0]['date'] == str(test_date)
        assert result[0]['count'] == 10
        assert result[1]['count'] == 15

    def test_get_top_posts(self, clickhouse_client, mock_client):
        """Тест получения топ постов"""
        # Настраиваем мок
        mock_instance = mock_client.return_value
        clickhouse_client.client = mock_instance
        mock_instance.execute.return_value = [(1, 100), (2, 90), (3, 80)]

        # Вызываем метод
        result = clickhouse_client.get_top_posts(metric_type='views', limit=3)

        # Проверяем результат
        assert len(result) == 3
        assert result[0]['post_id'] == 1
        assert result[0]['count'] == 100
        assert result[1]['post_id'] == 2
        assert result[1]['count'] == 90

    def test_get_top_users(self, clickhouse_client, mock_client):
        """Тест получения топ пользователей"""
        # Настраиваем мок
        mock_instance = mock_client.return_value
        clickhouse_client.client = mock_instance
        mock_instance.execute.return_value = [(10, 50), (20, 40), (30, 30)]

        # Вызываем метод
        result = clickhouse_client.get_top_users(metric_type='likes', limit=3)

        # Проверяем результат
        assert len(result) == 3
        assert result[0]['user_id'] == 10
        assert result[0]['count'] == 50

    def test_init_database(self, mock_client):
        """Тест инициализации базы данных"""
        mock_instance = mock_client.return_value

        # Создаем клиент (init_database вызовется автоматически)
        client = ClickHouseClient()

        # Проверяем что были созданы база и таблица
        calls = mock_instance.execute.call_args_list
        assert len(calls) >= 2

        # Проверяем создание базы данных
        assert "CREATE DATABASE IF NOT EXISTS" in calls[0][0][0]

        # Проверяем создание таблицы
        assert "CREATE TABLE IF NOT EXISTS events" in calls[1][0][0]