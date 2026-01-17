# tests/test_schedules.py
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from asset_management.app.category.models import Category


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
    return {
        "name": "schedule_admin",
        "email": "schedule_admin@example.com",
        "password": "adminpassword123",
        "club_name": "스케줄테스트동아리",
        "club_description": "스케줄 테스트용 동아리 설명",
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
def created_category(db_session, test_db) -> dict:
    """테스트용 카테고리 생성"""
    session = db_session()
    category = Category(name="테스트 카테고리")
    session.add(category)
    session.commit()
    session.refresh(category)
    category_data = {"id": category.id, "name": category.name}
    session.close()
    return category_data


@pytest.fixture(scope="function")
def asset_payload(signed_up_admin: dict, created_category: dict) -> dict:
    return {
        "name": "대여용 물품",
        "description": "스케줄 테스트용 물품",
        "club_id": signed_up_admin["club_id"],
        "category_id": created_category["id"],
        "quantity": 5,
        "location": "동아리방",
    }


@pytest.fixture(scope="function")
def created_asset(
    client: TestClient,
    admin_headers: dict,
    asset_payload: dict,
    signed_up_admin: dict,
) -> dict:
    res = client.post("/api/admin/assets", json=asset_payload, headers=admin_headers)
    assert res.status_code == 201, res.text

    data = res.json()
    assert "id" in data
    return data


@pytest.fixture(scope="function")
def schedule_payload(signed_up_admin: dict, created_asset: dict) -> dict:
    """기본 스케줄 생성 페이로드"""
    start_date = datetime.now() + timedelta(days=1)
    end_date = datetime.now() + timedelta(days=3)
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "asset_id": created_asset["id"],
        "user_id": signed_up_admin["id"],
        "status": "pending",
    }


@pytest.fixture(scope="function")
def created_schedule(
    client: TestClient,
    admin_headers: dict,
    signed_up_admin: dict,
    schedule_payload: dict,
) -> dict:
    """테스트용 스케줄 생성"""
    club_id = signed_up_admin["club_id"]
    res = client.post(
        f"/api/schedules/{club_id}",
        json=schedule_payload,
        headers=admin_headers,
    )
    assert res.status_code == 201, res.text

    data = res.json()
    assert "id" in data
    return data


# ---------------- Tests: 스케줄 생성 ----------------

def test_create_schedule_success(
    client: TestClient,
    admin_headers: dict,
    signed_up_admin: dict,
    schedule_payload: dict,
):
    """스케줄 생성 성공 테스트"""
    club_id = signed_up_admin["club_id"]
    
    res = client.post(
        f"/api/schedules/{club_id}",
        json=schedule_payload,
        headers=admin_headers,
    )
    assert res.status_code == 201, res.text

    data = res.json()
    assert "id" in data
    assert data["asset_id"] == schedule_payload["asset_id"]
    assert data["user_id"] == schedule_payload["user_id"]
    assert data["status"] == schedule_payload["status"]


def test_create_schedule_without_auth(
    client: TestClient,
    signed_up_admin: dict,
    schedule_payload: dict,
):
    """인증 없이 스케줄 생성 시 실패"""
    club_id = signed_up_admin["club_id"]
    
    res = client.post(
        f"/api/schedules/{club_id}",
        json=schedule_payload,
    )
    # 인증 없이는 401 또는 403 에러
    assert res.status_code in [401, 403], res.text


def test_create_schedule_invalid_status(
    client: TestClient,
    admin_headers: dict,
    signed_up_admin: dict,
    created_asset: dict,
):
    """잘못된 status 값으로 스케줄 생성 시 실패"""
    club_id = signed_up_admin["club_id"]
    start_date = datetime.now() + timedelta(days=1)
    end_date = datetime.now() + timedelta(days=3)
    
    invalid_payload = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "asset_id": created_asset["id"],
        "user_id": signed_up_admin["id"],
        "status": "invalid_status",
    }
    
    res = client.post(
        f"/api/schedules/{club_id}",
        json=invalid_payload,
        headers=admin_headers,
    )
    assert res.status_code == 400, res.text


# ---------------- Tests: 스케줄 조회 ----------------

def test_get_schedules_success(
    client: TestClient,
    admin_headers: dict,
    signed_up_admin: dict,
    created_schedule: dict,
):
    """스케줄 목록 조회 성공 테스트"""
    club_id = signed_up_admin["club_id"]
    
    res = client.get(
        f"/api/schedules/{club_id}",
        headers=admin_headers,
    )
    assert res.status_code == 200, res.text

    data = res.json()
    assert "schedules" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert "pages" in data
    assert isinstance(data["schedules"], list)


