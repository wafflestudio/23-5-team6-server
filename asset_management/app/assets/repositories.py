from sqlalchemy import select
from typing import Annotated
from datetime import datetime
from fastapi import Depends
from sqlalchemy.orm import Session
from asset_management.app.assets.models import Asset
from asset_management.app.schedule.models import Schedule, Status
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
    
    def get_asset_status(self, asset_id: int) -> int:
        """Schedule을 기반으로 물품의 대여 상태 반환 (0: 대여 가능, 1: 대여 중)"""
        active_schedule = self.session.query(Schedule).filter(
            Schedule.asset_id == asset_id,
            Schedule.status == Status.IN_USE.value,
        ).first()
        return 1 if active_schedule else 0