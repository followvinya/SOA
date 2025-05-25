import grpc
from concurrent import futures
import time
import logging
import sys
import os

sys.path.insert(0, '/app')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def serve():
    try:
        from statistics_service.generated import statistics_pb2_grpc
        from statistics_service.app.service import StatisticsServicer
        from statistics_service.app.clickhouse_client import ClickHouseClient
        from statistics_service.app.kafka_consumer import KafkaEventConsumer

        logger.info("Starting statistics gRPC server...")

        clickhouse_client = ClickHouseClient()

        kafka_consumer = KafkaEventConsumer(clickhouse_client)
        kafka_consumer.start()

        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        statistics_pb2_grpc.add_StatisticsServiceServicer_to_server(
            StatisticsServicer(clickhouse_client),
            server
        )

        server.add_insecure_port('[::]:50052')
        server.start()
        logger.info("Statistics gRPC server started successfully on port 50052")

        try:
            while True:
                time.sleep(86400)
        except KeyboardInterrupt:
            kafka_consumer.stop()
            server.stop(0)
            logger.info("Server stopped")

    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    serve()