def test_get_schedules_with_pagination(
    client: TestClient,
    admin_headers: dict,
    signed_up_admin: dict,
    created_schedule: dict,
):
    """페이지네이션이 적용된 스케줄 조회 테스트"""
    club_id = signed_up_admin["club_id"]
    
    res = client.get(
        f"/api/schedules/{club_id}?page=1&size=5",
        headers=admin_headers,
    )
    assert res.status_code == 200, res.text

    data = res.json()
    assert data["page"] == 1
    assert data["size"] == 5


def test_get_schedules_filter_by_status(
    client: TestClient,
    admin_headers: dict,
    signed_up_admin: dict,
    created_schedule: dict,
):
    """상태별 스케줄 필터링 테스트"""
    club_id = signed_up_admin["club_id"]
    
    # pending 상태로 필터링
    res = client.get(
        f"/api/schedules/{club_id}?status=pending",
        headers=admin_headers,
    )
    assert res.status_code == 200, res.text

    data = res.json()
    for schedule in data["schedules"]:
        assert schedule["status"] == "pending"


def test_get_schedules_filter_by_asset_id(
    client: TestClient,
    admin_headers: dict,
    signed_up_admin: dict,
    created_schedule: dict,
    created_asset: dict,
):
    """물품 ID별 스케줄 필터링 테스트"""
    club_id = signed_up_admin["club_id"]
    asset_id = created_asset["id"]
    
    res = client.get(
        f"/api/schedules/{club_id}?asset_id={asset_id}",
        headers=admin_headers,
    )
    assert res.status_code == 200, res.text

    data = res.json()
    for schedule in data["schedules"]:
        assert schedule["asset_id"] == asset_id


def test_get_schedules_filter_by_date_range(
    client: TestClient,
    admin_headers: dict,
    signed_up_admin: dict,
    created_schedule: dict,
):
    """날짜 범위로 스케줄 필터링 테스트"""
    club_id = signed_up_admin["club_id"]
    start_date = datetime.now().isoformat()
    end_date = (datetime.now() + timedelta(days=7)).isoformat()
    
    res = client.get(
        f"/api/schedules/{club_id}?start_date={start_date}&end_date={end_date}",
        headers=admin_headers,
    )
    assert res.status_code == 200, res.text

    data = res.json()
    assert isinstance(data["schedules"], list)


def test_get_schedules_without_auth(
    client: TestClient,
    signed_up_admin: dict,
):
    """인증 없이 스케줄 조회 시 실패"""
    club_id = signed_up_admin["club_id"]
    
    res = client.get(f"/api/schedules/{club_id}")
    assert res.status_code in [401, 403], res.text


# ---------------- Tests: 스케줄 수정 ----------------

def test_update_schedule_status(
    client: TestClient,
    admin_headers: dict,
    created_schedule: dict,
):
    """스케줄 상태 수정 테스트"""
    schedule_id = created_schedule["id"]
    
    update_payload = {
        "status": "approved",
    }
    
    res = client.put(
        f"/api/schedules/{schedule_id}",
        json=update_payload,
        headers=admin_headers,
    )
    assert res.status_code == 200, res.text

    data = res.json()
    assert data["status"] == "approved"


def test_update_schedule_dates(
    client: TestClient,
    admin_headers: dict,
    created_schedule: dict,
):
    """스케줄 날짜 수정 테스트"""
    schedule_id = created_schedule["id"]
    new_start_date = datetime.now() + timedelta(days=5)
    new_end_date = datetime.now() + timedelta(days=7)
    
    update_payload = {
        "start_date": new_start_date.isoformat(),
        "end_date": new_end_date.isoformat(),
    }
    
    res = client.put(
        f"/api/schedules/{schedule_id}",
        json=update_payload,
        headers=admin_headers,
    )
    assert res.status_code == 200, res.text


def test_update_schedule_without_auth(
    client: TestClient,
    created_schedule: dict,
):
    """인증 없이 스케줄 수정 시 실패"""
    schedule_id = created_schedule["id"]
    
    update_payload = {
        "status": "approved",
    }
    
    res = client.put(
        f"/api/schedules/{schedule_id}",
        json=update_payload,
    )
    assert res.status_code in [401, 403], res.text


def test_update_schedule_to_returned(
    client: TestClient,
    admin_headers: dict,
    created_schedule: dict,
):
    """스케줄을 반납 완료 상태로 변경 테스트"""
    schedule_id = created_schedule["id"]
    
    update_payload = {
        "status": "returned",
    }
    
    res = client.put(
        f"/api/schedules/{schedule_id}",
        json=update_payload,
        headers=admin_headers,
    )
    assert res.status_code == 200, res.text

    data = res.json()
    assert data["status"] == "returned"


