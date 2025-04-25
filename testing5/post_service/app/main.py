import grpc
from concurrent import futures
import time
import logging
import sys
import os


sys.path.append("/app/generated")

import posts_pb2_grpc
from .database import engine
from .models import Base
from .service import PostServicer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def serve():
    logger.info(f"PYTHONPATH: {sys.path}")
    generated_dir = "/app/generated"
    logger.info(
        f"Files in {generated_dir}: {os.listdir(generated_dir) if os.path.exists(generated_dir) else 'directory not found'}")

    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    posts_pb2_grpc.add_PostServiceServicer_to_server(PostServicer(), server)

    server.add_insecure_port('[::]:50051')
    server.start()
    logger.info("gRPC server started on port 50051")

    try:
        while True:
            time.sleep(86400)  # One day in seconds
    except KeyboardInterrupt:
        server.stop(0)
        logger.info("Server stopped")


if __name__ == '__main__':
    serve()