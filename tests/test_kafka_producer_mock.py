import pytest
from unittest.mock import Mock, patch, MagicMock
import sys

# Мокируем kafka и KafkaError до импорта
sys.modules['kafka'] = MagicMock()
sys.modules['kafka.errors'] = MagicMock()


# Создаем фейковый класс KafkaError
class MockKafkaError(Exception):
    pass


# Добавляем его в мок
sys.modules['kafka.errors'].KafkaError = MockKafkaError


class TestKafkaProducer:

    @patch('post_service.app.kafka_producer.producer')
    def test_send_event_success(self, mock_producer):
        """Тест успешной отправки события"""
        # Импортируем после мокирования
        from post_service.app.kafka_producer import send_event

        # Настраиваем мок
        mock_future = Mock()
        mock_future.get.return_value = Mock(partition=0, offset=100)
        mock_producer.send.return_value = mock_future
        mock_producer.flush = Mock()

        # Отправляем событие
        result = send_event("test-topic", "key1", {"data": "test"})

        # Проверяем
        assert result == True
        mock_producer.send.assert_called_once()
        mock_producer.flush.assert_called_once()

    @patch('post_service.app.kafka_producer.init_kafka_producer')
    @patch('post_service.app.kafka_producer.producer', None)  # Устанавливаем producer в None
    def test_send_event_failure(self, mock_init):
        """Тест неудачной отправки события"""
        from post_service.app.kafka_producer import send_event

        # Мокируем неудачную инициализацию
        mock_init.return_value = False

        # Отправляем событие
        result = send_event("test-topic", "key1", {"data": "test"})

        # Проверяем
        assert result == False
        mock_init.assert_called_once()

    @patch('post_service.app.kafka_producer.send_event')
    def test_send_user_registration_event(self, mock_send_event):
        """Тест отправки события регистрации"""
        from post_service.app.kafka_producer import send_user_registration_event

        mock_send_event.return_value = True

        registration_data = {
            "user_id": 1,
            "username": "testuser",
            "email": "test@example.com"
        }

        result = send_user_registration_event(1, registration_data)

        assert result == True
        mock_send_event.assert_called_once_with(
            "user-registration",
            1,
            registration_data
        )