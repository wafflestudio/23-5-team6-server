from typing import Annotated, Optional, Union, List

from fastapi import Depends
from asset_management.app.assets.repositories import AssetRepository
from asset_management.app.assets.schemas import AssetCreateRequest, AssetResponse, AssetUpdateRequest
# from asset_management.app.assets.exceptions import (
# )
from asset_management.app.assets.models import Asset

# from asset_management.app.category.services import CategoryService


class AssetService:
    def __init__(
        self,
        asset_repository: Annotated[AssetRepository, Depends()],
    ) -> None:
        self.asset_repository = asset_repository

    def create_asset_for_admin(
        self, admin_club_id: int, asset_request: AssetCreateRequest
    ) -> AssetResponse:
        
        new_asset = Asset(
            name=asset_request.name,
            description=asset_request.description,
            club_id=admin_club_id,
            category_id=asset_request.category_id,
            # category_name=CategoryService.get_category_by_id(asset_request.category_id).name,
            total_quantity=asset_request.quantity,
            available_quantity=asset_request.quantity,
            location=asset_request.location,
        )

        self.asset_repository.create_asset(new_asset)

        return AssetResponse(
            id=new_asset.id,
            name=new_asset.name,
            status=new_asset.status,
            description=new_asset.description,
            club_id=new_asset.club_id,
            category_id=new_asset.category_id,
            category_name=None,  # To be filled if needed
            total_quantity=new_asset.total_quantity,
            available_quantity=new_asset.available_quantity,
            location=new_asset.location,
            created_at=new_asset.created_at,
        )

    def update_asset_for_admin(
        self, admin_club_id: int, asset_id: int, asset_request: AssetUpdateRequest
    ) -> AssetResponse:
        
        asset = self.asset_repository.get_asset_by_id(asset_id)
        if asset is None:
            raise Exception("ItemNotFoundException")  # Replace with proper exception

        updated_asset = self.asset_repository.modify_asset(
            asset,
            name=asset_request.name,
            description=asset_request.description,
            club_id=admin_club_id,
            category_id=asset_request.category_id,
            total_quantity=asset_request.quantity,
            available_quantity=asset_request.quantity,
            location=asset_request.location,
        )

        return AssetResponse(
            id=updated_asset.id,
            name=updated_asset.name,
            description=updated_asset.description,
            club_id=updated_asset.club_id,
            category_id=updated_asset.category_id,
            category_name=None,  # To be filled if needed
            total_quantity=updated_asset.total_quantity,
            available_quantity=updated_asset.available_quantity,
            location=updated_asset.location,
        )

    def delete_asset_for_admin(self, asset_id: int) -> None:

        asset = self.asset_repository.get_asset_by_id(asset_id)
        if asset is None:
            raise Exception("ItemNotFoundException")  # Replace with proper exception
        
        self.asset_repository.delete_asset(asset)

    def list_assets_for_club(self, club_id: int) -> List[AssetResponse]:
        assets = self.asset_repository.get_all_assets_in_club(club_id)
        return [
            AssetResponse(
                id=asset.id,
                name=asset.name,
                status=asset.status,
                description=asset.description,
                club_id=asset.club_id,
                category_id=asset.category_id,
                category_name=None,  # To be filled if needed
                total_quantity=asset.total_quantity,
                available_quantity=asset.available_quantity,
                location=asset.location,
                created_at=asset.created_at,
            )
            for asset in assets
        ]