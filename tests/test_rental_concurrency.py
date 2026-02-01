import pytest
from concurrent.futures import ThreadPoolExecutor

def _return_image_file():
    return {"file": ("return.jpg", b"fake-image-bytes", "image/jpeg")}


@pytest.fixture(scope="function")
def admin_club(client, db_session):
    """Create a club with admin via admin signup"""
    admin_signup_payload = {
        "name": "rentaladmin",
        "email": "rentaladmin@example.com",
        "password": "adminpass123",
        "club_name": "Rental Test Club",
        "club_description": "Test club for rentals",
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
    }


@pytest.fixture(scope="function")
def admin_token(client, admin_club):
    """Get authentication token for admin"""
    response = client.post(
        "/api/auth/login",
        json={"email": admin_club["admin_email"], "password": admin_club["admin_password"]},
    )
    assert response.status_code == 200
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
def user_token(client, test_user):
    """Get authentication token for test user"""
    response = client.post(
        "/api/auth/login",
        json={"email": test_user["email"], "password": test_user["password"]},
    )
    assert response.status_code == 200
    return response.json()["tokens"]["access_token"]


@pytest.fixture(scope="function")
def test_asset_one_quantity(client, admin_token, admin_club):
    """Create a test asset with quantity=1 for concurrency tests"""
    asset_payload = {
        "name": "Test Camera (Qty1)",
        "description": "Canon EOS R5",
        "category_id": None,
        "quantity": 1,
        "location": "Storage Room A",
        "club_id": admin_club["club_id"],
    }
    response = client.post(
        "/api/admin/assets",
        json=asset_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201, f"Failed to create asset: {response.text}"
    return response.json()


@pytest.fixture(scope="function")
def user_in_club(client, admin_token, test_user, admin_club):
    """Add test user to the club"""
    payload = {
        "user_id": test_user["id"],
        "club_id": admin_club["club_id"],
        "permission": 0,
    }
    response = client.post(
        "/api/club-members",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    return test_user


@pytest.fixture(scope="function")
def borrowed_rental_id(client, user_token, test_asset_one_quantity, user_in_club):
    """Borrow the item once (API only) to create a rental_id for return concurrency test"""
    response = client.post(
        "/api/rentals/borrow",
        json={"item_id": test_asset_one_quantity["id"]},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_borrow_concurrency_only_one_success_api_only(
    client,
    user_token,
    test_asset_one_quantity,
    user_in_club,
):

    item_id = test_asset_one_quantity["id"]

    def borrow_once():
        return client.post(
            "/api/rentals/borrow",
            json={"item_id": item_id},
            headers={"Authorization": f"Bearer {user_token}"},
        )

    with ThreadPoolExecutor(max_workers=30) as executor:
        responses = list(executor.map(lambda _: borrow_once(), range(30)))

    success = [r for r in responses if r.status_code == 201]
    fail = [r for r in responses if r.status_code == 400]

    assert len(success) == 1
    assert len(fail) == 29


def test_return_concurrency_only_one_success_api_only(
    client,
    user_token,
    test_asset_one_quantity,
    user_in_club,
    borrowed_rental_id,
):

    rental_id = borrowed_rental_id

    def return_once():
        return client.post(
            f"/api/rentals/{rental_id}/return",
            files=_return_image_file(),
            headers={"Authorization": f"Bearer {user_token}"},
        )

    with ThreadPoolExecutor(max_workers=30) as executor:
        responses = list(executor.map(lambda _: return_once(), range(30)))

    success = [r for r in responses if r.status_code == 200]
    fail = [r for r in responses if r.status_code == 400]

    assert len(success) == 1
    assert len(fail) == 29
