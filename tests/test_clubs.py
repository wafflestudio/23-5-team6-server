def test_club_crud_via_admin_signup(client):
    admin_payload = {
        "name": "Admin User",
        "email": "admin@example.com",
        "password": "strongpassword",
        "club_name": "Waffle Studio",
        "club_description": "Test club",
    }
    signup_response = client.post("/api/admin/signup", json=admin_payload)
    assert signup_response.status_code == 201
    admin_data = signup_response.json()
    club_id = admin_data["club_id"]

    create_response = client.post("/api/clubs", json={"name": "Direct Club"})
    assert create_response.status_code == 405

    list_response = client.get("/api/clubs")
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert isinstance(list_data, list)
    assert any(club["id"] == club_id for club in list_data)

    get_response = client.get(f"/api/clubs/{club_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == admin_payload["club_name"]

    update_payload = {"name": "Updated Club"}
    update_response = client.put(f"/api/clubs/{club_id}", json=update_payload)
    assert update_response.status_code == 200
    assert update_response.json()["name"] == update_payload["name"]

    delete_response = client.delete(f"/api/clubs/{club_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/clubs/{club_id}")
    assert missing_response.status_code == 404


def test_admin_signup_with_custom_club_code(client):
    admin_payload = {
        "name": "Admin Custom",
        "email": "custom_admin@example.com",
        "password": "strongpassword",
        "club_name": "Custom Code Club",
        "club_description": "Test club with custom code",
        "club_code": "CUSTOM1",
    }
    signup_response = client.post("/api/admin/signup", json=admin_payload)
    assert signup_response.status_code == 201
    admin_data = signup_response.json()
    assert admin_data["club_code"] == admin_payload["club_code"]


def test_admin_signup_duplicate_club_code_conflict(client):
    first_payload = {
        "name": "Admin One",
        "email": "admin1@example.com",
        "password": "strongpassword",
        "club_name": "Club One",
        "club_description": "First club",
        "club_code": "DUPLICATE",
    }
    second_payload = {
        "name": "Admin Two",
        "email": "admin2@example.com",
        "password": "strongpassword",
        "club_name": "Club Two",
        "club_description": "Second club",
        "club_code": "DUPLICATE",
    }
    first_response = client.post("/api/admin/signup", json=first_payload)
    assert first_response.status_code == 201

    second_response = client.post("/api/admin/signup", json=second_payload)
    assert second_response.status_code == 409


def test_admin_update_club_code(client):
    admin_payload = {
        "name": "Admin Update",
        "email": "update_admin@example.com",
        "password": "strongpassword",
        "club_name": "Update Code Club",
        "club_description": "Test club for update",
    }
    signup_response = client.post("/api/admin/signup", json=admin_payload)
    assert signup_response.status_code == 201
    admin_data = signup_response.json()
    club_id = admin_data["club_id"]

    login_response = client.post(
        "/api/auth/login",
        json={"email": admin_payload["email"], "password": admin_payload["password"]},
    )
    assert login_response.status_code == 200
    token = login_response.json()["tokens"]["access_token"]

    patch_response = client.patch(
        "/api/admin/club-code",
        json={"club_code": "UPDATED1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["club_code"] == "UPDATED1"

    club_response = client.get(f"/api/clubs/{club_id}")
    assert club_response.status_code == 200
    assert club_response.json()["club_code"] == "UPDATED1"


def test_admin_get_my_club(client):
    admin_payload = {
        "name": "Admin My Club",
        "email": "myclub_admin@example.com",
        "password": "strongpassword",
        "club_name": "My Club",
        "club_description": "Test club for my-club endpoint",
    }
    signup_response = client.post("/api/admin/signup", json=admin_payload)
    assert signup_response.status_code == 201
    admin_data = signup_response.json()

    login_response = client.post(
        "/api/auth/login",
        json={"email": admin_payload["email"], "password": admin_payload["password"]},
    )
    assert login_response.status_code == 200
    token = login_response.json()["tokens"]["access_token"]

    my_club_response = client.get(
        "/api/admin/my-club",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert my_club_response.status_code == 200
    my_club_data = my_club_response.json()
    assert my_club_data["club_id"] == admin_data["club_id"]
    assert my_club_data["club_name"] == admin_data["club_name"]
    assert my_club_data["club_code"] == admin_data["club_code"]
