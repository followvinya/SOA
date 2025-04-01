import grpc
from datetime import datetime
from typing import List
from concurrent import futures
import sys
import os
import logging

# Настраиваем путь для импорта сгенерированных файлов
sys.path.append("/app/generated")

import posts_pb2
import posts_pb2_grpc
from .database import get_db, SessionLocal
from .repository import PostRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PostServicer(posts_pb2_grpc.PostServiceServicer):
    def CreatePost(self, request, context):
        logger.info(f"Creating post with title: {request.title}")
        db = SessionLocal()
        try:
            repo = PostRepository(db)
            post = repo.create_post(
                title=request.title,
                description=request.description,
                creator_id=request.creator_id,
                is_private=request.is_private,
                tags=list(request.tags)
            )

            return posts_pb2.Post(
                id=post.id,
                title=post.title,
                description=post.description,
                creator_id=post.creator_id,
                created_at=post.created_at.isoformat(),
                updated_at=post.updated_at.isoformat(),
                is_private=post.is_private,
                tags=post.tags
            )
        except Exception as e:
            logger.error(f"Error creating post: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error creating post: {str(e)}")
            return posts_pb2.Post()
        finally:
            db.close()

    # ... остальные методы остаются без изменений ...

    def GetPost(self, request, context):
        logger.info(f"Fetching post with ID: {request.id}")
        db = SessionLocal()
        try:
            repo = PostRepository(db)
            post = repo.get_post(post_id=request.id, user_id=request.user_id)

            if not post:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Post not found or access denied")
                return posts_pb2.Post()

            return posts_pb2.Post(
                id=post.id,
                title=post.title,
                description=post.description,
                creator_id=post.creator_id,
                created_at=post.created_at.isoformat(),
                updated_at=post.updated_at.isoformat(),
                is_private=post.is_private,
                tags=post.tags
            )
        except Exception as e:
            logger.error(f"Error fetching post: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error fetching post: {str(e)}")
            return posts_pb2.Post()
        finally:
            db.close()

    def ListPosts(self, request, context):
        logger.info(
            f"Listing posts for user ID: {request.user_id}, page: {request.page}, page_size: {request.page_size}")
        db = SessionLocal()
        try:
            repo = PostRepository(db)
            posts, total, page, page_size = repo.list_posts(
                user_id=request.user_id,
                page=request.page,
                page_size=request.page_size
            )

            response = posts_pb2.ListPostsResponse(
                total=total,
                page=page,
                page_size=page_size
            )

            for post in posts:
                pb_post = posts_pb2.Post(
                    id=post.id,
                    title=post.title,
                    description=post.description,
                    creator_id=post.creator_id,
                    created_at=post.created_at.isoformat(),
                    updated_at=post.updated_at.isoformat(),
                    is_private=post.is_private,
                    tags=post.tags
                )
                response.posts.append(pb_post)

            return response
        except Exception as e:
            logger.error(f"Error listing posts: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error listing posts: {str(e)}")
            return posts_pb2.ListPostsResponse()
        finally:
            db.close()

    def UpdatePost(self, request, context):
        logger.info(f"Updating post with ID: {request.id}")
        db = SessionLocal()
        try:
            repo = PostRepository(db)
            post = repo.update_post(
                post_id=request.id,
                title=request.title,
                description=request.description,
                creator_id=request.creator_id,
                is_private=request.is_private,
                tags=list(request.tags)
            )

            if not post:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Post not found or access denied")
                return posts_pb2.Post()

            logger.info(f"Post updated successfully: {post.id}")
            # Логируем данные для отладки
            logger.info(
                f"Updated post data: title={post.title}, description={post.description}, created_at={post.created_at}, updated_at={post.updated_at}")

            # Преобразуем datetime в строки, чтобы избежать ошибок сериализации
            created_at_str = post.created_at.isoformat() if post.created_at else ""
            updated_at_str = post.updated_at.isoformat() if post.updated_at else ""

            return posts_pb2.Post(
                id=post.id,
                title=post.title,
                description=post.description,
                creator_id=post.creator_id,
                created_at=created_at_str,
                updated_at=updated_at_str,
                is_private=post.is_private,
                tags=post.tags or []  # Защищаемся от None
            )
        except Exception as e:
            logger.error(f"Error updating post: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error updating post: {str(e)}")
            return posts_pb2.Post()
        finally:
            db.close()

    def DeletePost(self, request, context):
        logger.info(f"Deleting post with ID: {request.id}")
        db = SessionLocal()
        try:
            repo = PostRepository(db)
            success = repo.delete_post(post_id=request.id, creator_id=request.creator_id)

            if not success:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Post not found or access denied")
                return posts_pb2.DeletePostResponse(success=False)

            return posts_pb2.DeletePostResponse(success=True)
        except Exception as e:
            logger.error(f"Error deleting post: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error deleting post: {str(e)}")
            return posts_pb2.DeletePostResponse(success=False)
        finally:
            db.close()