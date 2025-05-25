import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
import json


class TestKafkaEvents:

    @patch('post_service.app.kafka_producer.producer')
    def test_send_post_like_event(self, mock_producer):
        from post_service.app.kafka_producer import send_post_like_event
        mock_producer.send = Mock()
        mock_producer.flush = Mock()
        mock_future = Mock()
        mock_future.get.return_value = Mock(partition=0, offset=100)
        mock_producer.send.return_value = mock_future

        result = send_post_like_event(user_id=123, post_id=456)
        assert result == True

        assert mock_producer.send.called
        call_args = mock_producer.send.call_args

        assert call_args[0][0] == 'post-likes'
        assert call_args[1]['key'] == 123

        sent_data = call_args[1]['value']
        assert sent_data['user_id'] == 123
        assert sent_data['post_id'] == 456
        assert sent_data['action'] == 'like'
        assert 'timestamp' in sent_data

    @patch('post_service.app.kafka_producer.producer')
    def test_send_post_view_event(self, mock_producer):
        from post_service.app.kafka_producer import send_post_view_event

        mock_producer.send = Mock()
        mock_producer.flush = Mock()
        mock_future = Mock()
        mock_future.get.return_value = Mock(partition=0, offset=101)
        mock_producer.send.return_value = mock_future

        result = send_post_view_event(user_id=789, post_id=321)

        assert result == True
        call_args = mock_producer.send.call_args
        assert call_args[0][0] == 'post-views'  # topic
        assert call_args[1]['key'] == 789  # user_id

        sent_data = call_args[1]['value']
        assert sent_data['user_id'] == 789
        assert sent_data['post_id'] == 321
        assert sent_data['action'] == 'view'
        assert 'timestamp' in sent_data

    @patch('post_service.app.kafka_producer.producer')
    def test_send_post_comment_event(self, mock_producer):
        from post_service.app.kafka_producer import send_post_comment_event

        mock_producer.send = Mock()
        mock_producer.flush = Mock()
        mock_future = Mock()
        mock_future.get.return_value = Mock(partition=0, offset=102)
        mock_producer.send.return_value = mock_future

        result = send_post_comment_event(
            user_id=111,
            post_id=222,
            comment_id=333,
            comment_text="Great post!"
        )

        assert result == True
        call_args = mock_producer.send.call_args
        assert call_args[0][0] == 'post-comments'  # topic
        assert call_args[1]['key'] == 111  # user_id

        sent_data = call_args[1]['value']
        assert sent_data['user_id'] == 111
        assert sent_data['post_id'] == 222
        assert sent_data['comment_id'] == 333
        assert sent_data['comment_text'] == "Great post!"
        assert sent_data['action'] == 'comment'
        assert 'timestamp' in sent_data

    @patch('user_service.kafka_producer.producer')
    def test_send_user_registration_event(self, mock_producer):
        from user_service.kafka_producer import send_user_registration_event

        mock_producer.send = Mock()
        mock_producer.flush = Mock()
        mock_future = Mock()
        mock_future.get.return_value = Mock(partition=0, offset=103)
        mock_producer.send.return_value = mock_future

        registration_data = {
            "user_id": 999,
            "username": "newuser",
            "email": "new@example.com",
            "registered_at": datetime.now().isoformat()
        }

        result = send_user_registration_event(999, registration_data)
        assert result == True

        call_args = mock_producer.send.call_args
        assert call_args[0][0] == 'user-registration'  # topic
        assert call_args[1]['key'] == 999  # user_id

        sent_data = call_args[1]['value']
        assert sent_data['user_id'] == 999
        assert sent_data['username'] == "newuser"
        assert sent_data['email'] == "new@example.com"
        assert 'timestamp' in sent_data
