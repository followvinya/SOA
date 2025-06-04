import pytest
import json
import time
from kafka import KafkaProducer, KafkaConsumer
from datetime import datetime
import sys
import os

sys.path.insert(0, '/app')


class TestKafkaIntegration:

    def test_post_like_event_processing(self, clickhouse_client):
        """Test 1: Kafka processes post like events and saves to ClickHouse"""
        # Create Kafka producer
        producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: str(k).encode('utf-8') if k else None
        )

        # Send like event
        event_data = {
            "user_id": 123,
            "post_id": 456,
            "action": "like",
            "timestamp": datetime.now().isoformat()
        }

        producer.send('post-likes', key=123, value=event_data)
        producer.flush()
        producer.close()

        # Wait for processing
        time.sleep(3)

        # Verify data in ClickHouse
        result = clickhouse_client.execute("""
            SELECT event_type, user_id, post_id 
            FROM events 
            WHERE event_type = 'like' AND user_id = 123 AND post_id = 456
        """)

        assert len(result) > 0
        assert result[0][0] == 'like'
        assert result[0][1] == 123
        assert result[0][2] == 456

    def test_post_comment_event_processing(self, clickhouse_client):
        """Test 2: Kafka processes post comment events and saves to ClickHouse"""
        # Create Kafka producer
        producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: str(k).encode('utf-8') if k else None
        )

        # Send comment event
        event_data = {
            "user_id": 789,
            "post_id": 101,
            "comment_id": 55,
            "comment_text": "Great post!",
            "action": "comment",
            "timestamp": datetime.now().isoformat()
        }

        producer.send('post-comments', key=789, value=event_data)
        producer.flush()
        producer.close()

        # Wait for processing
        time.sleep(3)

        # Verify data in ClickHouse
        result = clickhouse_client.execute("""
            SELECT event_type, user_id, post_id, comment_id 
            FROM events 
            WHERE event_type = 'comment' AND user_id = 789 AND post_id = 101
        """)

        assert len(result) > 0
        assert result[0][0] == 'comment'
        assert result[0][1] == 789
        assert result[0][2] == 101
        assert result[0][3] == 55