import unittest
from unittest.mock import MagicMock
from datetime import datetime
from post_service.app.repository import PostRepository
from post_service.app.models import Post


class TestPostRepository(unittest.TestCase):

    def setUp(self):
        self.db_session = MagicMock()
        self.post_repo = PostRepository(self.db_session)

        self.test_post = Post(
            id=1,
            title="Test Post",
            description="Test Description",
            creator_id=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_private=False,
            tags=["test", "unit"]
        )

    def test_create_post(self):
        self.db_session.add.return_value = None
        self.db_session.commit.return_value = None
        self.db_session.refresh.side_effect = lambda x: setattr(x, 'id', 1)

        title = "Test Post"
        description = "Test Description"
        creator_id = 1
        is_private = False
        tags = ["test", "unit"]

        # Вызов тестируемого метода
        result = self.post_repo.create_post(title, description, creator_id, is_private, tags)

        # Проверки
        self.assertEqual(result.title, title)
        self.assertEqual(result.description, description)
        self.assertEqual(result.creator_id, creator_id)
        self.assertEqual(result.is_private, is_private)
        self.assertEqual(result.tags, tags)
        self.assertEqual(result.id, 1)

        self.db_session.add.assert_called_once()
        self.db_session.commit.assert_called_once()
        self.db_session.refresh.assert_called_once()

    def test_get_post_found(self):       # Тест получения существующего поста
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = self.test_post
        query_mock.filter.return_value = filter_mock
        self.db_session.query.return_value = query_mock

        result = self.post_repo.get_post(1, 1)

        self.assertEqual(result, self.test_post)
        self.db_session.query.assert_called_once()

    def test_get_post_not_found(self):     # Тест получения несуществующего поста
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = None
        query_mock.filter.return_value = filter_mock
        self.db_session.query.return_value = query_mock

        result = self.post_repo.get_post(999, 1)

        self.assertIsNone(result)
        self.db_session.query.assert_called_once()

    def test_get_post_private_no_access(self):   # Тест получения приватного поста без прав доступа
        private_post = Post(
            id=2,
            title="Private Post",
            description="Private Description",
            creator_id=2,  # Другой пользователь
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_private=True,  # Приватный пост
            tags=["private"]
        )

        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = private_post
        query_mock.filter.return_value = filter_mock
        self.db_session.query.return_value = query_mock

        result = self.post_repo.get_post(2, 1)  # Пользователь 1 пытается получить пост пользователя 2

        self.assertIsNone(result)
        self.db_session.query.assert_called_once()

    def test_list_posts(self):       # Тест получения списка постов
        user_id = 1
        page = 1
        page_size = 10

        posts = [self.test_post]
        total = 1

        query_mock = MagicMock()
        filter_mock = MagicMock()
        order_mock = MagicMock()
        offset_mock = MagicMock()
        limit_mock = MagicMock()

        query_mock.filter.return_value = filter_mock
        filter_mock.count.return_value = total
        filter_mock.order_by.return_value = order_mock
        order_mock.offset.return_value = offset_mock
        offset_mock.limit.return_value = limit_mock
        limit_mock.all.return_value = posts

        self.db_session.query.return_value = query_mock

        result_posts, result_total, result_page, result_page_size = self.post_repo.list_posts(user_id, page, page_size)
        self.assertEqual(result_posts, posts)
        self.assertEqual(result_total, total)
        self.assertEqual(result_page, page)
        self.assertEqual(result_page_size, page_size)
        self.db_session.query.assert_called_once()

    def test_update_post_success(self):        # Тест успешного обновления поста
        post_id = 1
        new_title = "Updated Title"
        new_description = "Updated Description"
        creator_id = 1
        is_private = True
        tags = ["updated", "test"]

        post_mock = MagicMock(spec=Post)
        post_mock.id = post_id
        post_mock.creator_id = creator_id

        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = post_mock
        query_mock.filter.return_value = filter_mock
        self.db_session.query.return_value = query_mock

        result = self.post_repo.update_post(post_id, new_title, new_description, creator_id, is_private, tags)

        self.assertEqual(result, post_mock)
        self.assertEqual(post_mock.title, new_title)
        self.assertEqual(post_mock.description, new_description)
        self.assertEqual(post_mock.is_private, is_private)
        self.assertEqual(post_mock.tags, tags)
        self.db_session.commit.assert_called_once()

    def test_update_post_not_found(self):     # Тест обновления несуществующего поста
        post_id = 999
        new_title = "Updated Title"
        new_description = "Updated Description"
        creator_id = 1
        is_private = True
        tags = ["updated", "test"]

        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = None  # Пост не найден
        query_mock.filter.return_value = filter_mock
        self.db_session.query.return_value = query_mock

        result = self.post_repo.update_post(post_id, new_title, new_description, creator_id, is_private, tags)

        self.assertIsNone(result)
        self.db_session.commit.assert_not_called()

    def test_update_post_unauthorized(self):    # Тест обновления поста без прав доступа
        post_id = 1
        new_title = "Updated Title"
        new_description = "Updated Description"
        creator_id = 2  # Другой пользователь
        is_private = True
        tags = ["updated", "test"]

        post_mock = MagicMock(spec=Post)
        post_mock.id = post_id
        post_mock.creator_id = 1  # Настоящий создатель

        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = post_mock
        query_mock.filter.return_value = filter_mock
        self.db_session.query.return_value = query_mock

        result = self.post_repo.update_post(post_id, new_title, new_description, creator_id, is_private, tags)

        self.assertIsNone(result)
        self.db_session.commit.assert_not_called()

    def test_delete_post_success(self):     # Тест успешного удаления поста
        post_id = 1
        creator_id = 1

        post_mock = MagicMock(spec=Post)
        post_mock.id = post_id
        post_mock.creator_id = creator_id

        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = post_mock
        query_mock.filter.return_value = filter_mock
        self.db_session.query.return_value = query_mock

        result = self.post_repo.delete_post(post_id, creator_id)

        self.assertTrue(result)
        self.db_session.delete.assert_called_once_with(post_mock)
        self.db_session.commit.assert_called_once()

    def test_delete_post_not_found(self):  # Тест удаления несуществующего поста

        post_id = 999
        creator_id = 1

        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = None  # Пост не найден
        query_mock.filter.return_value = filter_mock
        self.db_session.query.return_value = query_mock

        result = self.post_repo.delete_post(post_id, creator_id)

        self.assertFalse(result)
        self.db_session.delete.assert_not_called()
        self.db_session.commit.assert_not_called()

    def test_delete_post_unauthorized(self):   # Тест удаления поста без прав доступа

        post_id = 1
        post_creator_id = 1
        user_id = 2  # Другой пользователь

        post_mock = MagicMock(spec=Post)
        post_mock.id = post_id
        post_mock.creator_id = post_creator_id

        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = post_mock
        query_mock.filter.return_value = filter_mock
        self.db_session.query.return_value = query_mock

        result = self.post_repo.delete_post(post_id, user_id)

        self.assertFalse(result)
        self.db_session.delete.assert_not_called()
        self.db_session.commit.assert_not_called()


if __name__ == '__main__':
    unittest.main()