import pytest
from app.models.user import User, UserRole
from app.core.security import get_password_hash

def test_login_access_token(client, db):
    password = "testpassword123"
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password=get_password_hash(password),
        role=UserRole.WORKER,
        is_active=True
    )
    db.add(user)
    db.commit()

    response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": password}
    )
    
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"

def test_login_incorrect_password(client, db):
    password = "testpassword123"
    user = User(
        email="test2@example.com",
        username="testuser2",
        full_name="Test User 2",
        hashed_password=get_password_hash(password),
        role=UserRole.WORKER,
        is_active=True
    )
    db.add(user)
    db.commit()

    response = client.post(
        "/api/auth/login",
        data={"username": "test2@example.com", "password": "wrongpassword"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"
