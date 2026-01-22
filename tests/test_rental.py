import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta


@pytest.fixture(scope="function")
def admin_club(client, db_session):
    """Create a club with admin via admin signup"""
    admin_signup_payload = {
        "name": "rentaladmin",
        "email": "rentaladmin@example.com",
        "password": "adminpass123",
        "club_name": "Rental Test Club",
        "club_description": "Test club for rentals"
    }
    response = client.post(
        "/api/admin/signup",
        json=admin_signup_payload,
    )
    assert response.status_code == 201
    data = response.json()
    return {
        "club_id": data["club_id"],
        "admin_user_id": data["id"],
        "admin_email": admin_signup_payload["email"],
        "admin_password": admin_signup_payload["password"]
    }


@pytest.fixture(scope="function")
def admin_club_with_location(client):
    """Create a club with location via admin signup"""
    admin_signup_payload = {
        "name": "rentaladmin_location",
        "email": "rentaladmin_location@example.com",
        "password": "adminpass123",
        "club_name": "Rental Location Club",
        "club_description": "Test club for rentals with location",
        "location_lat": 37_566_500,
        "location_lng": 126_978_000,
    }
    response = client.post(
        "/api/admin/signup",
        json=admin_signup_payload,
    )
    assert response.status_code == 201
    data = response.json()
    return {
        "club_id": data["club_id"],
        "admin_user_id": data["id"],
        "admin_email": admin_signup_payload["email"],
        "admin_password": admin_signup_payload["password"],
        "location_lat": admin_signup_payload["location_lat"],
        "location_lng": admin_signup_payload["location_lng"],
    }


@pytest.fixture(scope="function")
def admin_token(client, admin_club):
    """Get authentication token for admin"""
    response = client.post(
        "/api/auth/login",
        json={"email": admin_club["admin_email"], "password": admin_club["admin_password"]},
    )
    return response.json()["tokens"]["access_token"]


@pytest.fixture(scope="function")
def admin_token_with_location(client, admin_club_with_location):
    """Get authentication token for admin with club location"""
    response = client.post(
        "/api/auth/login",
        json={
            "email": admin_club_with_location["admin_email"],
            "password": admin_club_with_location["admin_password"],
        },
    )
    return response.json()["tokens"]["access_token"]


@pytest.fixture(scope="function")
def test_user(client, db_session):
    """Create a test user"""
    test_user_data = {
        "name": "rentaluser",
        "email": "rentaluser@example.com",
        "password": "userpass123",
    }
    response = client.post("/api/users/signup", json=test_user_data)
    assert response.status_code == 201
    data = response.json()
    data["password"] = test_user_data["password"]
    return data


@pytest.fixture(scope="function")
def test_user_location(client):
    """Create a test user for location club"""
    test_user_data = {
        "name": "rentaluser_location",
        "email": "rentaluser_location@example.com",
        "password": "userpass123",
    }
    response = client.post("/api/users/signup", json=test_user_data)
    assert response.status_code == 201
    data = response.json()
    data["password"] = test_user_data["password"]
    return data


@pytest.fixture(scope="function")
def user_token(client, test_user):
    """Get authentication token for test user"""
    response = client.post(
        "/api/auth/login",
        json={"email": test_user["email"], "password": test_user["password"]},
    )
    return response.json()["tokens"]["access_token"]


@pytest.fixture(scope="function")
def user_token_location(client, test_user_location):
    """Get authentication token for location test user"""
    response = client.post(
        "/api/auth/login",
        json={"email": test_user_location["email"], "password": test_user_location["password"]},
    )
    return response.json()["tokens"]["access_token"]


