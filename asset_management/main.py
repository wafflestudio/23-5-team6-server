from fastapi import FastAPI

from asset_management.app.user.routes import router as user_router
from asset_management.app.auth.router import router as auth_router

app = FastAPI(title="Asset Management API")


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(user_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
