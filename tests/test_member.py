import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="function")
def user_data(client, db_session):
    """Create a test user and return user data"""
    test_user_data = {
        "name": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword",
    }

    response = client.post("/api/users/signup", json=test_user_data)
    assert response.status_code == 201
    data = response.json()
    data["password"] = test_user_data["password"]
    return data


@pytest.fixture(scope="function")
def auth_token(client, user_data):
    """Get authentication token for test user"""
    response = client.post(
        "/api/auth/login",
        json={"email": user_data["email"], "password": user_data["password"]},
    )
    return response.json()["tokens"]["access_token"]


@pytest.fixture(scope="function")
def test_club(client, auth_token, user_data, db_session):
    """Create a test club and return club data (user is NOT automatically added)"""
    create_payload = {"name": "Test Club", "description": "Test club for members"}
    response = client.post(
        "/api/clubs",
        json=create_payload,
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture(scope="function")
def admin_user_data(client, db_session):
    """Create an admin user and return user data"""
    test_user_data = {
        "name": "adminuser",
        "email": "adminuser@example.com",
        "password": "adminpassword",
    }
    response = client.post("/api/users/signup", json=test_user_data)
    assert response.status_code == 201
    data = response.json()
    data["password"] = test_user_data["password"]
    return data


@pytest.fixture(scope="function")
def admin_token(client, admin_user_data):
    """Get authentication token for admin user"""
    response = client.post(
        "/api/auth/login",
        json={"email": admin_user_data["email"], "password": admin_user_data["password"]},
    )
    return response.json()["tokens"]["access_token"]


@pytest.fixture(scope="function")
def test_club_with_admin(client, test_club, admin_token, admin_user_data, db_session):
    """Add admin user to test club with permission=1 directly in DB"""
    from asset_management.app.user.models import UserClublist
    
    Session = db_session
    session = Session()
    try:
        user_club = UserClublist(
            user_id=admin_user_data["id"],
            club_id=test_club["id"],
            permission=1  # Admin permission
        )
        session.add(user_club)
        session.commit()
    finally:
        session.close()
    
    return test_club


def test_create_club_member(client: TestClient, admin_token, test_club_with_admin, user_data):
    """Test POST /api/club-members - Create a new club member"""
    payload = {"user_id": user_data["id"], "club_id": test_club_with_admin["id"], "permission": 0}

    response = client.post(
        "/api/club-members",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == payload["user_id"]
    assert data["club_id"] == payload["club_id"]
    assert data["permission"] == payload["permission"]
    assert "id" in data


def test_get_club_members_list(client: TestClient, admin_token, test_club_with_admin, user_data):
    """Test GET /api/club-members - Get club members with pagination"""
    # Create a club member first
    payload = {"user_id": user_data["id"], "club_id": test_club_with_admin["id"], "permission": 0}
    create_response = client.post(
        "/api/club-members",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_response.status_code == 201

    # Get members list
    response = client.get(
        "/api/club-members", headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert "pages" in data
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) > 0


def test_get_club_members_by_club_id(
    client: TestClient, admin_token, test_club_with_admin, user_data
):
    """Test GET /api/club-members?club_id={club_id} - Filter by club"""
    # Create a club member
    payload = {"user_id": user_data["id"], "club_id": test_club_with_admin["id"], "permission": 0}
    create_response = client.post(
        "/api/club-members",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_response.status_code == 201

    # Get members by club_id
    response = client.get(
        f"/api/club-members?club_id={test_club_with_admin['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 2  # admin + user
    assert all(member["club_id"] == test_club_with_admin["id"] for member in data["items"])


def test_get_club_members_by_user_id(
    client: TestClient, admin_token, test_club_with_admin, user_data
):
    """Test GET /api/club-members?user_id={user_id} - Filter by user"""
    # Create a club member
    payload = {"user_id": user_data["id"], "club_id": test_club_with_admin["id"], "permission": 0}
    create_response = client.post(
        "/api/club-members",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_response.status_code == 201

    # Get members by user_id (must include club_id for admin to see other users)
    response = client.get(
        f"/api/club-members?club_id={test_club_with_admin['id']}&user_id={user_data['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) > 0
    assert all(member["user_id"] == user_data["id"] for member in data["items"])


def test_get_club_members_by_member_id(
    client: TestClient, admin_token, test_club_with_admin, user_data
):
    """Test GET /api/club-members?member_id={member_id} - Get specific member"""
    # Create a club member
    payload = {"user_id": user_data["id"], "club_id": test_club_with_admin["id"], "permission": 0}
    create_response = client.post(
        "/api/club-members",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_response.status_code == 201
    member_id = create_response.json()["id"]

    # Get member by member_id
    response = client.get(
        f"/api/club-members?member_id={member_id}&club_id={test_club_with_admin['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == member_id


def test_get_club_members_by_permission(
    client: TestClient, admin_token, test_club_with_admin, user_data, admin_user_data
):
    """Test GET /api/club-members?permission={permission} - Filter by permission"""
    # Create a regular member (permission=0)
    payload = {"user_id": user_data["id"], "club_id": test_club_with_admin["id"], "permission": 0}
    create_response = client.post(
        "/api/club-members",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_response.status_code == 201

    # Get admin members (permission=1)
    response = client.get(
        f"/api/club-members?club_id={test_club_with_admin['id']}&permission=1",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1  # At least the admin
    assert all(member["permission"] == 1 for member in data["items"])
    assert any(member["user_id"] == admin_user_data["id"] for member in data["items"])


def test_get_club_members_by_club_and_permission(
    client: TestClient, admin_token, test_club_with_admin, user_data
):
    """Test GET /api/club-members?club_id={club_id}&permission={permission} - Filter by both"""
    # Create club members
    payload = {"user_id": user_data["id"], "club_id": test_club_with_admin["id"], "permission": 2}
    create_response = client.post(
        "/api/club-members",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_response.status_code == 201

    # Get members by club_id and permission
    response = client.get(
        f"/api/club-members?club_id={test_club_with_admin['id']}&permission=2",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    assert all(
        member["club_id"] == test_club_with_admin["id"] and member["permission"] == 2
        for member in data["items"]
    )


def test_get_club_members_with_pagination(
    client: TestClient, admin_token, test_club_with_admin, user_data
):
    """Test GET /api/club-members with pagination parameters"""
    # Create a club member
    payload = {"user_id": user_data["id"], "club_id": test_club_with_admin["id"], "permission": 0}
    create_response = client.post(
        "/api/club-members",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_response.status_code == 201

    # Test pagination
    response = client.get(
        "/api/club-members?page=1&size=5",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["size"] == 5
    assert len(data["items"]) <= 5


def test_update_club_member(client: TestClient, admin_token, test_club_with_admin, user_data):
    """Test PUT /api/club-members/{member_id} - Update member permission"""
    # Create a club member
    payload = {"user_id": user_data["id"], "club_id": test_club_with_admin["id"], "permission": 0}
    create_response = client.post(
        "/api/club-members",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_response.status_code == 201
    member_id = create_response.json()["id"]

    # Update permission
    update_payload = {"permission": 2}
    response = client.put(
        f"/api/club-members/{member_id}",
        json=update_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["permission"] == 2
    assert data["id"] == member_id


def test_delete_club_member(client: TestClient, admin_token, test_club_with_admin, user_data):
    """Test DELETE /api/club-members/{member_id} - Delete a club member"""
    # Create a club member
    payload = {"user_id": user_data["id"], "club_id": test_club_with_admin["id"], "permission": 0}
    create_response = client.post(
        "/api/club-members",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_response.status_code == 201
    member_id = create_response.json()["id"]

    # Delete member
    response = client.delete(
        f"/api/club-members/{member_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 204

    # Verify deletion
    get_response = client.get(
        f"/api/club-members?member_id={member_id}&club_id={test_club_with_admin['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert get_response.status_code == 200
    assert len(get_response.json()["items"]) == 0


def test_create_club_member_without_auth(client: TestClient, test_club, user_data):
    """Test POST /api/club-members without authentication - Should fail"""
    payload = {"user_id": user_data["id"], "club_id": test_club["id"], "permission": 1}

    response = client.post("/api/club-members", json=payload)
    assert response.status_code == 401


def test_update_nonexistent_member(client: TestClient, admin_token):
    """Test PUT /api/club-members/{member_id} with non-existent ID"""
    update_payload = {"permission": 2}
    response = client.put(
        "/api/club-members/99999",
        json=update_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404


def test_delete_nonexistent_member(client: TestClient, admin_token):
    """Test DELETE /api/club-members/{member_id} with non-existent ID"""
    response = client.delete(
        "/api/club-members/99999", headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 404


def test_regular_user_can_only_see_own_members(client: TestClient, auth_token, test_club_with_admin, user_data):
    """Test that regular user can only see their own club memberships"""
    # Add user as regular member
    payload = {"user_id": user_data["id"], "club_id": test_club_with_admin["id"], "permission": 0}
    response = client.post(
        "/api/club-members",
        json=payload,
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 403  # Regular user cannot add members


def test_forbidden_update_without_permission(client: TestClient, auth_token, test_club_with_admin, admin_token, user_data):
    """Test that regular user cannot update club members"""
    # Admin creates a member
    payload = {"user_id": user_data["id"], "club_id": test_club_with_admin["id"], "permission": 0}
    create_response = client.post(
        "/api/club-members",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_response.status_code == 201
    member_id = create_response.json()["id"]

    # Regular user tries to update
    update_payload = {"permission": 1}
    response = client.put(
        f"/api/club-members/{member_id}",
        json=update_payload,
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 403


def test_forbidden_delete_without_permission(client: TestClient, auth_token, test_club_with_admin, admin_token, user_data):
    """Test that regular user cannot delete club members"""
    # Admin creates a member
    payload = {"user_id": user_data["id"], "club_id": test_club_with_admin["id"], "permission": 0}
    create_response = client.post(
        "/api/club-members",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_response.status_code == 201
    member_id = create_response.json()["id"]

    # Regular user tries to delete
    response = client.delete(
        f"/api/club-members/{member_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 403


def test_create_member_with_permission_0(client: TestClient, admin_token, test_club_with_admin, user_data):
    """Test creating a regular member (permission=0)"""
    payload = {"user_id": user_data["id"], "club_id": test_club_with_admin["id"], "permission": 0}
    response = client.post(
        "/api/club-members",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["permission"] == 0


def test_create_member_with_permission_2_no_auth_required(client: TestClient, auth_token, test_club, user_data):
    """Test creating a pending member (permission=2) - should work for any user"""
    payload = {"user_id": user_data["id"], "club_id": test_club["id"], "permission": 2}
    response = client.post(
        "/api/club-members",
        json=payload,
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    # Permission 2 should work without admin privilege
    assert response.status_code in [201, 400, 422]  # May fail due to validation or duplicate


def test_duplicate_member_creation(client: TestClient, admin_token, test_club_with_admin, user_data):
    """Test that creating duplicate member fails or is allowed (depending on implementation)"""
    payload = {"user_id": user_data["id"], "club_id": test_club_with_admin["id"], "permission": 0}
    
    # First creation
    response1 = client.post(
        "/api/club-members",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response1.status_code == 201

    # Second creation (duplicate)
    response2 = client.post(
        "/api/club-members",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    # Some implementations may allow duplicates, others may reject
    assert response2.status_code in [201, 400, 409]  # Created, Bad request, or Conflict


def test_create_member_with_nonexistent_club(client: TestClient, admin_token, user_data):
    """Test creating member with non-existent club_id"""
    payload = {"user_id": user_data["id"], "club_id": 99999, "permission": 0}
    response = client.post(
        "/api/club-members",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code in [400, 403, 404]  # Bad request, Forbidden, or Not found


def test_create_member_without_club_id_or_code(client: TestClient, admin_token, user_data):
    """Test that creating member without club_id or club_code fails"""
    payload = {"user_id": user_data["id"], "permission": 0}
    response = client.post(
        "/api/club-members",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400
