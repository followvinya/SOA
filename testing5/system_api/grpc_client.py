import grpc
import os
import sys
from typing import List, Optional
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "..", "post_service", "generated"))

import posts_pb2
import posts_pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

POST_SERVICE_URL = os.getenv("POST_SERVICE_URL", "localhost:50051")


class PostServiceClient:
    def __init__(self):
        self.channel = grpc.insecure_channel(POST_SERVICE_URL)
        self.stub = posts_pb2_grpc.PostServiceStub(self.channel)

    def create_post(self, title: str, description: str, creator_id: int, is_private: bool = False,
                    tags: List[str] = None):
        logger.info(f"Creating post with title: {title}, creator_id: {creator_id}")
        try:
            request = posts_pb2.CreatePostRequest(
                title=title,
                description=description,
                creator_id=creator_id,
                is_private=is_private,
                tags=tags or []
            )
            response = self.stub.CreatePost(request)
            return {
                "id": response.id,
                "title": response.title,
                "description": response.description,
                "creator_id": response.creator_id,
                "created_at": response.created_at,
                "updated_at": response.updated_at,
                "is_private": response.is_private,
                "tags": list(response.tags)
            }
        except grpc.RpcError as e:
            status_code = e.code()
            details = e.details()
            logger.error(f"gRPC error: {status_code} - {details}")
            raise

    def get_post(self, post_id: int, user_id: int):
        logger.info(f"Getting post with ID: {post_id}, user_id: {user_id}")
        try:
            request = posts_pb2.GetPostRequest(id=post_id, user_id=user_id)
            response = self.stub.GetPost(request)
            return {
                "id": response.id,
                "title": response.title,
                "description": response.description,
                "creator_id": response.creator_id,
                "created_at": response.created_at,
                "updated_at": response.updated_at,
                "is_private": response.is_private,
                "tags": list(response.tags)
            }
        except grpc.RpcError as e:
            status_code = e.code()
            details = e.details()
            logger.error(f"gRPC error: {status_code} - {details}")
            raise

    def list_posts(self, user_id: int, page: int = 1, page_size: int = 10):
        logger.info(f"Listing posts for user_id: {user_id}, page: {page}, page_size: {page_size}")
        try:
            request = posts_pb2.ListPostsRequest(user_id=user_id, page=page, page_size=page_size)
            response = self.stub.ListPosts(request)

            posts = []
            for post in response.posts:
                posts.append({
                    "id": post.id,
                    "title": post.title,
                    "description": post.description,
                    "creator_id": post.creator_id,
                    "created_at": post.created_at,
                    "updated_at": post.updated_at,
                    "is_private": post.is_private,
                    "tags": list(post.tags)
                })

            return {
                "posts": posts,
                "total": response.total,
                "page": response.page,
                "page_size": response.page_size
            }
        except grpc.RpcError as e:
            status_code = e.code()
            details = e.details()
            logger.error(f"gRPC error: {status_code} - {details}")
            raise

    def update_post(self, post_id: int, creator_id: int, title: Optional[str] = None,
                    description: Optional[str] = None, is_private: Optional[bool] = None,
                    tags: Optional[List[str]] = None):
        logger.info(f"Updating post with ID: {post_id}, creator_id: {creator_id}")
        try:
            try:
                current_post = self.get_post(post_id, creator_id)
            except grpc.RpcError:
                current_post = {
                    "title": "",
                    "description": "",
                    "is_private": False,
                    "tags": []
                }

            # Обновляем только те поля, которые переданы
            request_title = title if title is not None else current_post.get("title", "")
            request_description = description if description is not None else current_post.get("description", "")
            request_is_private = is_private if is_private is not None else current_post.get("is_private", False)
            request_tags = tags if tags is not None else current_post.get("tags", [])

            logger.info(
                f"Sending request data: title={request_title}, description={request_description}, is_private={request_is_private}, tags={request_tags}")

            request = posts_pb2.UpdatePostRequest(
                id=post_id,
                title=request_title,
                description=request_description,
                creator_id=creator_id,
                is_private=request_is_private,
                tags=request_tags or []
            )

            response = self.stub.UpdatePost(request)
            logger.info(f"Received response: {response}")

            if not response.id:
                logger.error("Received empty response from gRPC server")
                raise Exception("Post update failed: Empty response from server")

            return {
                "id": response.id,
                "title": response.title,
                "description": response.description,
                "creator_id": response.creator_id,
                "created_at": response.created_at,
                "updated_at": response.updated_at,
                "is_private": response.is_private,
                "tags": list(response.tags)
            }
        except grpc.RpcError as e:
            status_code = e.code()
            details = e.details()
            logger.error(f"gRPC error: {status_code} - {details}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            raise

    def delete_post(self, post_id: int, creator_id: int):
        logger.info(f"Deleting post with ID: {post_id}, creator_id: {creator_id}")
        try:
            request = posts_pb2.DeletePostRequest(id=post_id, creator_id=creator_id)
            response = self.stub.DeletePost(request)
            return response.success
        except grpc.RpcError as e:
            status_code = e.code()
            details = e.details()
            logger.error(f"gRPC error: {status_code} - {details}")
            raise