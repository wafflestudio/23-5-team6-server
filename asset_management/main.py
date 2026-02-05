from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from asset_management.app.user.routes import router as user_router
from asset_management.app.auth.router import router as auth_router
from asset_management.app.club.routes import router as club_router
from asset_management.app.club.application_routes import router as club_application_router
from asset_management.app.admin.routes import router as admin_router
from asset_management.app.assets.router import router as asset_router
from asset_management.app.club_member.router import router as club_member_router
from asset_management.app.schedule.router import router as schedule_router
from asset_management.app.rental.router import router as rental_router
from asset_management.app.statistics.router import router as statistics_router
from asset_management.app.picture.router import router as pictuer_router


# 파일 업로드 크기 제한 미들웨어 (10MB)
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB


class LimitUploadSizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > MAX_UPLOAD_SIZE:
                return JSONResponse(
                    status_code=413,
                    content={"detail": f"파일 크기가 너무 큽니다. 최대 {MAX_UPLOAD_SIZE // (1024 * 1024)}MB까지 허용됩니다."}
                )
        return await call_next(request)


app = FastAPI(title="Asset Management API")

# 파일 크기 제한 미들웨어 (가장 먼저 적용)
app.add_middleware(LimitUploadSizeMiddleware)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://d1vqqxs5v1ouxk.cloudfront.net",
                   "http://localhost:5173",
                   "https://baroborrow.p-e.kr",
                   "https://api.baroborrow.p-e.kr",
                   ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(user_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(club_router, prefix="/api")
app.include_router(club_application_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(asset_router, prefix="/api")
app.include_router(club_member_router, prefix="/api")
app.include_router(schedule_router, prefix="/api")
app.include_router(rental_router, prefix="/api")
app.include_router(statistics_router, prefix="/api")
app.include_router(pictuer_router, prefix="/api")
