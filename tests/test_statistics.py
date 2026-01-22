# tests/test_statistics.py
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
        "name": "stats_admin",
        "email": "stats_admin@example.com",
        "password": "adminpassword123",
        "club_name": "통계테스트동아리",
        "club_description": "통계 테스트용 동아리 설명",
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
    category = Category(name="통계 테스트 카테고리")
    session.add(category)
    session.commit()
    session.refresh(category)
    category_data = {"id": category.id, "name": category.name}
    session.close()
    return category_data


@pytest.fixture(scope="function")
def asset_payload(signed_up_admin: dict, created_category: dict) -> dict:
    return {
        "name": "통계용 물품",
        "description": "통계 테스트용 물품",
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
) -> dict:
    res = client.post("/api/admin/assets", json=asset_payload, headers=admin_headers)
    assert res.status_code == 201, res.text
    data = res.json()
    assert "id" in data
    assert data["name"] == asset_payload["name"]
    return data


@pytest.fixture(scope="function")
def user_signup_payload() -> dict:
    return {
        "name": "stats_user",
        "email": "stats_user@example.com",
        "password": "userpassword",
    }


@pytest.fixture(scope="function")
def signed_up_user(client: TestClient, user_signup_payload: dict) -> dict:
    res = client.post("/api/users/signup", json=user_signup_payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert "id" in data
    return data


@pytest.fixture(scope="function")
def user_access_token(client: TestClient, user_signup_payload: dict, signed_up_user: dict) -> str:
    res = client.post(
        "/api/auth/login",
        json={"email": user_signup_payload["email"], "password": user_signup_payload["password"]},
    )
    assert res.status_code == 200, res.text
    return _extract_access_token(res.json())


@pytest.fixture(scope="function")
def user_headers(user_access_token: str) -> dict:
    return {"Authorization": f"Bearer {user_access_token}"}


@pytest.fixture(scope="function")
def user_joined_club(
    client: TestClient,
    user_headers: dict,
    signed_up_admin: dict,
    signed_up_user: dict,
) -> dict:
    """사용자를 동아리에 가입시킴"""
    club_id = signed_up_admin["club_id"]
    # 가입 신청
    res = client.post(f"/api/clubs/{club_id}/apply", headers=user_headers)
    assert res.status_code in [200, 201], res.text
    
    # 관리자가 승인할 수 있도록 정보 반환
    return {
        "club_id": club_id,
        "user_id": signed_up_user["id"]
    }


# ---------------- tests ----------------

def test_get_statistics_for_new_asset(
    client: TestClient,
    created_asset: dict,
):
    """새로 생성된 자산의 통계를 조회하면 기본값으로 초기화되어야 함"""
    asset_id = created_asset["id"]
    
    res = client.get(f"/api/statistics/{asset_id}")
    assert res.status_code == 200, res.text
    
    data = res.json()
    assert data["total_rental_count"] == 0
    assert data["average_rental_duration"] == 0.0
    assert data["recent_rental_count"] == 0
    assert data["recent_avg_duration"] == 0.0
    assert data["unique_borrower_count"] == 0
    assert data["last_borrowed_at"] is None
    assert "last_updated_at" in data


def test_get_statistics_nonexistent_asset(client: TestClient):
    """존재하지 않는 자산의 통계를 조회하면 lazy creation으로 생성됨"""
    res = client.get("/api/statistics/99999")
    # lazy creation이 작동하므로 200이 반환되고, 기본값으로 초기화됨
    assert res.status_code == 200
    data = res.json()
    assert data["total_rental_count"] == 0


def test_statistics_after_single_rental(
    client: TestClient,
    admin_headers: dict,
    user_headers: dict,
    created_asset: dict,
    signed_up_admin: dict,
    signed_up_user: dict,
):
    """1건의 대여 후 통계가 올바르게 계산되는지 확인"""
    asset_id = created_asset["id"]
    club_id = signed_up_admin["club_id"]
    
    # 사용자를 동아리 멤버로 추가
    member_payload = {
        "user_id": signed_up_user["id"],
        "club_id": club_id,
        "permission": 0  # 일반 멤버
    }
    res = client.post("/api/club-members", json=member_payload, headers=admin_headers)
    assert res.status_code == 201, res.text
    
    # 스케줄 생성 (대여)
    start = datetime.now()
    end = start + timedelta(hours=2)  # 2시간 = 7200초
    
    schedule_payload = {
        "asset_id": asset_id,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }
    
    res = client.post(f"/api/schedules/{club_id}", json=schedule_payload, headers=user_headers)
    assert res.status_code == 201, res.text
    
    # 통계 조회
    res = client.get(f"/api/statistics/{asset_id}")
    assert res.status_code == 200, res.text
    
    data = res.json()
    assert data["total_rental_count"] == 1
    assert data["average_rental_duration"] == pytest.approx(7200.0, rel=0.1)  # 2시간
    assert data["recent_rental_count"] == 1
    assert data["recent_avg_duration"] == pytest.approx(7200.0, rel=0.1)
    assert data["unique_borrower_count"] == 1
    assert data["last_borrowed_at"] is not None


def test_statistics_multiple_rentals_same_user(
    client: TestClient,
    admin_headers: dict,
    user_headers: dict,
    created_asset: dict,
    signed_up_admin: dict,
    signed_up_user: dict,
):
    """동일 사용자가 여러 번 대여했을 때 통계 확인"""
    asset_id = created_asset["id"]
    club_id = signed_up_admin["club_id"]
    
    # 사용자를 동아리 멤버로 추가
    member_payload = {
        "user_id": signed_up_user["id"],
        "club_id": club_id,
        "permission": 0  # 일반 멤버
    }
    res = client.post("/api/club-members", json=member_payload, headers=admin_headers)
    assert res.status_code == 201, res.text
    
    # 3번 대여 (1시간, 2시간, 3시간)
    durations = [1, 2, 3]  # hours
    
    for hours in durations:
        start = datetime.now()
        end = start + timedelta(hours=hours)
        
        schedule_payload = {
            "asset_id": asset_id,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }
        
        res = client.post(f"/api/schedules/{club_id}", json=schedule_payload, headers=user_headers)
        assert res.status_code == 201, res.text
    
    # 통계 조회
    res = client.get(f"/api/statistics/{asset_id}")
    assert res.status_code == 200, res.text
    
    data = res.json()
    assert data["total_rental_count"] == 3
    # 평균: (1 + 2 + 3) / 3 = 2시간 = 7200초
    assert data["average_rental_duration"] == pytest.approx(7200.0, rel=0.1)
    assert data["recent_rental_count"] == 3
    assert data["unique_borrower_count"] == 1  # 동일 사용자


def test_statistics_multiple_users(
    client: TestClient,
    admin_headers: dict,
    created_asset: dict,
    signed_up_admin: dict,
):
    """여러 사용자가 대여했을 때 unique_borrower_count 확인"""
    asset_id = created_asset["id"]
    club_id = signed_up_admin["club_id"]
    
    # 3명의 사용자 생성 및 대여
    for i in range(3):
        # 사용자 생성
        user_payload = {
            "name": f"user_{i}",
            "email": f"user_{i}@example.com",
            "password": "password123"
        }
        res = client.post("/api/users/signup", json=user_payload)
        assert res.status_code == 201, res.text
        user_data = res.json()
        
        # 로그인
        res = client.post("/api/auth/login", json={
            "email": user_payload["email"],
            "password": user_payload["password"]
        })
        assert res.status_code == 200, res.text
        token = _extract_access_token(res.json())
        headers = {"Authorization": f"Bearer {token}"}
        
        # 동아리 멤버 추가
        member_payload = {
            "user_id": user_data["id"],
            "club_id": club_id,
            "permission": 0  # 일반 멤버
        }
        res = client.post("/api/club-members", json=member_payload, headers=admin_headers)
        assert res.status_code == 201, res.text
        
        # 스케줄 생성
        start = datetime.now()
        end = start + timedelta(hours=1)
        schedule_payload = {
            "asset_id": asset_id,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }
        res = client.post(f"/api/schedules/{club_id}", json=schedule_payload, headers=headers)
        assert res.status_code == 201, res.text
    
    # 통계 조회
    res = client.get(f"/api/statistics/{asset_id}")
    assert res.status_code == 200, res.text
    
    data = res.json()
    assert data["total_rental_count"] == 3
    assert data["unique_borrower_count"] == 3  # 3명의 다른 사용자


def test_statistics_recent_vs_total(
    client: TestClient,
    admin_headers: dict,
    user_headers: dict,
    created_asset: dict,
    signed_up_admin: dict,
    signed_up_user: dict,
    db_session,
):
    """최근 30일 통계와 전체 통계가 올바르게 분리되는지 확인"""
    asset_id = created_asset["id"]
    club_id = signed_up_admin["club_id"]
    
    # 사용자를 동아리 멤버로 추가
    member_payload = {
        "user_id": signed_up_user["id"],
        "club_id": club_id,
        "permission": 0  # 일반 멤버
    }
    res = client.post("/api/club-members", json=member_payload, headers=admin_headers)
    assert res.status_code == 201, res.text
    
    # DB에 직접 접근하여 과거 스케줄 생성 (35일 전)
    from asset_management.app.schedule.models import Schedule
    
    session = db_session()
    old_schedule = Schedule(
        asset_id=asset_id,
        user_id=signed_up_user["id"],
        club_id=club_id,
        start_date=datetime.now() - timedelta(days=35),
        end_date=datetime.now() - timedelta(days=35) + timedelta(hours=1),
        status="returned"
    )
    session.add(old_schedule)
    session.commit()
    session.close()
    
    # 최근 스케줄 생성 (API 통해)
    start = datetime.now()
    end = start + timedelta(hours=2)
    
    schedule_payload = {
        "asset_id": asset_id,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }
    res = client.post(f"/api/schedules/{club_id}", json=schedule_payload, headers=user_headers)
    assert res.status_code == 201, res.text
    
    # 통계 조회
    res = client.get(f"/api/statistics/{asset_id}")
    assert res.status_code == 200, res.text
    
    data = res.json()
    assert data["total_rental_count"] == 2  # 전체 2건
    assert data["recent_rental_count"] == 1  # 최근 30일은 1건만


def test_statistics_zero_duration(
    client: TestClient,
    admin_headers: dict,
    user_headers: dict,
    created_asset: dict,
    signed_up_admin: dict,
    signed_up_user: dict,
):
    """대여 기간이 0인 경우 (즉시 반납) 처리 확인"""
    asset_id = created_asset["id"]
    club_id = signed_up_admin["club_id"]
    
    # 사용자를 동아리 멤버로 추가
    member_payload = {
        "user_id": signed_up_user["id"],
        "club_id": club_id,
        "permission": 0  # 일반 멤버
    }
    res = client.post("/api/club-members", json=member_payload, headers=admin_headers)
    assert res.status_code == 201, res.text
    
    # 동일 시간으로 스케줄 생성
    now = datetime.now()
    
    schedule_payload = {
        "asset_id": asset_id,
        "start_date": now.isoformat(),
        "end_date": now.isoformat(),
    }
    
    res = client.post(f"/api/schedules/{club_id}", json=schedule_payload, headers=user_headers)
    assert res.status_code == 201, res.text
    
    # 통계 조회
    res = client.get(f"/api/statistics/{asset_id}")
    assert res.status_code == 200, res.text
    
    data = res.json()
    assert data["total_rental_count"] == 1
    assert data["average_rental_duration"] == 0.0