@pytest.fixture(scope="function")
def test_asset(client, admin_token, admin_club):
    """Create a test asset"""
    asset_payload = {
        "name": "Test Camera",
        "description": "Canon EOS R5",
        "category_id": None,
        "quantity": 3,
        "location": "Storage Room A",
        "club_id": admin_club["club_id"]
    }
    response = client.post(
        "/api/admin/assets",
        json=asset_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201, f"Failed to create asset: {response.text}"
    return response.json()


@pytest.fixture(scope="function")
def test_asset_with_location(client, admin_token_with_location, admin_club_with_location):
    """Create a test asset for location club"""
    asset_payload = {
        "name": "Test Camera Location",
        "description": "Canon EOS R5",
        "category_id": None,
        "quantity": 3,
        "location": "Storage Room A",
        "club_id": admin_club_with_location["club_id"],
    }
    response = client.post(
        "/api/admin/assets",
        json=asset_payload,
        headers={"Authorization": f"Bearer {admin_token_with_location}"},
    )
    assert response.status_code == 201, f"Failed to create asset: {response.text}"
    return response.json()


@pytest.fixture(scope="function")
def user_in_club(client, admin_token, test_user, admin_club):
    """Add test user to the club"""
    payload = {
        "user_id": test_user["id"],
        "club_id": admin_club["club_id"],
        "permission": 0
    }
    response = client.post(
        "/api/club-members",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    return test_user


@pytest.fixture(scope="function")
def user_in_club_with_location(
    client,
    admin_token_with_location,
    test_user_location,
    admin_club_with_location,
):
    """Add location test user to the location club"""
    payload = {
        "user_id": test_user_location["id"],
        "club_id": admin_club_with_location["club_id"],
        "permission": 0,
    }
    response = client.post(
        "/api/club-members",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token_with_location}"},
    )
    assert response.status_code == 201
    return test_user_location


def test_borrow_item_success(client, user_token, test_asset, user_in_club):
    """Test successful item borrowing"""
    tomorrow = date.today() + timedelta(days=1)
    payload = {
        "item_id": test_asset["id"],
        "expected_return_date": tomorrow.isoformat()
    }
    
    response = client.post(
        "/api/rentals/borrow",
        json=payload,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["item_id"] == test_asset["id"]
    assert data["user_id"] == user_in_club["id"]
    assert data["status"] == "borrowed"
    assert "id" in data
    assert isinstance(data["id"], int)
    assert data["expected_return_date"] == tomorrow.isoformat()
    assert data["returned_at"] is None


def test_borrow_item_without_expected_return_date(client, user_token, test_asset, user_in_club):
    """Test borrowing without expected return date"""
    payload = {
        "item_id": test_asset["id"]
    }
    
    response = client.post(
        "/api/rentals/borrow",
        json=payload,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["item_id"] == test_asset["id"]
    assert data["status"] == "borrowed"


def test_borrow_nonexistent_item(client, user_token, user_in_club):
    """Test borrowing non-existent item"""
    payload = {
        "item_id": 99999
    }
    
    response = client.post(
        "/api/rentals/borrow",
        json=payload,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    
    assert response.status_code == 404
    assert "존재하지 않는 물품 ID" in response.json()["detail"]


def test_borrow_item_no_quantity_available(client, user_token, test_asset, user_in_club, db_session):
    """Test borrowing when no quantity available"""
    # Manually set available_quantity to 0
    from asset_management.app.assets.models import Asset
    Session = db_session
    session = Session()
    try:
        asset = session.query(Asset).filter(Asset.id == test_asset["id"]).first()
        asset.available_quantity = 0
        session.commit()
    finally:
        session.close()
    
    payload = {
        "item_id": test_asset["id"]
    }
    
    response = client.post(
        "/api/rentals/borrow",
        json=payload,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    
    assert response.status_code == 400
    assert "대여 가능한 수량 없음" in response.json()["detail"]


def test_borrow_without_auth(client, test_asset):
    """Test borrowing without authentication"""
    payload = {
        "item_id": test_asset["id"]
    }
    
    response = client.post(
        "/api/rentals/borrow",
        json=payload,
    )
    
    assert response.status_code == 401


def test_return_item_success(client, user_token, test_asset, user_in_club):
    """Test successful item return"""
    # First borrow the item
    borrow_payload = {
        "item_id": test_asset["id"]
    }
    borrow_response = client.post(
        "/api/rentals/borrow",
        json=borrow_payload,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert borrow_response.status_code == 201
    rental_id = borrow_response.json()["id"]
    
    # Then return it
    response = client.post(
        f"/api/rentals/{rental_id}/return",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == rental_id
    assert data["status"] == "returned"
    assert data["returned_at"] is not None


def test_return_requires_location_when_club_has_location(
    client,
    user_token_location,
    test_asset_with_location,
    user_in_club_with_location,
):
    borrow_payload = {
        "item_id": test_asset_with_location["id"]
    }
    borrow_response = client.post(
        "/api/rentals/borrow",
        json=borrow_payload,
        headers={"Authorization": f"Bearer {user_token_location}"},
    )
    assert borrow_response.status_code == 201
    rental_id = borrow_response.json()["id"]

    response = client.post(
        f"/api/rentals/{rental_id}/return",
        headers={"Authorization": f"Bearer {user_token_location}"},
    )
    assert response.status_code == 400
    assert "반납 위치 정보가 필요합니다" in response.json()["detail"]


def test_return_with_location_within_radius_success(
    client,
    user_token_location,
    test_asset_with_location,
    user_in_club_with_location,
    admin_club_with_location,
):
    borrow_payload = {
        "item_id": test_asset_with_location["id"]
    }
    borrow_response = client.post(
        "/api/rentals/borrow",
        json=borrow_payload,
        headers={"Authorization": f"Bearer {user_token_location}"},
    )
    assert borrow_response.status_code == 201
    rental_id = borrow_response.json()["id"]

    response = client.post(
        f"/api/rentals/{rental_id}/return",
        json={
            "location_lat": admin_club_with_location["location_lat"],
            "location_lng": admin_club_with_location["location_lng"],
        },
        headers={"Authorization": f"Bearer {user_token_location}"},
    )
    assert response.status_code == 200


def test_return_nonexistent_rental(client, user_token):
    """Test returning non-existent rental"""
    response = client.post(
        "/api/rentals/99999/return",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    
    assert response.status_code == 404
    assert "존재하지 않는 대여 기록" in response.json()["detail"]


def test_return_invalid_rental_id(client, user_token):
    """Test returning with invalid rental ID format"""
    response = client.post(
        "/api/rentals/invalid-id/return",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    
    # 정수형이 아닌 값은 422 Validation Error 발생
    assert response.status_code == 422


def test_return_other_users_rental(client, user_token, test_asset, user_in_club, admin_token, admin_club):
    """Test that user cannot return another user's rental"""
    # Admin borrows the item
    borrow_payload = {
        "item_id": test_asset["id"]
    }
    borrow_response = client.post(
        "/api/rentals/borrow",
        json=borrow_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert borrow_response.status_code == 201
    rental_id = borrow_response.json()["id"]
    
    # Regular user tries to return admin's rental
    response = client.post(
        f"/api/rentals/{rental_id}/return",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    
    assert response.status_code == 403
    assert "본인이 대여한 물품이 아님" in response.json()["detail"]


def test_return_already_returned_item(client, user_token, test_asset, user_in_club):
    """Test returning an already returned item"""
    # Borrow the item
    borrow_payload = {
        "item_id": test_asset["id"]
    }
    borrow_response = client.post(
        "/api/rentals/borrow",
        json=borrow_payload,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert borrow_response.status_code == 201
    rental_id = borrow_response.json()["id"]
    
    # Return it once
    first_return = client.post(
        f"/api/rentals/{rental_id}/return",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert first_return.status_code == 200
    
    # Try to return again
    second_return = client.post(
        f"/api/rentals/{rental_id}/return",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    
    assert second_return.status_code == 400
    assert "이미 반납된 물품" in second_return.json()["detail"]


def test_return_without_auth(client):
    """Test returning without authentication"""
    response = client.post(
        "/api/rentals/rental-001/return",
    )
    
    assert response.status_code == 401


def test_quantity_decreases_on_borrow(client, user_token, test_asset, user_in_club, db_session):
    """Test that available quantity decreases when item is borrowed"""
    initial_quantity = test_asset["available_quantity"]
    
    # Borrow the item
    payload = {
        "item_id": test_asset["id"]
    }
    response = client.post(
        "/api/rentals/borrow",
        json=payload,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 201
    
    # Check quantity decreased
    from asset_management.app.assets.models import Asset
    Session = db_session
    session = Session()
    try:
        asset = session.query(Asset).filter(Asset.id == test_asset["id"]).first()
        assert asset.available_quantity == initial_quantity - 1
    finally:
        session.close()


def test_quantity_increases_on_return(client, user_token, test_asset, user_in_club, db_session):
    """Test that available quantity increases when item is returned"""
    # Borrow the item
    borrow_payload = {
        "item_id": test_asset["id"]
    }
    borrow_response = client.post(
        "/api/rentals/borrow",
        json=borrow_payload,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert borrow_response.status_code == 201
    rental_id = borrow_response.json()["id"]
    
    # Get quantity after borrow
    from asset_management.app.assets.models import Asset
    Session = db_session
    session = Session()
    try:
        asset = session.query(Asset).filter(Asset.id == test_asset["id"]).first()
        quantity_after_borrow = asset.available_quantity
    finally:
        session.close()
    
    # Return the item
    return_response = client.post(
        f"/api/rentals/{rental_id}/return",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert return_response.status_code == 200
    
    # Check quantity increased
    session = Session()
    try:
        asset = session.query(Asset).filter(Asset.id == test_asset["id"]).first()
        assert asset.available_quantity == quantity_after_borrow + 1
    finally:
        session.close()


def test_multiple_borrows_same_item(client, user_token, test_asset, user_in_club):
    """Test multiple users can borrow the same item if quantity available"""
    # Create another user
    another_user_data = {
        "name": "anotheruser",
        "email": "anotheruser@example.com",
        "password": "password123",
    }
    signup_response = client.post("/api/users/signup", json=another_user_data)
    assert signup_response.status_code == 201, f"Signup failed: {signup_response.text}"
    another_user_id = signup_response.json()["id"]
    
    # Login as another user
    login_response = client.post(
        "/api/auth/login",
        json={"email": another_user_data["email"], "password": another_user_data["password"]},
    )
    another_token = login_response.json()["tokens"]["access_token"]
    
    # First user borrows
    payload = {
        "item_id": test_asset["id"]
    }
    first_borrow = client.post(
        "/api/rentals/borrow",
        json=payload,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert first_borrow.status_code == 201
    
    # Second user borrows (should succeed if quantity > 1)
    second_borrow = client.post(
        "/api/rentals/borrow",
        json=payload,
        headers={"Authorization": f"Bearer {another_token}"},
    )
    
    if test_asset["available_quantity"] > 1:
        assert second_borrow.status_code == 201
        assert second_borrow.json()["user_id"] == another_user_id
    else:
        assert second_borrow.status_code == 400
