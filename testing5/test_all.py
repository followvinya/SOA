import os
import sys
from datetime import datetime, date, timedelta
sys.path.insert(0, os.path.abspath("."))


def run_simple_tests():
    print(f"=== Starting tests at {datetime.now()} ===\n")
    print("Test 1: Password Utilities")
    try:
        from user_service.utils import get_password_hash, verify_password

        password = "TestPassword123"
        hashed = get_password_hash(password)

        assert hashed != password, "Hash should be different from original password"
        assert verify_password(password, hashed), "Password verification should succeed"
        assert not verify_password("WrongPassword", hashed), "Wrong password should fail"

        print("✅ Password functions work correctly\n")
    except Exception as e:
        print(f"❌ Password test error: {str(e)}\n")

    print("Test 2: Database Connection")
    try:
        from sqlalchemy import text
        from user_service.database import SessionLocal

        db = SessionLocal()
        result = db.execute(text("SELECT 1 as test")).fetchone()
        db.close()

        assert result[0] == 1, "Database query should return 1"
        print("✅ Database connection successful\n")
    except Exception as e:
        print(f"❌ Database connection error: {str(e)}\n")
        print("Make sure your Docker containers are running with 'docker-compose up -d'")
        return

    timestamp = int(datetime.now().timestamp())
    test_username = f"testuser_{timestamp}"
    test_email = f"{test_username}@example.com"


    print("Test 3: User Creation")
    try:
        from user_service.schemas import UserCreate
        from user_service.crud import create_user
        from user_service.database import SessionLocal

        user_data = UserCreate(
            username=test_username,
            email=test_email,
            password="TestPassword123"
        )

        db = SessionLocal()

        user = create_user(db=db, user=user_data)
        assert user.username == test_username, "Created user should have correct username"
        assert user.email == test_email, "Created user should have correct email"
        assert hasattr(user, "hashed_password"), "User should have hashed_password"
        assert hasattr(user, "created_at"), "User should have created_at timestamp"
        print(f"✅ Created test user: {user.username}")

        user_id = user.id
        print(f"✅ User ID: {user_id}")

        db.close()
    except Exception as e:
        print(f"❌ User creation error: {str(e)}\n")
        return

    print("\nTest 4: User Retrieval")
    try:
        from user_service.crud import get_user_by_username, get_user_by_email
        from user_service.database import SessionLocal

        db = SessionLocal()

        user_by_username = get_user_by_username(db=db, username=test_username)
        assert user_by_username is not None, "User should be retrievable by username"
        assert user_by_username.username == test_username, "Retrieved user should have correct username"
        print(f"✅ Retrieved user by username: {user_by_username.username}")

        user_by_email = get_user_by_email(db=db, email=test_email)
        assert user_by_email is not None, "User should be retrievable by email"
        assert user_by_email.email == test_email, "Retrieved user should have correct email"
        print(f"✅ Retrieved user by email: {user_by_email.email}")

        from user_service.models import User
        user_by_id = db.query(User).filter(User.id == user_id).first()
        assert user_by_id is not None, "User should be retrievable by ID"
        assert user_by_id.id == user_id, "Retrieved user should have correct ID"
        print(f"✅ Retrieved user by ID: {user_by_id.id}")

        db.close()
    except Exception as e:
        print(f"❌ User retrieval error: {str(e)}\n")

    print("\nTest 5: Authentication")
    try:
        from user_service.crud import authenticate_user
        from user_service.database import SessionLocal

        db = SessionLocal()

        authenticated_user = authenticate_user(db, test_username, "TestPassword123")
        assert authenticated_user is not False, "Authentication should succeed with correct credentials"
        assert authenticated_user.username == test_username, "Authenticated user should have correct username"
        print(f"✅ Authentication successful with correct credentials")

        wrong_auth = authenticate_user(db, test_username, "WrongPassword")
        assert wrong_auth is False, "Authentication should fail with wrong password"
        print(f"✅ Authentication correctly failed with wrong password")

        nonexistent_auth = authenticate_user(db, "nonexistent_user", "TestPassword123")
        assert nonexistent_auth is False, "Authentication should fail with nonexistent user"
        print(f"✅ Authentication correctly failed with nonexistent user")

        db.close()
    except Exception as e:
        print(f"❌ Authentication test error: {str(e)}\n")

    print("\nTest 6: User Profile Update")
    try:
        from user_service.schemas import UserUpdate
        from user_service.crud import update_user
        from user_service.database import SessionLocal

        db = SessionLocal()

        update_data = UserUpdate(
            first_name="Test",
            last_name="User",
            birth_date=date(1990, 1, 1),
            phone_number="+1234567890"
        )

        updated_user = update_user(db=db, user_id=user_id, user_update=update_data)

        assert updated_user.first_name == "Test", "User first_name should be updated"
        assert updated_user.last_name == "User", "User last_name should be updated"
        assert updated_user.birth_date == date(1990, 1, 1), "User birth_date should be updated"
        assert updated_user.phone_number == "+1234567890", "User phone_number should be updated"

        print(f"✅ User profile updated successfully")

        from user_service.crud import get_user_by_username
        refreshed_user = get_user_by_username(db=db, username=test_username)
        assert refreshed_user.first_name == "Test", "User update should persist in database"

        print(f"✅ User update persisted in database")

        db.close()
    except Exception as e:
        print(f"❌ User update error: {str(e)}\n")

    print("\nTest 7: JWT Token Operations")
    try:
        from user_service.utils import create_access_token
        from jose import jwt
        from user_service.utils import SECRET_KEY, ALGORITHM

        user_data = {"sub": test_username}
        expires = timedelta(minutes=30)
        token = create_access_token(data=user_data, expires_delta=expires)

        assert token is not None, "Token should be generated"
        assert isinstance(token, str), "Token should be a string"
        assert len(token) > 0, "Token should not be empty"
        print(f"✅ Generated access token")

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == test_username, "Token should contain username"
        assert "exp" in payload, "Token should contain expiration"
        print(f"✅ Token validated successfully")

    except Exception as e:
        print(f"❌ Token test error: {str(e)}\n")

    print("\nTest 8: Schema Validation")
    try:
        from user_service.schemas import UserCreate, UserUpdate, UserLogin
        from pydantic import ValidationError

        valid_user = UserCreate(
            username="validuser",
            email="valid@example.com",
            password="ValidPass123"
        )
        assert valid_user.username == "validuser", "Valid user should be created"
        print(f"✅ Valid UserCreate schema accepted")

        valid_login = UserLogin(
            username="validuser",
            password="ValidPass123"
        )
        assert valid_login.username == "validuser", "Valid login should be accepted"
        print(f"✅ Valid UserLogin schema accepted")

        try:
            UserCreate(
                username="invaliduser",
                email="not-an-email",
                password="ValidPass123"
            )
            assert False, "Invalid email should raise ValidationError"
        except ValidationError:
            print(f"✅ Invalid email correctly rejected")

        try:
            UserCreate(
                username="invaliduser",
                email="valid@example.com",
                password="short"
            )
            assert False, "Short password should raise ValidationError"
        except ValidationError:
            print(f"✅ Short password correctly rejected")

        valid_update = UserUpdate(
            first_name="New",
            last_name="Name",
            email="new@example.com"
        )
        assert valid_update.first_name == "New", "Valid update should be accepted"
        print(f"✅ Valid UserUpdate schema accepted")

    except Exception as e:
        print(f"❌ Schema validation error: {str(e)}\n")

    print("\nTest 9: Cleanup")
    try:
        from sqlalchemy import text
        from user_service.database import SessionLocal

        db = SessionLocal()
        db.execute(text(f"DELETE FROM users WHERE username = '{test_username}'"))
        db.commit()

        from user_service.crud import get_user_by_username
        deleted_user = get_user_by_username(db=db, username=test_username)
        assert deleted_user is None, "User should be deleted"

        print(f"✅ Test user deleted successfully")
        db.close()
    except Exception as e:
        print(f"❌ Cleanup error: {str(e)}\n")

    print("\n=== Tests completed ===")


if __name__ == "__main__":
    run_simple_tests()
