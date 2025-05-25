import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from statistics_service.app.kafka_consumer import KafkaEventConsumer


class TestKafkaEventConsumer:
    @pytest.fixture
    def mock_clickhouse_client(self):
        mock = Mock()
        mock.insert_event = Mock()
        return mock

    @pytest.fixture
    def kafka_consumer(self, mock_clickhouse_client):
        return KafkaEventConsumer(mock_clickhouse_client)

    def test_process_view_message(self, kafka_consumer, mock_clickhouse_client):
        """Тест обработки сообщения о просмотре"""
        # Создаем тестовое сообщение
        message = Mock()
        message.topic = 'post-views'
        message.value = {
            'user_id': 1,
            'post_id': 2,
            'timestamp': datetime.now().isoformat()
        }

        # Обрабатываем сообщение
        kafka_consumer.process_message(message)

        # Проверяем что событие было сохранено
        mock_clickhouse_client.insert_event.assert_called_once()
        call_args = mock_clickhouse_client.insert_event.call_args[1]
        assert call_args['event_type'] == 'view'
        assert call_args['user_id'] == 1
        assert call_args['post_id'] == 2

    def test_process_like_message(self, kafka_consumer, mock_clickhouse_client):
        """Тест обработки сообщения о лайке"""
        message = Mock()
        message.topic = 'post-likes'
        message.value = {
            'user_id': 3,
            'post_id': 4,
            'timestamp': datetime.now().isoformat()
        }

        kafka_consumer.process_message(message)

        call_args = mock_clickhouse_client.insert_event.call_args[1]
        assert call_args['event_type'] == 'like'
        assert call_args['user_id'] == 3
        assert call_args['post_id'] == 4

    def test_process_comment_message(self, kafka_consumer, mock_clickhouse_client):
        """Тест обработки сообщения о комментарии"""
        message = Mock()
        message.topic = 'post-comments'
        message.value = {
            'user_id': 5,
            'post_id': 6,
            'comment_id': 7,
            'comment_text': 'Test comment',
            'timestamp': datetime.now().isoformat()
        }

        kafka_consumer.process_message(message)

        call_args = mock_clickhouse_client.insert_event.call_args[1]
        assert call_args['event_type'] == 'comment'
        assert call_args['user_id'] == 5
        assert call_args['post_id'] == 6
        assert call_args['comment_id'] == 7

    def test_process_unknown_topic(self, kafka_consumer, mock_clickhouse_client):
        """Тест обработки неизвестного топика"""
        message = Mock()
        message.topic = 'unknown-topic'
        message.value = {'user_id': 1, 'post_id': 2}

        # Обрабатываем сообщение
        kafka_consumer.process_message(message)

        # Проверяем что insert_event НЕ был вызван
        mock_clickhouse_client.insert_event.assert_not_called()

    @patch('statistics_service.app.kafka_consumer.KafkaConsumer')
    def test_init_consumer(self, mock_kafka_consumer, kafka_consumer):
        """Тест инициализации consumer"""
        # Настраиваем мок
        mock_instance = Mock()
        mock_kafka_consumer.return_value = mock_instance

        # Инициализируем
        result = kafka_consumer.init_consumer()

        # Проверяем
        assert result is True
        assert kafka_consumer.consumer == mock_instance

        # Проверяем параметры
        mock_kafka_consumer.assert_called_once()
        call_args = mock_kafka_consumer.call_args[1]
        assert 'post-views' in mock_kafka_consumer.call_args[0]
        assert 'post-likes' in mock_kafka_consumer.call_args[0]
        assert 'post-comments' in mock_kafka_consumer.call_args[0]
        assert call_args['group_id'] == 'statistics-service'