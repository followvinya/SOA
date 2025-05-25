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
        from post_service.generated import posts_pb2_grpc
        from post_service.app.database import engine
        from post_service.app.models import Base
        from post_service.app.service import PostServicer

        logger.info("Starting gRPC server...")

        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        posts_pb2_grpc.add_PostServiceServicer_to_server(PostServicer(), server)

        server.add_insecure_port('[::]:50051')
        server.start()
        logger.info("gRPC server started successfully on port 50051")

        try:
            while True:
                time.sleep(86400)
        except KeyboardInterrupt:
            server.stop(0)
            logger.info("Server stopped")

    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    serve()