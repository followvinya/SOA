import pytest
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from post_service.app.repository import PostRepository
from datetime import datetime

# Создаем базовый класс для тестовых моделей
Base = declarative_base()


# Переопределяем модели для SQLite (используем JSON вместо ARRAY)
class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    creator_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    is_private = Column(Boolean, default=False)
    tags = Column(JSON, nullable=True)  # JSON вместо ARRAY для SQLite


class PostLike(Base):
    __tablename__ = "post_likes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PostView(Base):
    __tablename__ = "post_views"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PostComment(Base):
    __tablename__ = "post_comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


# Создаем тестовую БД в памяти
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """Создает чистую БД для каждого теста"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Патчим модели в репозитории
    import post_service.app.models
    post_service.app.models.Post = Post
    post_service.app.models.PostLike = PostLike
    post_service.app.models.PostView = PostView
    post_service.app.models.PostComment = PostComment

    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def repository(db):
    """Создает экземпляр репозитория"""
    return PostRepository(db)


class TestPostRepository:
    def test_create_post(self, repository):
        """Тест создания поста"""
        post = repository.create_post(
            title="Test Post",
            description="Test Description",
            creator_id=1,
            is_private=False,
            tags=["test", "python"]
        )

        assert post.id is not None
        assert post.title == "Test Post"
        assert post.description == "Test Description"
        assert post.creator_id == 1
        assert post.is_private == False
        assert post.tags == ["test", "python"]

    def test_get_post(self, repository):
        """Тест получения поста"""
        # Создаем пост
        created_post = repository.create_post(
            title="Test Post",
            description="Test Description",
            creator_id=1
        )

        # Получаем пост
        post = repository.get_post(created_post.id, user_id=1)
        assert post is not None
        assert post.id == created_post.id
        assert post.title == "Test Post"

    def test_get_private_post_access_denied(self, repository):
        """Тест доступа к приватному посту"""
        # Создаем приватный пост
        private_post = repository.create_post(
            title="Private Post",
            description="Private Description",
            creator_id=1,
            is_private=True
        )

        # Пытаемся получить пост другим пользователем
        post = repository.get_post(private_post.id, user_id=2)
        assert post is None

    def test_update_post(self, repository):
        """Тест обновления поста"""
        # Создаем пост
        post = repository.create_post(
            title="Old Title",
            description="Old Description",
            creator_id=1
        )

        # Обновляем пост
        updated_post = repository.update_post(
            post_id=post.id,
            title="New Title",
            description="New Description",
            creator_id=1,
            is_private=False,
            tags=["updated"]
        )

        assert updated_post is not None
        assert updated_post.title == "New Title"
        assert updated_post.description == "New Description"
        assert updated_post.tags == ["updated"]

    def test_delete_post(self, repository):
        """Тест удаления поста"""
        # Создаем пост
        post = repository.create_post(
            title="To Delete",
            description="Will be deleted",
            creator_id=1
        )

        # Удаляем пост
        result = repository.delete_post(post.id, creator_id=1)
        assert result == True

        # Проверяем, что пост удален
        deleted_post = repository.get_post(post.id, user_id=1)
        assert deleted_post is None

    def test_like_post(self, repository):
        """Тест лайка поста"""
        # Создаем пост
        post = repository.create_post(
            title="Test Post",
            description="Test Description",
            creator_id=1
        )

        # Лайкаем пост
        like = repository.like_post(post.id, user_id=2)
        assert like is not None
        assert like.post_id == post.id
        assert like.user_id == 2

        # Проверяем, что повторный лайк возвращает существующий
        like2 = repository.like_post(post.id, user_id=2)
        assert like2.id == like.id

    def test_view_post(self, repository):
        """Тест просмотра поста"""
        # Создаем пост
        post = repository.create_post(
            title="Test Post",
            description="Test Description",
            creator_id=1
        )

        # Просматриваем пост
        view = repository.view_post(post.id, user_id=2)
        assert view is not None
        assert view.post_id == post.id
        assert view.user_id == 2

    def test_add_comment(self, repository):
        """Тест добавления комментария"""
        # Создаем пост
        post = repository.create_post(
            title="Test Post",
            description="Test Description",
            creator_id=1
        )

        # Добавляем комментарий
        comment = repository.add_comment(
            post_id=post.id,
            user_id=2,
            text="Great post!"
        )
        assert comment is not None
        assert comment.post_id == post.id
        assert comment.user_id == 2
        assert comment.text == "Great post!"

    def test_get_post_comments(self, repository):
        """Тест получения комментариев с пагинацией"""
        # Создаем пост
        post = repository.create_post(
            title="Test Post",
            description="Test Description",
            creator_id=1
        )

        # Добавляем несколько комментариев
        for i in range(15):
            repository.add_comment(
                post_id=post.id,
                user_id=2,
                text=f"Comment {i}"
            )

        # Получаем первую страницу
        comments, total, page, page_size = repository.get_post_comments(
            post_id=post.id,
            user_id=1,
            page=1,
            page_size=10
        )

        assert len(comments) == 10
        assert total == 15
        assert page == 1
        assert page_size == 10