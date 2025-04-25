import unittest
from unittest.mock import MagicMock, patch
import grpc
from datetime import datetime
from post_service.app.service import PostServicer
from post_service.app.models import Post
from post_service.generated import posts_pb2


class TestPostServicer(unittest.TestCase):

    def setUp(self):
        self.servicer = PostServicer()
        self.db_session = MagicMock()
        self.repo = MagicMock()

        patcher1 = patch('post_service.app.service.SessionLocal', return_value=self.db_session)
        patcher2 = patch('post_service.app.service.PostRepository', return_value=self.repo)

        self.mock_session = patcher1.start()
        self.mock_repo = patcher2.start()

        self.addCleanup(patcher1.stop)
        self.addCleanup(patcher2.stop)

        self.context = MagicMock()  # Мок для gRPC контекста

        # Тестовый пост !!!!!!!!!!!
        self.test_post = MagicMock(spec=Post)
        self.test_post.id = 1
        self.test_post.title = "Test Post"
        self.test_post.description = "Test Description"
        self.test_post.creator_id = 1
        self.test_post.created_at = datetime.now()
        self.test_post.updated_at = datetime.now()
        self.test_post.is_private = False
        self.test_post.tags = ["test", "grpc"]

    def test_create_post(self):                                  # Тест метода создания поста
        self.repo.create_post.return_value = self.test_post

        request = posts_pb2.CreatePostRequest(           # Создаем gRPC запрос!!!!!!!!!!
            title="Test Post",
            description="Test Description",
            creator_id=1,
            is_private=False,
            tags=["test", "grpc"]
        )

        # Вызов тестируемого метода
        response = self.servicer.CreatePost(request, self.context)

        # Проверки
        self.repo.create_post.assert_called_once_with(
            title=request.title,
            description=request.description,
            creator_id=request.creator_id,
            is_private=request.is_private,
            tags=list(request.tags)
        )
        self.assertEqual(response.id, self.test_post.id)
        self.assertEqual(response.title, self.test_post.title)
        self.assertEqual(response.description, self.test_post.description)
        self.assertEqual(response.creator_id, self.test_post.creator_id)

    def test_get_post_success(self):       # успешный пост
        self.repo.get_post.return_value = self.test_post
        request = posts_pb2.GetPostRequest(id=1, user_id=1)      # Создаем gRPC запрос

        # Вызов
        response = self.servicer.GetPost(request, self.context)

        # Проверки
        self.repo.get_post.assert_called_once_with(post_id=request.id, user_id=request.user_id)
        self.assertEqual(response.id, self.test_post.id)
        self.assertEqual(response.title, self.test_post.title)
        self.assertEqual(response.description, self.test_post.description)
        self.context.set_code.assert_not_called()

    def test_get_post_not_found(self):     # Тест получения несуществующего поста
        self.repo.get_post.return_value = None
        request = posts_pb2.GetPostRequest(id=999, user_id=1)
        response = self.servicer.GetPost(request, self.context)

        self.repo.get_post.assert_called_once_with(post_id=request.id, user_id=request.user_id)
        self.context.set_code.assert_called_once_with(grpc.StatusCode.NOT_FOUND)
        self.assertEqual(response, posts_pb2.Post())

    def test_list_posts(self):      # Тест получения списка постов
        posts = [self.test_post]
        total = 1
        page = 1
        page_size = 10

        self.repo.list_posts.return_value = (posts, total, page, page_size)
        request = posts_pb2.ListPostsRequest(user_id=1, page=1, page_size=10)
        response = self.servicer.ListPosts(request, self.context)

        self.repo.list_posts.assert_called_once_with(
            user_id=request.user_id,
            page=request.page,
            page_size=request.page_size
        )
        self.assertEqual(response.total, total)
        self.assertEqual(response.page, page)
        self.assertEqual(response.page_size, page_size)
        self.assertEqual(len(response.posts), 1)

    def test_update_post_success(self):   # Тест успешного обновления поста
        self.repo.update_post.return_value = self.test_post

        request = posts_pb2.UpdatePostRequest(
            id=1,
            title="Updated Title",
            description="Updated Description",
            creator_id=1,
            is_private=True,
            tags=["updated", "test"]
        )

        response = self.servicer.UpdatePost(request, self.context)

        self.repo.update_post.assert_called_once_with(
            post_id=request.id,
            title=request.title,
            description=request.description,
            creator_id=request.creator_id,
            is_private=request.is_private,
            tags=list(request.tags)
        )
        self.assertEqual(response.id, self.test_post.id)
        self.context.set_code.assert_not_called()

    def test_update_post_not_found(self):        # Тест обновления несуществующего поста
        self.repo.update_post.return_value = None

        request = posts_pb2.UpdatePostRequest(
            id=999,
            title="Updated Title",
            description="Updated Description",
            creator_id=1,
            is_private=True,
            tags=["updated", "test"]
        )
        response = self.servicer.UpdatePost(request, self.context)

        self.repo.update_post.assert_called_once()
        self.context.set_code.assert_called_once_with(grpc.StatusCode.NOT_FOUND)
        self.assertEqual(response, posts_pb2.Post())

    def test_update_post_partial_update(self):        # Тест частичного обновления поста
        original_post = MagicMock(spec=Post)
        original_post.id = 1
        original_post.title = "Original Title"
        original_post.description = "Original Description"
        original_post.creator_id = 1
        original_post.created_at = datetime.now()
        original_post.updated_at = datetime.now()
        original_post.is_private = False
        original_post.tags = ["original", "tags"]

        # Настройка обновленного поста
        updated_post = MagicMock(spec=Post)
        updated_post.id = 1
        updated_post.title = "Original Title"  # Не изменяется
        updated_post.description = "Updated Description"  # Изменяется
        updated_post.creator_id = 1
        updated_post.created_at = original_post.created_at
        updated_post.updated_at = datetime.now()
        updated_post.is_private = True  # Изменяется
        updated_post.tags = ["original", "tags"]  # Не изменяется

        self.repo.update_post.return_value = updated_post

        # Запрос с обновлением только описания и флага приватности
        request = posts_pb2.UpdatePostRequest(
            id=1,
            creator_id=1,
            description="Updated Description",
            is_private=True
        )

        response = self.servicer.UpdatePost(request, self.context)
        self.repo.update_post.assert_called_once()
        call_args = self.repo.update_post.call_args[0]
        call_kwargs = self.repo.update_post.call_args[1]

        if len(call_args) >= 1:
            self.assertEqual(call_args[0], 1)  # post_id
        else:
            self.assertEqual(call_kwargs['post_id'], 1)

        if len(call_args) >= 2:
            self.assertEqual(call_args[1], 1)  # creator_id
        else:
            self.assertEqual(call_kwargs['creator_id'], 1)

        if 'title' in call_kwargs:
            self.assertTrue(call_kwargs['title'] is None or call_kwargs['title'] == '')

        self.assertEqual(call_kwargs.get('description', None), "Updated Description")
        self.assertEqual(call_kwargs.get('is_private', None), True)

        self.assertEqual(response.id, updated_post.id)
        self.assertEqual(response.title, "Original Title")
        self.assertEqual(response.description, "Updated Description")
        self.assertTrue(response.is_private)
        self.context.set_code.assert_not_called()

    def test_delete_post_success(self):   # Тест успешного удаления поста
        self.repo.delete_post.return_value = True

        request = posts_pb2.DeletePostRequest(id=1, creator_id=1)
        response = self.servicer.DeletePost(request, self.context)

        self.repo.delete_post.assert_called_once_with(post_id=request.id, creator_id=request.creator_id)
        self.assertTrue(response.success)
        self.context.set_code.assert_not_called()

    def test_delete_post_failure(self):   # Тест неудачного удаления поста
        self.repo.delete_post.return_value = False
        request = posts_pb2.DeletePostRequest(id=999, creator_id=1)
        response = self.servicer.DeletePost(request, self.context)

        self.repo.delete_post.assert_called_once_with(post_id=request.id, creator_id=request.creator_id)
        self.context.set_code.assert_called_once_with(grpc.StatusCode.NOT_FOUND)
        self.assertFalse(response.success)


if __name__ == '__main__':
    unittest.main()
