import pytest
from unittest.mock import Mock, MagicMock, patch
import grpc
import sys

# Мокируем kafka до импорта
sys.modules['kafka'] = MagicMock()
sys.modules['kafka.errors'] = MagicMock()

# Теперь можем импортировать
from post_service.app.service import PostServicer
from post_service.generated import posts_pb2


class TestPostServicer:

    @pytest.fixture
    def servicer(self):
        return PostServicer()

    @pytest.fixture
    def mock_context(self):
        context = Mock()
        context.set_code = Mock()
        context.set_details = Mock()
        return context

    @patch('post_service.app.service.SessionLocal')
    @patch('post_service.app.service.PostRepository')
    def test_create_post_success(self, mock_repo_class, mock_session, servicer, mock_context):
        """Тест успешного создания поста через gRPC"""
        # Настраиваем моки
        mock_db = Mock()
        mock_session.return_value = mock_db

        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        # Мокаем созданный пост
        mock_post = Mock()
        mock_post.id = 1
        mock_post.title = "Test Title"
        mock_post.description = "Test Description"
        mock_post.creator_id = 1
        mock_post.created_at = Mock()
        mock_post.created_at.isoformat.return_value = "2023-01-01T00:00:00"
        mock_post.updated_at = Mock()
        mock_post.updated_at.isoformat.return_value = "2023-01-01T00:00:00"
        mock_post.is_private = False
        mock_post.tags = ["test"]

        mock_repo.create_post.return_value = mock_post

        # Создаем запрос
        request = posts_pb2.CreatePostRequest(
            title="Test Title",
            description="Test Description",
            creator_id=1,
            is_private=False,
            tags=["test"]
        )

        # Вызываем метод
        response = servicer.CreatePost(request, mock_context)

        # Проверяем результат
        assert response.id == 1
        assert response.title == "Test Title"
        assert response.description == "Test Description"
        assert response.creator_id == 1
        assert response.is_private == False
        assert list(response.tags) == ["test"]