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


def test_update_club_location(client):
    admin_payload = {
        "name": "Location Admin",
        "email": "location_admin@example.com",
        "password": "strongpassword",
        "club_name": "Location Club",
        "club_description": "Test club for location update",
    }
    signup_response = client.post("/api/admin/signup", json=admin_payload)
    assert signup_response.status_code == 201
    club_id = signup_response.json()["club_id"]

    update_payload = {"location_lat": 3712, "location_lng": 12705}
    update_response = client.put(f"/api/clubs/{club_id}", json=update_payload)
    assert update_response.status_code == 200
    update_data = update_response.json()
    assert update_data["location_lat"] == update_payload["location_lat"]
    assert update_data["location_lng"] == update_payload["location_lng"]

    get_response = client.get(f"/api/clubs/{club_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["location_lat"] == update_payload["location_lat"]
    assert get_data["location_lng"] == update_payload["location_lng"]


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


def test_get_my_clubs_unauthorized(client):
    """인증 없이 /clubs/me 엔드포인트 호출 시 401 에러"""
    response = client.get("/api/clubs/me")
    assert response.status_code == 401


def test_get_my_clubs_single_club(client):
    """사용자가 하나의 클럽에 속한 경우"""
    # 관리자로 가입하여 클럽 생성
    admin_payload = {
        "name": "Test Admin",
        "email": "test_admin@example.com",
        "password": "strongpassword",
        "club_name": "Test Club",
        "club_description": "Test club description",
    }
    signup_response = client.post("/api/admin/signup", json=admin_payload)
    assert signup_response.status_code == 201
    admin_data = signup_response.json()

    # 로그인
    login_response = client.post(
        "/api/auth/login",
        json={"email": admin_payload["email"], "password": admin_payload["password"]},
    )
    assert login_response.status_code == 200
    token = login_response.json()["tokens"]["access_token"]

    # 내 클럽 목록 조회
    my_clubs_response = client.get(
        "/api/clubs/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert my_clubs_response.status_code == 200
    clubs = my_clubs_response.json()
    assert isinstance(clubs, list)
    assert len(clubs) == 1
    assert clubs[0]["id"] == admin_data["club_id"]
    assert clubs[0]["name"] == admin_payload["club_name"]


def test_get_my_clubs_multiple_clubs(client):
    """사용자가 여러 클럽에 속한 경우"""
    # 첫 번째 관리자로 첫 번째 클럽 생성
    admin1_payload = {
        "name": "Admin One",
        "email": "admin1_multi@example.com",
        "password": "strongpassword",
        "club_name": "Club One",
        "club_description": "First club",
    }
    signup1 = client.post("/api/admin/signup", json=admin1_payload)
    assert signup1.status_code == 201
    club1_data = signup1.json()

    # 첫 번째 관리자 로그인
    login1_response = client.post(
        "/api/auth/login",
        json={"email": admin1_payload["email"], "password": admin1_payload["password"]},
    )
    assert login1_response.status_code == 200
    admin1_token = login1_response.json()["tokens"]["access_token"]

    # 두 번째 관리자로 두 번째 클럽 생성
    admin2_payload = {
        "name": "Admin Two",
        "email": "admin2_multi@example.com",
        "password": "strongpassword",
        "club_name": "Club Two",
        "club_description": "Second club",
    }
    signup2 = client.post("/api/admin/signup", json=admin2_payload)
    assert signup2.status_code == 201
    club2_data = signup2.json()

    # 첫 번째 관리자가 두 번째 클럽에 가입 (permission=2는 가입대기 상태)
    join_response = client.post(
        "/api/club-members/",
        json={
            "user_id": club1_data["id"],  # user의 id 사용
            "club_code": club2_data["club_code"],
            "permission": 2
        },
        headers={"Authorization": f"Bearer {admin1_token}"},
    )
    assert join_response.status_code == 201
    
    # 두 번째 관리자가 로그인
    login2_response = client.post(
        "/api/auth/login",
        json={"email": admin2_payload["email"], "password": admin2_payload["password"]},
    )
    assert login2_response.status_code == 200
    admin2_token = login2_response.json()["tokens"]["access_token"]
    
    # 두 번째 클럽의 관리자가 첫 번째 관리자의 가입을 승인 (permission=0으로 변경)
    member_id = join_response.json()["id"]
    approve_response = client.put(
        f"/api/club-members/{member_id}",
        json={"permission": 0},
        headers={"Authorization": f"Bearer {admin2_token}"},
    )
    assert approve_response.status_code == 200

    # 첫 번째 관리자의 클럽 목록 조회 (두 개의 클럽에 속해 있음)
    my_clubs_response = client.get(
        "/api/clubs/me",
        headers={"Authorization": f"Bearer {admin1_token}"},
    )
    assert my_clubs_response.status_code == 200
    clubs = my_clubs_response.json()
    assert isinstance(clubs, list)
    assert len(clubs) == 2
    
    club_ids = [club["id"] for club in clubs]
    assert club1_data["club_id"] in club_ids
    assert club2_data["club_id"] in club_ids
