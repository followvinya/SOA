import grpc
from datetime import datetime
from typing import List
from concurrent import futures
import sys
import os
import logging

from post_service.app import models

sys.path.insert(0, '/app')

from post_service.generated import posts_pb2
from post_service.generated import posts_pb2_grpc
from post_service.app.database import get_db, SessionLocal
from post_service.app.repository import PostRepository
from post_service.app.kafka_producer import send_post_like_event, send_post_view_event, send_post_comment_event

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
                created_at=post.created_at.isoformat() if post.created_at else "",
                updated_at=post.updated_at.isoformat() if post.updated_at else "",
                is_private=post.is_private,
                tags=post.tags or []
            )
        except Exception as e:
            logger.error(f"Error creating post: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error creating post: {str(e)}")
            return posts_pb2.Post()
        finally:
            db.close()


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
            logger.info(
                f"Updated post data: title={post.title}, description={post.description}, created_at={post.created_at}, updated_at={post.updated_at}")

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
                tags=post.tags or []
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

    def LikePost(self, request, context):
        logger.info(f"Liking post with ID: {request.post_id} by user ID: {request.user_id}")
        db = SessionLocal()
        try:
            repo = PostRepository(db)

            # Проверяем, существует ли уже лайк
            existing_like = db.query(models.PostLike).filter(
                models.PostLike.post_id == request.post_id,
                models.PostLike.user_id == request.user_id
            ).first()

            if existing_like:
                # Лайк уже существует, возвращаем успех но НЕ отправляем событие
                logger.info(f"Like already exists for post {request.post_id} by user {request.user_id}")
                return posts_pb2.LikePostResponse(success=True, like_id=existing_like.id)

            # Создаем новый лайк
            like = repo.like_post(post_id=request.post_id, user_id=request.user_id)

            if not like:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Post not found or access denied")
                return posts_pb2.LikePostResponse(success=False)

            # Отправляем событие ТОЛЬКО для нового лайка
            send_post_like_event(request.user_id, request.post_id)

            return posts_pb2.LikePostResponse(success=True, like_id=like.id)
        except Exception as e:
            logger.error(f"Error liking post: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error liking post: {str(e)}")
            return posts_pb2.LikePostResponse(success=False)
        finally:
            db.close()

    def ViewPost(self, request, context):
        logger.info(f"Recording view for post with ID: {request.post_id} by user ID: {request.user_id}")
        db = SessionLocal()
        try:
            repo = PostRepository(db)
            view = repo.view_post(post_id=request.post_id, user_id=request.user_id)

            if not view:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Post not found or access denied")
                return posts_pb2.ViewPostResponse(success=False)

            from .kafka_producer import send_post_view_event
            send_post_view_event(request.user_id, request.post_id)

            return posts_pb2.ViewPostResponse(success=True, view_id=view.id)
        except Exception as e:
            logger.error(f"Error recording view: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error recording view: {str(e)}")
            return posts_pb2.ViewPostResponse(success=False)
        finally:
            db.close()

    def AddComment(self, request, context):
        logger.info(f"Adding comment to post with ID: {request.post_id} by user ID: {request.user_id}")
        db = SessionLocal()
        try:
            repo = PostRepository(db)
            comment = repo.add_comment(post_id=request.post_id, user_id=request.user_id, text=request.text)

            if not comment:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Post not found or access denied")
                return posts_pb2.Comment()

            from .kafka_producer import send_post_comment_event
            send_post_comment_event(request.user_id, request.post_id, comment.id, comment.text)

            return posts_pb2.Comment(
                id=comment.id,
                post_id=comment.post_id,
                user_id=comment.user_id,
                text=comment.text,
                created_at=comment.created_at.isoformat(),
                updated_at=comment.updated_at.isoformat()
            )
        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error adding comment: {str(e)}")
            return posts_pb2.Comment()
        finally:
            db.close()

    def GetPostComments(self, request, context):
        logger.info(f"Getting comments for post with ID: {request.post_id}")
        db = SessionLocal()
        try:
            repo = PostRepository(db)
            comments, total, page, page_size = repo.get_post_comments(
                post_id=request.post_id,
                user_id=request.user_id,
                page=request.page,
                page_size=request.page_size
            )

            if comments is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Post not found or access denied")
                return posts_pb2.GetPostCommentsResponse()

            response = posts_pb2.GetPostCommentsResponse(
                total=total,
                page=page,
                page_size=page_size
            )

            for comment in comments:
                pb_comment = posts_pb2.Comment(
                    id=comment.id,
                    post_id=comment.post_id,
                    user_id=comment.user_id,
                    text=comment.text,
                    created_at=comment.created_at.isoformat(),
                    updated_at=comment.updated_at.isoformat()
                )
                response.comments.append(pb_comment)

            return response
        except Exception as e:
            logger.error(f"Error getting comments: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error getting comments: {str(e)}")
            return posts_pb2.GetPostCommentsResponse()
        finally:
            db.close()
