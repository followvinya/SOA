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


def send_user_registration_event(user_id, registration_data):
    """Send user registration event to Kafka"""
    if not producer:
        logger.error(f"Kafka producer not available, can't send user registration event")
        return False

    try:
        # Add timestamp to the event
        if isinstance(registration_data, dict):
            registration_data['timestamp'] = datetime.now().isoformat()

        # Send the event
        future = producer.send(USER_REGISTRATION_TOPIC, key=user_id, value=registration_data)
        producer.flush()  # Ensure the message is sent immediately
        record_metadata = future.get(timeout=10)

        logger.info(
            f"User registration event sent to topic {USER_REGISTRATION_TOPIC} at partition {record_metadata.partition}, offset {record_metadata.offset}")
        return True
    except Exception as e:
        logger.error(f"Error sending user registration event to Kafka: {str(e)}")
        return False