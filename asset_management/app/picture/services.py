from typing import Annotated, List

from fastapi import Depends, UploadFile, HTTPException
from asset_management.app.picture.repositories import PictureRepository
from asset_management.app.picture.schemas import PictureResponse, PictureCreateRequest
from asset_management.app.picture.models import Picture


class PictureService:
    def __init__(
        self,
        picture_repository: Annotated[PictureRepository, Depends()],
    ) -> None:
        self.picture_repository = picture_repository

    async def upload_picture(
        self, user_id: int, file: UploadFile, picture_request: PictureCreateRequest
    ) -> PictureResponse:
        
        data = await file.read()

        if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise HTTPException(status_code=400, detail="Unsupported image type")

        if len(data) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large")

        if picture_request.is_main:
            self.picture_repository.clear_main_picture_by_asset(picture_request.asset_id)

        new_picture = Picture(
            asset_id=picture_request.asset_id,
            is_main=picture_request.is_main,
            user_id=user_id,
            data=data,
            content_type=file.content_type,
            filename=file.filename or "upload",
            size=len(data)            
        )

        self.picture_repository.create_picture(new_picture)

        return PictureResponse(
            id=new_picture.id,
            date=new_picture.date,
            asset_id=new_picture.asset_id,
            is_main=new_picture.is_main,
            user_id=new_picture.user_id,
            content_type=new_picture.content_type,
            filename=new_picture.filename,
            size=new_picture.size,
        )

    def get_picture(self, picture_id: int) -> PictureResponse:
        picture = self.picture_repository.get_picture_by_id(picture_id)
        if picture is None:
            raise HTTPException(status_code=404, detail="Picture not found")

        return PictureResponse(
            id=picture.id,
            date=picture.date,
            asset_id=picture.asset_id,
            is_main=picture.is_main,
            user_id=picture.user_id,
            content_type=picture.content_type,
            filename=picture.filename,
            size=picture.size,
        )
    
    def get_picture_model(self, picture_id: int) -> Picture:
        picture = self.picture_repository.get_picture_by_id(picture_id)
        if picture is None:
            raise HTTPException(status_code=404, detail="Picture not found")
        return picture


    def delete_picture(self, picture_id: int) -> None:

        picture = self.picture_repository.get_picture_by_id(picture_id)
        if picture is None:
            raise HTTPException(status_code=404, detail="Picture not found")
        
        self.picture_repository.delete_picture(picture)

    def list_pictures_by_asset(self, asset_id: int) -> List[PictureResponse]:
        pictures = self.picture_repository.get_pictures_by_asset(asset_id)
        return [
            PictureResponse(
                id=picture.id,
                date=picture.date,
                asset_id=picture.asset_id,
                is_main=picture.is_main,
                user_id=picture.user_id,
                content_type=picture.content_type,
                filename=picture.filename,
                size=picture.size,
            )
            for picture in pictures
        ]
    
    def set_main_picture(self, asset_id: int, picture_id: int) -> None:
        picture = self.picture_repository.get_picture_by_id(picture_id)
        if picture is None or picture.asset_id != asset_id:
            raise HTTPException(status_code=404, detail="Picture not found for the given asset")

        self.picture_repository.clear_main_picture_by_asset(asset_id)

        picture.is_main = True
        self.picture_repository.session.commit()

    