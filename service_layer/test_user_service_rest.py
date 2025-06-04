import pytest
import asyncio
import httpx
from sqlalchemy.orm import Session
import sys
import os

sys.path.insert(0, '/app')

from user_service.models import User
from user_service import utils


class TestUserServiceREST:

    @pytest.mark.asyncio
    async def test_create_user_success(self, http_client, user_db_session, sample_user_data):
        """Test 1: Successfully create user via REST API"""
        response = await http_client.post(
            "http://localhost:8001/users/",
            json=sample_user_data
        )

        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == sample_user_data["username"]
        assert data["email"] == sample_user_data["email"]
        assert "id" in data
        assert "created_at" in data

        # Verify database entry
        db_user = user_db_session.query(User).filter(
            User.username == sample_user_data["username"]
        ).first()
        assert db_user is not None
        assert db_user.email == sample_user_data["email"]
        assert utils.verify_password(sample_user_data["password"], db_user.hashed_password)

    @pytest.mark.asyncio
    async def test_login_user_success(self, http_client, user_db_session, sample_user_data):
        """Test 2: Successfully login user via REST API"""
        # First create a user
        hashed_password = utils.get_password_hash(sample_user_data["password"])
        db_user = User(
            username=sample_user_data["username"],
            email=sample_user_data["email"],
            hashed_password=hashed_password
        )
        user_db_session.add(db_user)
        user_db_session.commit()

        # Test login
        login_data = {
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }

        response = await http_client.post(
            "http://localhost:8001/login/",
            json=login_data
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    @pytest.mark.asyncio
    async def test_update_user_profile_success(self, http_client, user_db_session, sample_user_data):
        """Test 3: Successfully update user profile via REST API"""
        # First create a user and get token
        hashed_password = utils.get_password_hash(sample_user_data["password"])
        db_user = User(
            username=sample_user_data["username"],
            email=sample_user_data["email"],
            hashed_password=hashed_password
        )
        user_db_session.add(db_user)
        user_db_session.commit()
        user_id = db_user.id

        # Get access token
        login_response = await http_client.post(
            "http://localhost:8001/login/",
            json={
                "username": sample_user_data["username"],
                "password": sample_user_data["password"]
            }
        )
        token = login_response.json()["access_token"]

        # Update profile
        update_data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+1234567890"
        }

        response = await http_client.put(
            "http://localhost:8001/users/me/",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["phone_number"] == "+1234567890"

        # Verify database update
        user_db_session.refresh(db_user)
        assert db_user.first_name == "John"
        assert db_user.last_name == "Doe"
        assert db_user.phone_number == "+1234567890"