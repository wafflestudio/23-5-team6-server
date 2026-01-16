from sqlalchemy import select
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from asset_management.app.assets.models import Asset
from asset_management.database.session import get_session



class AssetRepository:
    def __init__(self, session: Annotated[Session, Depends(get_session)]) -> None:
        self.session = session

    def create_asset(self, asset: Asset) -> Asset:
        self.session.add(asset)
        self.session.flush()
        return asset
    
    def get_asset_by_id(self, asset_id: int) -> Asset | None:
        assetLoc = select(Asset).where(Asset.id == asset_id)
        return self.session.scalar(assetLoc)
    
    def get_all_assets_in_club(self, club_id: int) -> list[Asset]:
        assetsLoc = select(Asset).where(Asset.club_id == club_id)
        return self.session.scalars(assetsLoc).all()
    
    def modify_asset(self, asset: Asset, **kwargs) -> Asset:
        for key, value in kwargs.items():
            if value is not None:
                setattr(asset, key, value)
        self.session.flush()

        return asset

    def delete_asset(self, asset: Asset) -> None:
        self.session.delete(asset)
        self.session.flush()