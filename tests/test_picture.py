"""Picture 업로드/조회/목록/대표설정/삭제 기능 테스트"""
import pytest
from io import BytesIO
from fastapi.testclient import TestClient


def _fake_jpeg_bytes() -> bytes:
    """
    간단한 JPEG 헤더 + 더미 데이터.
    실제 디코딩 목적이 아니라 업로드/저장/반환 흐름 테스트용.
    """
    return b"\xFF\xD8\xFF\xE0" + b"JFIF" + b"\x00" * 64 + b"\xFF\xD9"


@pytest.fixture(scope="function")
def admin_club(client: TestClient, db_session):
    """Create a club with admin via admin signup"""
    admin_signup_payload = {
        "name": "pictureadmin",
        "email": "pictureadmin@example.com",
        "password": "adminpass123",
        "club_name": "Picture Test Club",
        "club_description": "Test club for pictures",
        "location_lat": 37_500_000,
        "location_lng": 127_000_000,
    }
    response = client.post(
        "/api/admin/signup",
        json=admin_signup_payload,
    )
    assert response.status_code == 201, response.text
    data = response.json()
    return {
        "club_id": data["club_id"],
        "admin_user_id": data["id"],
        "admin_email": admin_signup_payload["email"],
        "admin_password": admin_signup_payload["password"],
    }


@pytest.fixture(scope="function")
def admin_token(client: TestClient, admin_club):
    """Get authentication token for admin"""
    response = client.post(
        "/api/auth/login",
        json={"email": admin_club["admin_email"], "password": admin_club["admin_password"]},
    )
    assert response.status_code == 200, response.text
    return response.json()["tokens"]["access_token"]


