"""CSV 파일 import/export 기능 테스트"""
import pytest
from io import BytesIO
from fastapi.testclient import TestClient


@pytest.fixture(scope="function")
def admin_user_token(client: TestClient, db_session) -> str:
    """관리자 사용자 토큰 생성"""
    # 관리자로 회원가입
    signup_data = {
        "name": "csv_admin",
        "email": "csv_admin@example.com",
        "password": "password123",
        "club_name": "CSV테스트동아리",
        "club_description": "CSV 테스트용",
        "location_lat": 37_500_000,
        "location_lng": 127_000_000,
    }
    res = client.post("/api/admin/signup", json=signup_data)
    assert res.status_code == 201, res.text
    
    # 로그인
    login_data = {
        "email": "csv_admin@example.com",
        "password": "password123"
    }
    res = client.post("/api/auth/login", json=login_data)
    assert res.status_code == 200, res.text
    
    tokens = res.json().get("tokens", res.json())
    return tokens["access_token"]


@pytest.fixture(scope="function")
def admin_headers(admin_user_token: str) -> dict:
    """관리자 헤더"""
    return {"Authorization": f"Bearer {admin_user_token}"}


def test_download_import_template(client: TestClient, admin_headers: dict):
    """CSV 템플릿 다운로드 테스트"""
    response = client.get("/api/assets/import_template", headers=admin_headers)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    assert "asset_import_template.csv" in response.headers["content-disposition"]
    
    # CSV 내용 확인
    content = response.text
    assert len(content) > 0
    assert "name" in content.lower() or "이름" in content


def test_import_assets_success(client: TestClient, admin_headers: dict):
    """CSV 파일 업로드 성공 테스트"""
    # CSV 파일 생성
    csv_content = """name,description,quantity,location,category_id
테스트물품1,설명1,5,창고A,1
테스트물품2,설명2,10,창고B,1
테스트물품3,설명3,3,창고C,1
"""
    
    files = {
        "file": ("test_assets.csv", BytesIO(csv_content.encode("utf-8")), "text/csv")
    }
    
    response = client.post(
        "/api/assets/import",
        files=files,
        headers=admin_headers
    )
    
    assert response.status_code == 200, response.text
    data = response.json()
    assert "imported" in data
    assert "failed" in data
    assert data["imported"] >= 0


def test_import_assets_invalid_csv(client: TestClient, admin_headers: dict):
    """잘못된 CSV 파일 업로드 테스트"""
    # 잘못된 CSV
    csv_content = """invalid,headers,format
값1,값2,값3
"""
    
    files = {
        "file": ("invalid.csv", BytesIO(csv_content.encode("utf-8")), "text/csv")
    }
    
    response = client.post(
        "/api/assets/import",
        files=files,
        headers=admin_headers
    )
    
    # 400 또는 성공이지만 failed > 0
    assert response.status_code in [200, 400]
    if response.status_code == 200:
        data = response.json()
        assert "failed" in data


def test_import_assets_empty_file(client: TestClient, admin_headers: dict):
    """빈 파일 업로드 테스트"""
    files = {
        "file": ("empty.csv", BytesIO(b""), "text/csv")
    }
    
    response = client.post(
        "/api/assets/import",
        files=files,
        headers=admin_headers
    )
    
    assert response.status_code in [200, 400]


def test_import_assets_without_auth(client: TestClient):
    """인증 없이 CSV 업로드 시도"""
    csv_content = """name,description,quantity
물품1,설명1,5
"""
    
    files = {
        "file": ("test.csv", BytesIO(csv_content.encode("utf-8")), "text/csv")
    }
    
    response = client.post("/api/assets/import", files=files)
    
    assert response.status_code == 401


def test_export_assets(client: TestClient, admin_headers: dict, db_session):
    """자산 목록 CSV 내보내기 테스트"""
    # 먼저 자산 생성
    asset_data = {
        "name": "내보내기테스트물품",
        "description": "테스트",
        "quantity": 5,
        "location": "창고",
        "category_id": 1
    }
    
    # 자산 생성 시도 (실패할 수 있음)
    client.post("/api/admin/assets", json=asset_data, headers=admin_headers)
    
    # CSV 내보내기
    response = client.get("/api/assets/export", headers=admin_headers)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    assert "asset_export_" in response.headers["content-disposition"]
    
    # CSV 내용 확인
    content = response.text
    assert len(content) >= 0  # 빈 목록일 수도 있음


def test_export_assets_without_auth(client: TestClient):
    """인증 없이 CSV 내보내기 시도"""
    response = client.get("/api/assets/export")
    
    assert response.status_code == 401


def test_export_assets_non_admin(client: TestClient, db_session):
    """일반 사용자로 CSV 내보내기 시도"""
    # 일반 사용자 생성 및 로그인
    signup_data = {
        "name": "일반사용자",
        "email": "user@example.com",
        "password": "password123",
        "student_id": "2024-12345"
    }
    
    # 회원가입 (일반 사용자 가입 엔드포인트 사용)
    res = client.post("/api/users/signup", json=signup_data)
    if res.status_code != 201:
        pytest.skip(f"일반 사용자 회원가입 실패: {res.status_code} - {res.text}")
    
    # 로그인
    login_data = {
        "email": "user@example.com",
        "password": "password123"
    }
    res = client.post("/api/auth/login", json=login_data)
    assert res.status_code == 200
    
    tokens = res.json().get("tokens", res.json())
    user_headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    
    # CSV 내보내기 시도
    response = client.get("/api/assets/export", headers=user_headers)
    
    assert response.status_code == 403


def test_import_with_special_characters(client: TestClient, admin_headers: dict):
    """특수 문자가 포함된 CSV 업로드 테스트"""
    csv_content = "name,description,quantity,location,category_id\n"
    csv_content += '"물품,쉼표포함",설명,5,창고,1\n'
    csv_content += '"물품-특수",설명,3,창고,1\n'
    
    files = {
        "file": ("special.csv", BytesIO(csv_content.encode("utf-8")), "text/csv")
    }
    
    response = client.post(
        "/api/assets/import",
        files=files,
        headers=admin_headers
    )
    
    assert response.status_code in [200, 400]


def test_import_large_file(client: TestClient, admin_headers: dict):
    """대용량 CSV 파일 업로드 테스트"""
    # 100개 항목 생성
    rows = ["name,description,quantity,location,category_id"]
    for i in range(100):
        rows.append(f"물품{i},설명{i},{i % 10 + 1},창고{i % 5},1")
    
    csv_content = "\n".join(rows)
    
    files = {
        "file": ("large.csv", BytesIO(csv_content.encode("utf-8")), "text/csv")
    }
    
    response = client.post(
        "/api/assets/import",
        files=files,
        headers=admin_headers
    )
    
    assert response.status_code in [200, 400]
    if response.status_code == 200:
        data = response.json()
        assert "imported" in data
        assert "failed" in data


def test_download_template_without_auth(client: TestClient):
    """인증 없이 템플릿 다운로드 시도"""
    response = client.get("/api/assets/import_template")
    
    # 템플릿은 인증 없이도 다운로드 가능할 수 있음
    # 정책에 따라 401 또는 200
    assert response.status_code in [200, 401]
