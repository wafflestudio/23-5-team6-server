from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Header, status, Response
from asset_management.app.assets.schemas import AssetCreateRequest, AssetResponse, AssetUpdateRequest
from asset_management.app.assets.services import AssetService
# from asset_management.app.assets.utils import (
# )

from asset_management.app.auth.dependencies import get_current_user
from asset_management.app.user.models import User

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("/{club_id}", status_code=status.HTTP_200_OK)
def list_assets(
    club_id: int,
    asset_service: AssetService = Depends(AssetService)
) -> list[AssetResponse]:
    assets = asset_service.list_assets_for_club(club_id)
    return assets
