"""
FastAPI 앱 시작 검증 테스트

이 테스트는 앱이 정상적으로 로드되고 시작되는지 확인합니다.
배포 전 CI에서 실행되어 런타임 에러를 미리 잡습니다.
"""
import pytest
from fastapi.testclient import TestClient


class TestAppStartup:
    """앱 시작 및 기본 동작 테스트"""

    def test_app_imports_successfully(self):
        """앱 모듈이 에러 없이 import 되는지 확인"""
        try:
            from asset_management.main import app
            assert app is not None
        except Exception as e:
            pytest.fail(f"앱 import 실패: {e}")

    def test_app_has_routes(self):
        """앱에 라우트가 등록되어 있는지 확인"""
        from asset_management.main import app
        assert len(app.routes) > 0, "등록된 라우트가 없습니다"

    def test_openapi_schema_generates(self):
        """OpenAPI 스키마가 정상 생성되는지 확인"""
        from asset_management.main import app
        schema = app.openapi()
        
        assert "info" in schema
        assert "paths" in schema
        assert schema["info"]["title"] == "Asset Management API"

    def test_health_endpoint_exists(self):
        """헬스체크 엔드포인트가 존재하는지 확인"""
        from asset_management.main import app
        route_paths = [route.path for route in app.routes]
        assert "/health" in route_paths, "/health 엔드포인트가 없습니다"


class TestRouterRegistration:
    """라우터 등록 테스트"""

    def test_all_routers_registered(self):
        """모든 주요 라우터가 등록되어 있는지 확인"""
        from asset_management.main import app
        
        route_paths = [route.path for route in app.routes]
        route_paths_str = " ".join(route_paths)
        
        # 주요 API 프리픽스 확인
        expected_prefixes = [
            "/api/users",
            "/api/auth", 
            "/api/clubs",
            "/api/assets",
            "/api/schedules",
        ]
        
        missing = []
        for prefix in expected_prefixes:
            if prefix not in route_paths_str:
                missing.append(prefix)
        
        if missing:
            pytest.fail(f"누락된 라우터: {missing}")


class TestDependencyImports:
    """의존성 모듈 import 테스트"""

    @pytest.mark.parametrize("module_path", [
        "asset_management.app.user.routes",
        "asset_management.app.user.models",
        "asset_management.app.auth.router",
        "asset_management.app.auth.models",
        "asset_management.app.auth.services",
        "asset_management.app.auth.dependencies",
        "asset_management.app.club.routes",
        "asset_management.app.club.models",
        "asset_management.app.assets.router",
        "asset_management.app.assets.models",
        "asset_management.app.assets.services",
        "asset_management.app.assets.repositories",
        "asset_management.app.schedule.models",
        "asset_management.app.club_member.router",
        "asset_management.app.admin.routes",
        "asset_management.app.category.models",
        "asset_management.database.session",
        "asset_management.database.common",
    ])
    def test_module_imports(self, module_path: str):
        """각 모듈이 에러 없이 import 되는지 확인"""
        import importlib
        try:
            importlib.import_module(module_path)
        except Exception as e:
            pytest.fail(f"{module_path} import 실패: {e}")


class TestPydanticSchemas:
    """Pydantic 스키마 검증 테스트"""

    def test_user_schemas_valid(self):
        """User 스키마가 유효한지 확인"""
        from asset_management.app.user.schemas import UserResponse
        # 스키마 import만 성공해도 기본 검증 통과

    def test_auth_schemas_valid(self):
        """Auth 스키마가 유효한지 확인"""
        from asset_management.app.auth.schemas import TokenResponse

    def test_club_schemas_valid(self):
        """Club 스키마가 유효한지 확인"""
        from asset_management.app.club.schemas import ClubResponse

    def test_asset_schemas_valid(self):
        """Asset 스키마가 유효한지 확인"""
        from asset_management.app.assets.schemas import AssetResponse

    def test_schedule_schemas_valid(self):
        """Schedule 스키마가 유효한지 확인"""
        from asset_management.app.schedule.schemas import ScheduleResponse
