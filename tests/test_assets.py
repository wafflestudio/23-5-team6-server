# tests/test_assets.py
import pytest
from fastapi.testclient import TestClient


# ---------------- helpers ----------------

def _extract_access_token(login_json: dict) -> str:
    """
    보통 형태:
      {"tokens": {"access_token": "...", "refresh_token": "..."}, ...}
    예외적으로:
      {"access_token": "..."}
    """
    if isinstance(login_json, dict):
        tokens = login_json.get("tokens")
        if isinstance(tokens, dict) and "access_token" in tokens:
            return tokens["access_token"]
        if "access_token" in login_json:
            return login_json["access_token"]
    raise AssertionError(f"Cannot find access_token in login response: {login_json}")


# ---------------- fixtures ----------------

@pytest.fixture(scope="function")
def admin_signup_payload() -> dict:
    # AdminSignupRequest에 맞춰 작성
    return {
        "name": "admin_user",
        "email": "admin_user@example.com",
        "password": "adminpassword",
        "club_name": "테스트동아리",
        "club_description": "테스트 동아리 설명",
    }


@pytest.fixture(scope="function")
def signed_up_admin(client: TestClient, admin_signup_payload: dict) -> dict:
    res = client.post("/api/admin/signup", json=admin_signup_payload)
    assert res.status_code == 201, res.text

    data = res.json()
    assert "id" in data
    assert data["email"] == admin_signup_payload["email"]
    assert "club_id" in data
    return data


@pytest.fixture(scope="function")
def admin_access_token(client: TestClient, admin_signup_payload: dict, signed_up_admin: dict) -> str:
    res = client.post(
        "/api/auth/login",
        json={"email": admin_signup_payload["email"], "password": admin_signup_payload["password"]},
    )
    assert res.status_code == 200, res.text
    return _extract_access_token(res.json())


@pytest.fixture(scope="function")
def admin_headers(admin_access_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_access_token}"}


@pytest.fixture(scope="function")
def asset_payload() -> dict:
    return {
        "name": "테스트 물품",
        "description": "테스트 설명",
        "category_id": None,
        "quantity": 3,
        "location": "동아리방",
    }


@pytest.fixture(scope="function")
def created_asset(
    client: TestClient,
    admin_headers: dict,
    asset_payload: dict,
    signed_up_admin: dict,  # club 생성 보장
) -> dict:
    res = client.post("/api/admin/assets", json=asset_payload, headers=admin_headers)
    assert res.status_code == 201, res.text

    data = res.json()
    assert "id" in data
    assert data["name"] == asset_payload["name"]
    return data


# ---------------- Tests ----------------

def test_admin_create_asset(
    client: TestClient,
    admin_headers: dict,
    asset_payload: dict,
    signed_up_admin: dict,
):
    res = client.post("/api/admin/assets", json=asset_payload, headers=admin_headers)
    assert res.status_code == 201, res.text

    data = res.json()
    assert "id" in data
    assert data["name"] == asset_payload["name"]

    # club_id는 서버가 current_user 기반으로 붙이는 구조이므로, 응답에 있으면 체크
    if "club_id" in data:
        assert data["club_id"] == signed_up_admin["club_id"]

    if "total_quantity" in data:
        assert data["total_quantity"] == asset_payload["quantity"]
    if "available_quantity" in data:
        assert data["available_quantity"] == asset_payload["quantity"]


def test_public_list_assets_in_club(
    client: TestClient,
    signed_up_admin: dict,
    created_asset: dict,
):
    club_id = signed_up_admin["club_id"]

    res = client.get(f"/api/assets/{club_id}")
    assert res.status_code == 200, res.text

    items = res.json()
    assert isinstance(items, list)
    assert any(i.get("id") == created_asset["id"] for i in items)


def test_admin_update_asset(
    client: TestClient,
    admin_headers: dict,
    signed_up_admin: dict,
    created_asset: dict,
):
    asset_id = created_asset["id"]
    patch_payload = {
        "name": "수정된 물품",
        "quantity": 5,
        "location": "창고",
        # description/category_id는 선택적으로 업데이트
    }

    res = client.patch(f"/api/admin/assets/{asset_id}", json=patch_payload, headers=admin_headers)
    assert res.status_code == 200, res.text

    data = res.json()
    assert data["id"] == created_asset["id"]
    assert data["name"] == patch_payload["name"]

    # update도 service에서 club_id를 admin_club_id로 덮어쓰고 있으니 확인 가능
    if "club_id" in data:
        assert data["club_id"] == signed_up_admin["club_id"]

    if "total_quantity" in data:
        assert data["total_quantity"] == patch_payload["quantity"]
    if "available_quantity" in data:
        assert data["available_quantity"] == patch_payload["quantity"]
    if "location" in data:
        assert data["location"] == patch_payload["location"]


def test_admin_delete_asset(
    client: TestClient,
    admin_headers: dict,
    signed_up_admin: dict,
    created_asset: dict,
):
    asset_id = created_asset["id"]

    res = client.delete(f"/api/admin/assets/{asset_id}", headers=admin_headers)
    assert res.status_code == 204, res.text

    # 삭제 확인: club list에서 빠졌는지
    club_id = signed_up_admin["club_id"]
    res = client.get(f"/api/assets/{club_id}")
    assert res.status_code == 200, res.text
    items = res.json()
    assert all(i.get("id") != asset_id for i in items)
