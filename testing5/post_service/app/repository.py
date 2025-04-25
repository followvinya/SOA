from sqlalchemy.orm import Session
from . import models
from typing import List, Optional
from datetime import datetime

#CRUD операции для постов

class PostRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_post(self, title: str, description: str, creator_id: int, is_private: bool = False,
                    tags: List[str] = None):
        db_post = models.Post(
            title=title,
            description=description,
            creator_id=creator_id,
            is_private=is_private,
            tags=tags or []
        )
        self.db.add(db_post)
        self.db.commit()
        self.db.refresh(db_post)
        return db_post

    def get_post(self, post_id: int, user_id: int):
        post = self.db.query(models.Post).filter(models.Post.id == post_id).first()

        if not post:
            return None

        # Проверка доступа: если пост приватный, его может видеть только создатель
        if post.is_private and post.creator_id != user_id:
            return None

        return post

    def list_posts(self, user_id: int, page: int = 1, page_size: int = 10):
        # По умолчанию показываем только посты пользователя и публичные посты других
        skip = (page - 1) * page_size

        query = self.db.query(models.Post).filter(
            (models.Post.creator_id == user_id) |  # Посты пользователя
            ((models.Post.is_private == False) & (models.Post.creator_id != user_id))  # Публичные посты других
        )

        total = query.count()
        posts = query.order_by(models.Post.created_at.desc()).offset(skip).limit(page_size).all()

        return posts, total, page, page_size

    def update_post(self, post_id: int, title: str, description: str, creator_id: int, is_private: bool,
                    tags: List[str]):
        post = self.db.query(models.Post).filter(models.Post.id == post_id).first()

        if not post:
            return None

        # Проверка авторизации: только создатель может обновить пост
        if post.creator_id != creator_id:
            return None

        post.title = title
        post.description = description
        post.is_private = is_private
        post.tags = tags
        post.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(post)
        return post

    def delete_post(self, post_id: int, creator_id: int):
        post = self.db.query(models.Post).filter(models.Post.id == post_id).first()

        if not post:
            return False

        # Проверка авторизации: только создатель может удалить пост
        if post.creator_id != creator_id:
            return False

        self.db.delete(post)
        self.db.commit()
        return True

    def like_post(self, post_id: int, user_id: int):
        """Add a like to a post"""
        # Check if post exists and user has access
        post = self.get_post(post_id, user_id)
        if not post:
            return None

        # Check if like already exists
        existing_like = self.db.query(models.PostLike).filter(
            models.PostLike.post_id == post_id,
            models.PostLike.user_id == user_id
        ).first()

        if existing_like:
            return existing_like

        # Create new like
        like = models.PostLike(post_id=post_id, user_id=user_id)
        self.db.add(like)
        self.db.commit()
        self.db.refresh(like)
        return like

    def view_post(self, post_id: int, user_id: int):
        """Record a view for a post"""
        # Check if post exists and user has access
        post = self.get_post(post_id, user_id)
        if not post:
            return None

        # Create view record
        view = models.PostView(post_id=post_id, user_id=user_id)
        self.db.add(view)
        self.db.commit()
        self.db.refresh(view)
        return view

    def add_comment(self, post_id: int, user_id: int, text: str):
        """Add a comment to a post"""
        # Check if post exists and user has access
        post = self.get_post(post_id, user_id)
        if not post:
            return None

        # Create comment
        comment = models.PostComment(post_id=post_id, user_id=user_id, text=text)
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        return comment

    def get_post_comments(self, post_id: int, user_id: int, page: int = 1, page_size: int = 10):
        """Get comments for a post with pagination"""
        # Check if post exists and user has access
        post = self.get_post(post_id, user_id)
        if not post:
            return None, 0, page, page_size

        # Get comments with pagination
        skip = (page - 1) * page_size
        query = self.db.query(models.PostComment).filter(models.PostComment.post_id == post_id)

        total = query.count()
        comments = query.order_by(models.PostComment.created_at.desc()).offset(skip).limit(page_size).all()

        return comments, total, page, page_size