@pytest.fixture(scope="function")
def test_asset(client: TestClient, admin_token: str, admin_club: dict):
    """Create a test asset"""
    asset_payload = {
        "name": "Test Camera",
        "description": "Canon EOS R5",
        "category_id": None,
        "quantity": 3,
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
def uploaded_picture(client: TestClient, admin_token: str, test_asset: dict):
    """Upload a picture and return PictureResponse"""
    files = {
        "file": ("test.jpg", BytesIO(_fake_jpeg_bytes()), "image/jpeg")
    }
    response = client.post(
        f"/api/admin/assets/{test_asset['id']}/pictures",
        files=files,
        params={"is_main": "true"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code in [201, 200], response.text
    data = response.json()
    assert "id" in data
    return data


def test_upload_picture_success(client: TestClient, admin_token: str, test_asset: dict):
    """Test successful picture upload"""
    files = {
        "file": ("test.jpg", BytesIO(_fake_jpeg_bytes()), "image/jpeg")
    }
    response = client.post(
        f"/api/admin/assets/{test_asset['id']}/pictures",
        files=files,
        params={"is_main": "false"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code in [201, 200], response.text
    data = response.json()
    assert data["asset_id"] == test_asset["id"]
    assert data["content_type"].startswith("image/")
    assert data["filename"] == "test.jpg"
    assert data["size"] > 0


def test_upload_picture_unsupported_type(client: TestClient, admin_token: str, test_asset: dict):
    """Test uploading unsupported file type"""
    files = {
        "file": ("test.txt", BytesIO(b"not an image"), "text/plain")
    }
    response = client.post(
        f"/api/admin/assets/{test_asset['id']}/pictures",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400
    assert "Unsupported" in response.json()["detail"] or "지원" in response.json()["detail"]


def test_upload_picture_too_large(client: TestClient, admin_token: str, test_asset: dict):
    """Test uploading oversized image (> 5MB)"""
    big_bytes = b"a" * (5 * 1024 * 1024 + 1)
    files = {
        "file": ("big.jpg", BytesIO(big_bytes), "image/jpeg")
    }
    response = client.post(
        f"/api/admin/assets/{test_asset['id']}/pictures",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400
    assert "large" in response.json()["detail"].lower() or "크" in response.json()["detail"]


def test_upload_picture_without_auth(client: TestClient, test_asset: dict):
    """Test uploading picture without authentication"""
    files = {
        "file": ("test.jpg", BytesIO(_fake_jpeg_bytes()), "image/jpeg")
    }
    response = client.post(
        f"/api/admin/assets/{test_asset['id']}/pictures",
        files=files,
    )
    assert response.status_code == 401


def test_list_asset_pictures(client: TestClient, admin_token: str, test_asset: dict, uploaded_picture: dict):
    """Test listing picture metadata for asset"""
    response = client.get(
        f"/api/assets/{test_asset['id']}/pictures",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code in [200, 401, 403], response.text

    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)
        assert any(item.get("id") == uploaded_picture["id"] for item in data)


def test_get_picture_binary(client: TestClient, uploaded_picture: dict):
    """Test getting picture binary"""
    response = client.get(f"/api/pictures/{uploaded_picture['id']}")
    assert response.status_code == 200, response.text
    assert response.headers.get("content-type", "").startswith("image/")
    assert len(response.content) > 0


def test_get_picture_not_found(client: TestClient):
    """Test getting non-existent picture binary"""
    response = client.get("/api/pictures/99999999")
    assert response.status_code in [404, 422]


def test_set_main_picture(client: TestClient, admin_token: str, test_asset: dict):
    """Test setting main picture"""
    # Upload two pictures (both non-main)
    files1 = {"file": ("a.jpg", BytesIO(_fake_jpeg_bytes()), "image/jpeg")}
    res1 = client.post(
        f"/api/admin/assets/{test_asset['id']}/pictures",
        files=files1,
        params={"is_main": "false"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res1.status_code in [201, 200], res1.text
    pic1_id = res1.json()["id"]

    files2 = {"file": ("b.jpg", BytesIO(_fake_jpeg_bytes()), "image/jpeg")}
    res2 = client.post(
        f"/api/admin/assets/{test_asset['id']}/pictures",
        files=files2,
        params={"is_main": "false"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res2.status_code in [201, 200], res2.text
    pic2_id = res2.json()["id"]

    # Set second as main
    response = client.patch(
        f"/api/admin/assets/{test_asset['id']}/pictures/{pic2_id}/main",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code in [204, 200], response.text

    # Verify via list (if accessible)
    list_res = client.get(
        f"/api/assets/{test_asset['id']}/pictures",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    if list_res.status_code != 200:
        return

    items = list_res.json()
    pic2 = next((x for x in items if x.get("id") == pic2_id), None)
    assert pic2 is not None
    assert pic2.get("is_main") is True

    pic1 = next((x for x in items if x.get("id") == pic1_id), None)
    if pic1 is not None:
        assert pic1.get("is_main") is False


def test_delete_picture_success(client: TestClient, admin_token: str, test_asset: dict):
    """Test deleting picture"""
    # Upload
    files = {"file": ("test.jpg", BytesIO(_fake_jpeg_bytes()), "image/jpeg")}
    upload = client.post(
        f"/api/admin/assets/{test_asset['id']}/pictures",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert upload.status_code in [201, 200], upload.text
    picture_id = upload.json()["id"]

    # Delete
    response = client.delete(
        f"/api/admin/assets/{test_asset['id']}/pictures/{picture_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code in [204, 200], response.text

    # Confirm delete (binary should be 404 or 410)
    get_res = client.get(f"/api/pictures/{picture_id}")
    assert get_res.status_code in [404, 410]


def test_delete_picture_without_auth(client: TestClient, admin_token: str, test_asset: dict):
    """Test deleting picture without authentication"""
    # Upload with admin
    files = {"file": ("test.jpg", BytesIO(_fake_jpeg_bytes()), "image/jpeg")}
    upload = client.post(
        f"/api/admin/assets/{test_asset['id']}/pictures",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert upload.status_code in [201, 200], upload.text
    picture_id = upload.json()["id"]

    # Delete without auth
    response = client.delete(
        f"/api/admin/assets/{test_asset['id']}/pictures/{picture_id}",
    )
    assert response.status_code == 401
