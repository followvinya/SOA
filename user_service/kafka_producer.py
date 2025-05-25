import json
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError
import time
import os
from datetime import datetime

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")

USER_REGISTRATION_TOPIC = "user-registration"

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

def send_user_registration_event(user_id, registration_data):
    if not producer:
        logger.warning(f"Kafka producer not available, attempting to reinitialize...")
        if not init_kafka_producer():
            logger.error(f"Cannot send user registration event")
            return False

    try:
        if isinstance(registration_data, dict):
            registration_data['timestamp'] = datetime.now().isoformat()

        future = producer.send(USER_REGISTRATION_TOPIC, key=user_id, value=registration_data)
        producer.flush()
        record_metadata = future.get(timeout=10)

        logger.info(
            f"User registration event sent to topic {USER_REGISTRATION_TOPIC} at partition {record_metadata.partition}, offset {record_metadata.offset}")
        return True
    except KafkaError as e:
        logger.error(f"Kafka error sending user registration event: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error sending user registration event to Kafka: {str(e)}")
        return False
