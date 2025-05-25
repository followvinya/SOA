import pytest
import asyncio
import httpx
from datetime import datetime
import time


class TestStatisticsIntegration:
    """Интеграционные тесты для проверки всей системы"""

    BASE_URL = "http://localhost:8000"
    STATS_URL = "http://localhost:8002"

    async def create_auth_headers(self):
        """Создаем пользователя и получаем токен"""
        async with httpx.AsyncClient() as client:
            user_data = {
                "username": f"test_stats_{datetime.now().timestamp()}",
                "email": f"stats_{datetime.now().timestamp()}@test.com",
                "password": "TestPass123"
            }

            # Создаем пользователя
            await client.post(f"{self.BASE_URL}/users", json=user_data)

            # Логинимся
            login_response = await client.post(
                f"{self.BASE_URL}/login",
                json={"username": user_data["username"], "password": user_data["password"]}
            )

            token = login_response.json()["access_token"]
            return {"Authorization": f"Bearer {token}"}

    @pytest.mark.asyncio
    async def test_full_statistics_flow(self):
        """Тест полного флоу: создание активности и проверка статистики"""
        # Получаем заголовки авторизации
        auth_headers = await self.create_auth_headers()

        async with httpx.AsyncClient() as client:
            # 1. Создаем пост
            post_data = {
                "title": "Test Statistics Post",
                "description": "Testing statistics collection",
                "is_private": False,
                "tags": ["test"]
            }

            post_response = await client.post(
                f"{self.BASE_URL}/posts",
                json=post_data,
                headers=auth_headers
            )
            assert post_response.status_code == 201
            post_id = post_response.json()["id"]

            # 2. Создаем активность
            # Просмотры
            for _ in range(5):
                await client.post(f"{self.BASE_URL}/posts/{post_id}/view", headers=auth_headers)

            # Лайк
            await client.post(f"{self.BASE_URL}/posts/{post_id}/like", headers=auth_headers)

            # Комментарии
            for i in range(3):
                await client.post(
                    f"{self.BASE_URL}/posts/{post_id}/comments",
                    json={"text": f"Test comment {i}"},
                    headers=auth_headers
                )

            # 3. Ждем обработки событий
            await asyncio.sleep(3)

            # 4. Проверяем статистику
            stats_response = await client.get(f"{self.STATS_URL}/statistics/posts/{post_id}")
            assert stats_response.status_code == 200

            stats = stats_response.json()
            assert stats["post_id"] == post_id
            assert stats["views_count"] >= 5
            assert stats["likes_count"] >= 1
            assert stats["comments_count"] >= 3

            # 5. Проверяем динамику
            dynamics_response = await client.get(
                f"{self.STATS_URL}/statistics/posts/{post_id}/views/dynamics"
            )
            assert dynamics_response.status_code == 200

            dynamics = dynamics_response.json()
            assert len(dynamics["daily_stats"]) > 0
            assert dynamics["daily_stats"][0]["count"] >= 5

    @pytest.mark.asyncio
    async def test_top_posts_integration(self):
        """Тест топа постов"""
        # Получаем заголовки авторизации
        auth_headers = await self.create_auth_headers()

        async with httpx.AsyncClient() as client:
            # Создаем несколько постов с разной активностью
            posts = []
            for i in range(3):
                post_response = await client.post(
                    f"{self.BASE_URL}/posts",
                    json={
                        "title": f"Post for top test {i}",
                        "description": "Testing top posts",
                        "is_private": False
                    },
                    headers=auth_headers
                )
                posts.append(post_response.json()["id"])

            # Создаем разное количество просмотров
            for i, post_id in enumerate(posts):
                for _ in range((i + 1) * 2):  # 2, 4, 6 просмотров
                    await client.post(f"{self.BASE_URL}/posts/{post_id}/view", headers=auth_headers)

            # Ждем обработки
            await asyncio.sleep(3)

            # Проверяем топ
            top_response = await client.get(f"{self.STATS_URL}/statistics/posts/top?metric=views")
            assert top_response.status_code == 200

            top_data = top_response.json()
            assert len(top_data["posts"]) > 0

            # Проверяем что посты отсортированы по убыванию
            for i in range(len(top_data["posts"]) - 1):
                assert top_data["posts"][i]["count"] >= top_data["posts"][i + 1]["count"]

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Тест обработки ошибок"""
        async with httpx.AsyncClient() as client:
            # Несуществующий пост
            response = await client.get(f"{self.STATS_URL}/statistics/posts/999999")
            assert response.status_code == 200  # Возвращает пустую статистику

            data = response.json()
            assert data["views_count"] == 0
            assert data["likes_count"] == 0
            assert data["comments_count"] == 0

            # Невалидная метрика
            response = await client.get(f"{self.STATS_URL}/statistics/posts/top?metric=invalid")
            assert response.status_code == 422

            # Без метрики
            response = await client.get(f"{self.STATS_URL}/statistics/posts/top")
            assert response.status_code == 422