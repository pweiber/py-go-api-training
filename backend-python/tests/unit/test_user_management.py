"""
Unit tests for User Management endpoints (Admin operations).
"""

from fastapi.testclient import TestClient

# Standard strong password for tests
STRONG_PASSWORD = "TestPassword123!"


def test_promote_user_to_admin(client):
    """Test that admin can promote user to admin role."""
    from tests.conftest import get_auth_headers

    # Create admin user
    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, "admin")

    # Register a regular user
    response = client.post("/register", json={
        "email": "user@test.com",
        "password": STRONG_PASSWORD
    })
    assert response.status_code == 201
    user_id = response.json()["id"]
    assert response.json()["role"] == "user"

    # Promote user to admin
    response = client.patch(
        f"/users/{user_id}/role",
        json={"role": "admin"},
        headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["role"] == "admin"
    assert data["email"] == "user@test.com"


def test_demote_admin_to_user(client):
    """Test that admin can demote another admin to user role."""
    from tests.conftest import get_auth_headers, create_admin_user

    # Create two admin users
    admin1_headers = get_auth_headers(client, "admin1@test.com", STRONG_PASSWORD, "admin")
    admin2_data = create_admin_user(client, "admin2@test.com", STRONG_PASSWORD)

    # Demote admin2 to user
    response = client.patch(
        f"/users/{admin2_data['id']}/role",
        json={"role": "user"},
        headers=admin1_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == admin2_data["id"]
    assert data["role"] == "user"


def test_cannot_demote_last_admin(client):
    """Test that system prevents demoting the last admin."""
    from tests.conftest import get_auth_headers, create_admin_user

    # Create single admin user using create_admin_user only (no duplicate registration)
    admin_data = create_admin_user(client, "admin@test.com", STRONG_PASSWORD)
    
    # Login as admin
    login_response = client.post("/login", json={
        "email": "admin@test.com",
        "password": STRONG_PASSWORD
    })
    admin_token = login_response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Try to demote the only admin
    response = client.patch(
        f"/users/{admin_data['id']}/role",
        json={"role": "user"},
        headers=admin_headers
    )
    assert response.status_code == 400
    assert "last admin" in response.json()["detail"].lower()


def test_non_admin_cannot_promote_users(client):
    """Test that regular users cannot promote other users."""
    from tests.conftest import get_auth_headers

    # Create regular user
    user_headers = get_auth_headers(client, "user@test.com", STRONG_PASSWORD, "user")

    # Register another user to promote
    response = client.post("/register", json={
        "email": "user2@test.com",
        "password": STRONG_PASSWORD
    })
    user2_id = response.json()["id"]

    # Try to promote as regular user (should fail)
    response = client.patch(
        f"/users/{user2_id}/role",
        json={"role": "admin"},
        headers=user_headers
    )
    assert response.status_code == 403
    assert "admin" in response.json()["detail"].lower()


def test_promote_nonexistent_user(client):
    """Test that promoting non-existent user returns 404."""
    from tests.conftest import get_auth_headers

    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, "admin")

    response = client.patch(
        "/users/99999/role",
        json={"role": "admin"},
        headers=admin_headers
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_promote_without_authentication(client):
    """Test that unauthenticated requests are rejected."""
    # Register a user
    response = client.post("/register", json={
        "email": "user@test.com",
        "password": STRONG_PASSWORD
    })
    user_id = response.json()["id"]

    # Try to promote without auth
    response = client.patch(
        f"/users/{user_id}/role",
        json={"role": "admin"}
    )
    assert response.status_code == 403


def test_list_all_users_as_admin(client):
    """Test that admin can list all users."""
    from tests.conftest import get_auth_headers

    # Create admin
    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, "admin")

    # Create some regular users
    client.post("/register", json={"email": "user1@test.com", "password": STRONG_PASSWORD})
    client.post("/register", json={"email": "user2@test.com", "password": STRONG_PASSWORD})

    # List all users
    response = client.get("/users", headers=admin_headers)
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 3  # admin + 2 regular users
    assert any(u["email"] == "admin@test.com" for u in users)
    assert any(u["email"] == "user1@test.com" for u in users)


def test_list_users_as_regular_user_fails(client):
    """Test that regular users cannot list all users."""
    from tests.conftest import get_auth_headers

    user_headers = get_auth_headers(client, "user@test.com", STRONG_PASSWORD, "user")

    response = client.get("/users", headers=user_headers)
    assert response.status_code == 403


def test_get_user_by_id_as_admin(client):
    """Test that admin can get specific user by ID."""
    from tests.conftest import get_auth_headers

    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, "admin")

    # Create a user
    response = client.post("/register", json={
        "email": "user@test.com",
        "password": STRONG_PASSWORD
    })
    user_id = response.json()["id"]

    # Get user by ID
    response = client.get(f"/users/{user_id}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == "user@test.com"
    assert data["role"] == "user"


def test_get_nonexistent_user_returns_404(client):
    """Test that getting non-existent user returns 404."""
    from tests.conftest import get_auth_headers

    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, "admin")

    response = client.get("/users/99999", headers=admin_headers)
    assert response.status_code == 404
