import json
import logging
import os
import time
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")

USER_REGISTRATION_TOPIC = "user-registration"
POST_LIKE_TOPIC = "post-likes"
POST_VIEW_TOPIC = "post-views"
POST_COMMENT_TOPIC = "post-comments"

producer = None


def init_kafka_producer(retries=5, delay=5):
    global producer

    for attempt in range(retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: str(k).encode('utf-8') if k else None,
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=1
            )
            logger.info(f"Kafka producer initialized successfully with bootstrap servers: {KAFKA_BOOTSTRAP_SERVERS}")
            return True
        except Exception as e:
            logger.error(f"Attempt {attempt + 1}/{retries} - Failed to initialize Kafka producer: {str(e)}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                logger.error("Failed to initialize Kafka producer after all retries")
                return False

init_kafka_producer()

def send_event(topic, key, value):
    if not producer:
        logger.warning(f"Kafka producer not available, attempting to reinitialize...")
        if not init_kafka_producer():
            logger.error(f"Cannot send event to topic {topic}")
            return False

    try:
        if isinstance(value, dict):
            value['timestamp'] = datetime.now().isoformat()

        future = producer.send(topic, key=key, value=value)
        producer.flush()  # Ensure the message is sent immediately
        record_metadata = future.get(timeout=10)

        logger.info(
            f"Event sent to topic {topic} at partition {record_metadata.partition}, offset {record_metadata.offset}")
        return True
    except KafkaError as e:
        logger.error(f"Kafka error sending event to topic {topic}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error sending event to Kafka topic {topic}: {str(e)}")
        return False


def send_user_registration_event(user_id, registration_data):
    return send_event(USER_REGISTRATION_TOPIC, user_id, registration_data)


def send_post_like_event(user_id, post_id):
    event_data = {
        "user_id": user_id,
        "post_id": post_id,
        "action": "like"
    }
    return send_event(POST_LIKE_TOPIC, user_id, event_data)


def send_post_view_event(user_id, post_id):
    event_data = {
        "user_id": user_id,
        "post_id": post_id,
        "action": "view"
    }
    return send_event(POST_VIEW_TOPIC, user_id, event_data)


def send_post_comment_event(user_id, post_id, comment_id, comment_text):
    event_data = {
        "user_id": user_id,
        "post_id": post_id,
        "comment_id": comment_id,
        "comment_text": comment_text,
        "action": "comment"
    }
    return send_event(POST_COMMENT_TOPIC, user_id, event_data)
