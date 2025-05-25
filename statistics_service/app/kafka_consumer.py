import json
import logging
import threading
import time
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import os

from .clickhouse_client import ClickHouseClient

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")


class KafkaEventConsumer:
    def __init__(self, clickhouse_client: ClickHouseClient):
        self.clickhouse_client = clickhouse_client
        self.consumer = None
        self.running = False

    def init_consumer(self):
        """Инициализируем Kafka consumer"""
        try:
            self.consumer = KafkaConsumer(
                'post-views',
                'post-likes',
                'post-comments',
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='statistics-service',
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            logger.info("Kafka consumer initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Kafka consumer: {str(e)}")
            return False

    def process_message(self, message):
        """Обрабатываем сообщение из Kafka"""
        try:
            topic = message.topic
            value = message.value

            event_type_map = {
                'post-views': 'view',
                'post-likes': 'like',
                'post-comments': 'comment'
            }

            event_type = event_type_map.get(topic)
            if not event_type:
                logger.warning(f"Unknown topic: {topic}")
                return

            user_id = value.get('user_id')
            post_id = value.get('post_id')
            comment_id = value.get('comment_id') if event_type == 'comment' else None
            timestamp_str = value.get('timestamp')


            timestamp = datetime.now()
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except:
                    pass


            self.clickhouse_client.insert_event(
                event_type=event_type,
                user_id=user_id,
                post_id=post_id,
                comment_id=comment_id,
                timestamp=timestamp
            )

            logger.info(f"Processed {event_type} event for post {post_id} by user {user_id}")

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")

    def start(self):
        """Запускаем consumer в отдельном потоке"""
        if not self.init_consumer():
            logger.error("Failed to start consumer")
            return

        self.running = True
        thread = threading.Thread(target=self._consume_loop)
        thread.daemon = True
        thread.start()
        logger.info("Kafka consumer started")

    def _consume_loop(self):
        """Основной цикл обработки сообщений"""
        while self.running:
            try:
                for message in self.consumer:
                    if not self.running:
                        break
                    self.process_message(message)
            except Exception as e:
                logger.error(f"Error in consumer loop: {str(e)}")
                time.sleep(5)
                if self.running:
                    self.init_consumer()

    def stop(self):
        """Останавливаем consumer"""
        self.running = False
        if self.consumer:
            self.consumer.close()