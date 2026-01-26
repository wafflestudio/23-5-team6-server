from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Header, status, Response, File, UploadFile
from asset_management.app.picture.services import PictureService

router = APIRouter(prefix="/pictures", tags=["pictures"])

@router.get("/{picture_id}", status_code=status.HTTP_200_OK)
def get_picture(
    picture_id: int,
    picture_service: Annotated[PictureService, Depends()],
) -> Response:
    
    """특정 사진을 가져옵니다."""
    picture = picture_service.get_picture_model(picture_id)
    return Response(
        content=picture.data,
        media_type=picture.content_type,
        headers={
            "Cache-Control": "public, max-age=86400"
        }
    )