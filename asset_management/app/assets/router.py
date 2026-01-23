from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Header, status, Response, File, UploadFile
from asset_management.app.assets.schemas import AssetCreateRequest, AssetResponse, AssetUpdateRequest, ImportResponse
from asset_management.app.assets.services import AssetService
# from asset_management.app.assets.utils import (
# )

from asset_management.app.auth.dependencies import get_current_user
from asset_management.app.user.models import User
import csv

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("/import_template", status_code=status.HTTP_200_OK)
def download_import_template(asset_service: Annotated[AssetService, Depends()]):
  """csv 템플릿 파일을 다운로드합니다."""
  template_content = asset_service.generate_import_template()
  return Response(
    content=template_content,
    media_type="text/csv",
    headers={
      "Content-Disposition": "attachment; filename=asset_import_template.csv"
    }
  )


@router.post("/import")
async def import_assets(
  file: UploadFile,
  user: Annotated[User, Depends(get_current_user)],
  asset_service: Annotated[AssetService, Depends()],
) -> ImportResponse:
  """csv 파일을 통해 자산을 대량으로 등록합니다. (관리자 전용)"""
  if user.is_admin is False:
    raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
  try:
    result = await asset_service.import_assets_from_csv(user.user_clublists[0].club_id, file)
    return ImportResponse(imported=result["imported"], failed=result["failed"])
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/export", status_code=status.HTTP_200_OK)
def export_assets(
  user: Annotated[User, Depends(get_current_user)], asset_service: Annotated[AssetService, Depends()]
):
  """자산 목록을 csv 파일로 내보냅니다.(관리자 전용)"""
  if user.is_admin is False:
    raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
  csv_content = asset_service.export_assets_to_csv(user.user_clublists[0].club_id)
  return Response(
    content=csv_content,
    media_type="text/csv",
    headers={
      "Content-Disposition": f"attachment; filename=asset_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    }
  )


@router.get("/{club_id}", status_code=status.HTTP_200_OK)
def list_assets(club_id: int, asset_service: AssetService = Depends(AssetService)) -> list[AssetResponse]:
  assets = asset_service.list_assets_for_club(club_id)
  return assets
