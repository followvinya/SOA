import json
import logging
from kafka import KafkaProducer
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")

# Kafka topics
USER_REGISTRATION_TOPIC = "user-registration"
POST_LIKE_TOPIC = "post-likes"
POST_VIEW_TOPIC = "post-views"
POST_COMMENT_TOPIC = "post-comments"

try:
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: str(k).encode('utf-8') if k else None
    )
    logger.info(f"Kafka producer initialized with bootstrap servers: {KAFKA_BOOTSTRAP_SERVERS}")
except Exception as e:
    logger.error(f"Failed to initialize Kafka producer: {str(e)}")
    producer = None


def send_event(topic, key, value):
    """Send an event to Kafka topic"""
    if not producer:
        logger.error(f"Kafka producer not available, can't send event to topic {topic}")
        return False

    try:
        # Add timestamp to the event
        if isinstance(value, dict):
            value['timestamp'] = datetime.now().isoformat()

        # Send the event
        future = producer.send(topic, key=key, value=value)
        producer.flush()  # Ensure the message is sent immediately
        record_metadata = future.get(timeout=10)

        logger.info(
            f"Event sent to topic {topic} at partition {record_metadata.partition}, offset {record_metadata.offset}")
        return True
    except Exception as e:
        logger.error(f"Error sending event to Kafka topic {topic}: {str(e)}")
        return False


def send_user_registration_event(user_id, registration_data):
    """Send user registration event to Kafka"""
    return send_event(USER_REGISTRATION_TOPIC, user_id, registration_data)


def send_post_like_event(user_id, post_id):
    """Send post like event to Kafka"""
    event_data = {
        "user_id": user_id,
        "post_id": post_id,
        "action": "like"
    }
    return send_event(POST_LIKE_TOPIC, user_id, event_data)


def send_post_view_event(user_id, post_id):
    """Send post view event to Kafka"""
    event_data = {
        "user_id": user_id,
        "post_id": post_id,
        "action": "view"
    }
    return send_event(POST_VIEW_TOPIC, user_id, event_data)


def send_post_comment_event(user_id, post_id, comment_id, comment_text):
    """Send post comment event to Kafka"""
    event_data = {
        "user_id": user_id,
        "post_id": post_id,
        "comment_id": comment_id,
        "comment_text": comment_text,
        "action": "comment"
    }
    return send_event(POST_COMMENT_TOPIC, user_id, event_data)