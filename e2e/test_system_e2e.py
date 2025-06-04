import pytest
import asyncio
import httpx
import grpc
import time
import sys
import os

sys.path.insert(0, '/app')

from post_service.generated import posts_pb2, posts_pb2_grpc
from statistics_service.generated import statistics_pb2, statistics_pb2_grpc


class TestSystemE2E:

    @pytest.mark.asyncio
    async def test_full_user_post_lifecycle(self, http_client, grpc_post_channel, grpc_statistics_channel):
        """E2E Test 1: Complete user registration -> post creation -> interaction -> statistics flow"""

        # Step 1: Register user
        user_data = {
            "username": f"testuser_{int(time.time())}",
            "email": f"test_{int(time.time())}@example.com",
            "password": "TestPass123"
        }

        register_response = await http_client.post(
            "http://localhost:8000/users",
            json=user_data
        )
        assert register_response.status_code == 201
        user_id = register_response.json()["id"]

        # Step 2: Login and get token
        login_response = await http_client.post(
            "http://localhost:8000/login",
            json={
                "username": user_data["username"],
                "password": user_data["password"]
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Step 3: Create post
        post_data = {
            "title": "My E2E Test Post",
            "description": "This is a test post for E2E testing",
            "is_private": False,
            "tags": ["test", "e2e"]
        }

        post_response = await http_client.post(
            "http://localhost:8000/posts",
            json=post_data,
            headers=headers
        )
        assert post_response.status_code == 201
        post_id = post_response.json()["id"]

        # Step 4: Like the post
        like_response = await http_client.post(
            f"http://localhost:8000/posts/{post_id}/like",
            headers=headers
        )
        assert like_response.status_code == 200
        assert like_response.json()["success"] is True

        # Step 5: View the post
        view_response = await http_client.post(
            f"http://localhost:8000/posts/{post_id}/view",
            headers=headers
        )
        assert view_response.status_code == 200
        assert view_response.json()["success"] is True

        # Step 6: Add comment
        comment_response = await http_client.post(
            f"http://localhost:8000/posts/{post_id}/comments",
            json={"text": "Great post!"},
            headers=headers
        )
        assert comment_response.status_code == 200

        # Step 7: Wait for Kafka processing
        time.sleep(5)

        # Step 8: Check statistics
        stats_response = await http_client.get(
            f"http://localhost:8002/statistics/posts/{post_id}"
        )
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["post_id"] == post_id
        assert stats["likes_count"] >= 1
        assert stats["views_count"] >= 1
        assert stats["comments_count"] >= 1

    @pytest.mark.asyncio
    async def test_multiple_users_interaction_scenario(self, http_client):
        """E2E Test 2: Multiple users interacting with same post"""

        # Create multiple users
        users = []
        for i in range(3):
            user_data = {
                "username": f"user_{i}_{int(time.time())}",
                "email": f"user_{i}_{int(time.time())}@example.com",
                "password": "TestPass123"
            }

            register_response = await http_client.post(
                "http://localhost:8000/users",
                json=user_data
            )
            assert register_response.status_code == 201

            login_response = await http_client.post(
                "http://localhost:8000/login",
                json={
                    "username": user_data["username"],
                    "password": user_data["password"]
                }
            )
            token = login_response.json()["access_token"]
            users.append({"token": token, "id": register_response.json()["id"]})

        # First user creates a post
        post_data = {
            "title": "Shared Post for Multiple Users",
            "description": "This post will be liked by multiple users",
            "is_private": False,
            "tags": ["shared", "popular"]
        }

        post_response = await http_client.post(
            "http://localhost:8000/posts",
            json=post_data,
            headers={"Authorization": f"Bearer {users[0]['token']}"}
        )
        assert post_response.status_code == 201
        post_id = post_response.json()["id"]

        # All users like and view the post
        for user in users:
            headers = {"Authorization": f"Bearer {user['token']}"}

            # Like
            like_response = await http_client.post(
                f"http://localhost:8000/posts/{post_id}/like",
                headers=headers
            )
            assert like_response.status_code == 200

            # View
            view_response = await http_client.post(
                f"http://localhost:8000/posts/{post_id}/view",
                headers=headers
            )
            assert view_response.status_code == 200

        # Wait for processing
        time.sleep(5)

        # Check statistics
        stats_response = await http_client.get(
            f"http://localhost:8002/statistics/posts/{post_id}"
        )
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["likes_count"] >= 3
        assert stats["views_count"] >= 3

    @pytest.mark.asyncio
    async def test_top_posts_scenario(self, http_client):
        """E2E Test 3: Create posts with different popularity and check top posts"""

        # Create user
        user_data = {
            "username": f"topuser_{int(time.time())}",
            "email": f"topuser_{int(time.time())}@example.com",
            "password": "TestPass123"
        }

        register_response = await http_client.post(
            "http://localhost:8000/users",
            json=user_data
        )
        login_response = await http_client.post(
            "http://localhost:8000/login",
            json={
                "username": user_data["username"],
                "password": user_data["password"]
            }
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create multiple posts
        posts = []
        for i in range(3):
            post_data = {
                "title": f"Post {i} for Top Test",
                "description": f"Description for post {i}",
                "is_private": False,
                "tags": ["top", "test"]
            }

            post_response = await http_client.post(
                "http://localhost:8000/posts",
                json=post_data,
                headers=headers
            )
            posts.append(post_response.json()["id"])

        # Create different numbers of likes for each post
        like_counts = [5, 3, 1]  # Post 0 gets 5 likes, Post 1 gets 3, Post 2 gets 1

        for post_idx, (post_id, like_count) in enumerate(zip(posts, like_counts)):
            for like_idx in range(like_count):
                # Create temporary users for likes
                temp_user = {
                    "username": f"liker_{post_idx}_{like_idx}_{int(time.time())}",
                    "email": f"liker_{post_idx}_{like_idx}_{int(time.time())}@example.com",
                    "password": "TestPass123"
                }

                await http_client.post("http://localhost:8000/users", json=temp_user)
                temp_login = await http_client.post(
                    "http://localhost:8000/login",
                    json={"username": temp_user["username"], "password": temp_user["password"]}
                )
                temp_token = temp_login.json()["access_token"]
                temp_headers = {"Authorization": f"Bearer {temp_token}"}

                # Like the post
                await http_client.post(
                    f"http://localhost:8000/posts/{post_id}/like",
                    headers=temp_headers
                )

                # Wait for Kafka processing
            time.sleep(5)

            # Check top posts
            top_response = await http_client.get(
                "http://localhost:8002/statistics/posts/top?metric=likes&limit=3"
            )
            assert top_response.status_code == 200
            top_posts = top_response.json()["posts"]

            # Verify ordering (most likes first)
            assert len(top_posts) >= 1
            if len(top_posts) >= 2:
                assert top_posts[0]["count"] >= top_posts[1]["count"]