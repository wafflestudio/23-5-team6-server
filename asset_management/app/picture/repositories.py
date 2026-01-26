from sqlalchemy import select
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from asset_management.app.picture.models import Picture
from asset_management.database.session import get_session



class PictureRepository:
    def __init__(self, session: Annotated[Session, Depends(get_session)]) -> None:
        self.session = session

    def create_picture(self, picture: Picture) -> Picture:
        self.session.add(picture)
        self.session.commit()
        self.session.refresh(picture)
        return picture
    
    def get_picture_by_id(self, picture_id: int) -> Picture | None:
        pictureLoc = select(Picture).where(Picture.id == picture_id)
        return self.session.scalar(pictureLoc)
    
    def get_pictures_by_asset(self, asset_id: int) -> list[Picture]:
        picturesLoc = select(Picture).where(Picture.asset_id == asset_id)
        return self.session.scalars(picturesLoc).all()
    
    def clear_main_picture_by_asset(self, asset_id: int) -> None:
        picturesLoc = select(Picture).where(Picture.asset_id == asset_id, Picture.is_main == True)
        main_pictures = self.session.scalars(picturesLoc).all()
        for pic in main_pictures:
            pic.is_main = False
        self.session.commit()

    def get_main_picture_by_asset(self, asset_id: int) -> Picture | None:
        pictureLoc = select(Picture).where(Picture.asset_id == asset_id, Picture.is_main == True)
        return self.session.scalar(pictureLoc)
    
    def delete_picture(self, picture: Picture) -> None:
        self.session.delete(picture)
        self.session.commit()