def test_update_schedule_to_cancelled(
    client: TestClient,
    admin_headers: dict,
    created_schedule: dict,
):
    """스케줄을 취소 상태로 변경 테스트"""
    schedule_id = created_schedule["id"]
    
    update_payload = {
        "status": "cancelled",
    }
    
    res = client.put(
        f"/api/schedules/{schedule_id}",
        json=update_payload,
        headers=admin_headers,
    )
    assert res.status_code == 200, res.text

    data = res.json()
    assert data["status"] == "cancelled"


# ---------------- Tests: 스케줄 삭제 ----------------

def test_delete_schedule_success(
    client: TestClient,
    admin_headers: dict,
    signed_up_admin: dict,
    created_schedule: dict,
):
    """스케줄 삭제 성공 테스트"""
    schedule_id = created_schedule["id"]
    club_id = signed_up_admin["club_id"]
    
    res = client.delete(
        f"/api/schedules/{schedule_id}",
        headers=admin_headers,
    )
    assert res.status_code == 204, res.text

    # 삭제 확인: 스케줄 목록에서 해당 스케줄이 없어야 함
    res = client.get(
        f"/api/schedules/{club_id}",
        headers=admin_headers,
    )
    assert res.status_code == 200, res.text
    
    data = res.json()
    schedule_ids = [s["id"] for s in data["schedules"]]
    assert schedule_id not in schedule_ids


def test_delete_schedule_without_auth(
    client: TestClient,
    created_schedule: dict,
):
    """인증 없이 스케줄 삭제 시 실패"""
    schedule_id = created_schedule["id"]
    
    res = client.delete(f"/api/schedules/{schedule_id}")
    assert res.status_code in [401, 403], res.text


def test_delete_nonexistent_schedule(
    client: TestClient,
    admin_headers: dict,
):
    """존재하지 않는 스케줄 삭제 시 실패"""
    nonexistent_id = 99999
    
    res = client.delete(
        f"/api/schedules/{nonexistent_id}",
        headers=admin_headers,
    )
    # 존재하지 않는 리소스는 404
    assert res.status_code in [403, 404], res.text


# ---------------- Tests: 스케줄 상태 흐름 ----------------

def test_schedule_status_flow_pending_to_approved_to_in_use(
    client: TestClient,
    admin_headers: dict,
    created_schedule: dict,
):
    """스케줄 상태 흐름 테스트: pending -> approved -> in_use"""
    schedule_id = created_schedule["id"]
    
    # pending -> approved
    res = client.put(
        f"/api/schedules/{schedule_id}",
        json={"status": "approved"},
        headers=admin_headers,
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "approved"
    
    # approved -> in_use
    res = client.put(
        f"/api/schedules/{schedule_id}",
        json={"status": "in_use"},
        headers=admin_headers,
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "in_use"


def test_schedule_full_lifecycle(
    client: TestClient,
    admin_headers: dict,
    created_schedule: dict,
):
    """스케줄 전체 라이프사이클 테스트: pending -> approved -> in_use -> returned"""
    schedule_id = created_schedule["id"]
    
    statuses = ["approved", "in_use", "returned"]
    
    for status in statuses:
        res = client.put(
            f"/api/schedules/{schedule_id}",
            json={"status": status},
            headers=admin_headers,
        )
        assert res.status_code == 200, res.text
        assert res.json()["status"] == status


# ---------------- Tests: 여러 스케줄 생성 ----------------

def test_create_multiple_schedules(
    client: TestClient,
    admin_headers: dict,
    signed_up_admin: dict,
    created_asset: dict,
):
    """여러 스케줄 생성 테스트"""
    club_id = signed_up_admin["club_id"]
    
    schedules_to_create = []
    for i in range(3):
        start_date = datetime.now() + timedelta(days=i * 5 + 1)
        end_date = datetime.now() + timedelta(days=i * 5 + 3)
        schedules_to_create.append({
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "asset_id": created_asset["id"],
            "user_id": signed_up_admin["id"],
            "status": "pending",
        })
    
    created_ids = []
    for payload in schedules_to_create:
        res = client.post(
            f"/api/schedules/{club_id}",
            json=payload,
            headers=admin_headers,
        )
        assert res.status_code == 201, res.text
        created_ids.append(res.json()["id"])
    
    # 생성된 스케줄이 목록에 있는지 확인
    res = client.get(
        f"/api/schedules/{club_id}",
        headers=admin_headers,
    )
    assert res.status_code == 200, res.text
    
    data = res.json()
    schedule_ids_in_response = [s["id"] for s in data["schedules"]]
    for created_id in created_ids:
        assert created_id in schedule_ids_in_response
