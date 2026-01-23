import csv
from datetime import datetime
from io import StringIO
from typing import Annotated, List

from fastapi import Depends, UploadFile
from asset_management.app.assets.repositories import AssetRepository
from asset_management.app.assets.schemas import AssetCreateRequest, AssetResponse, AssetUpdateRequest
from asset_management.app.assets.models import Asset


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
            status=0,
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
            status=self.asset_repository.get_asset_status(updated_asset.id),
            category_id=updated_asset.category_id,
            category_name=None,  # To be filled if needed
            total_quantity=updated_asset.total_quantity,
            available_quantity=updated_asset.available_quantity,
            location=updated_asset.location,
            created_at=updated_asset.created_at,
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
                status=self.asset_repository.get_asset_status(asset.id),
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
    
    def generate_import_template(self) -> str:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["name", "description", "total_quantity", "available_quantity", "location", "created_at"])
        writer.writerow(["예시 행입니다. 이름은 50자", "설명은 500자","최대 수량","대여 가능 수량", "동아리 내 위치(100자 이하)", "2024-01-01 00:00:00"])
        csv_content = output.getvalue()
        output.close()
        return csv_content
    
    async def import_assets_from_csv(self, club_id: int, file: UploadFile) -> dict:
        contents = await file.read()
        
        csv_data = StringIO(contents.decode("utf-8"))
        reader = csv.DictReader(csv_data)
        failed = []
        imported_count = 0
        for row in reader:
          try:
            self.asset_repository.create_asset(Asset(
              name=row["name"],
              description=row["description"],
              total_quantity=int(row["total_quantity"]),
              available_quantity=int(row["available_quantity"]),
              location=row["location"],
              created_at=datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S"),
              club_id=club_id
            ))
            imported_count += 1
          except Exception:
            failed.append(row)
        return {"imported": imported_count, "failed": failed}
        
        
    
    def export_assets_to_csv(self, club_id: int) -> str:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["name", "description", "total_quantity", "available_quantity", "location", "created_at"])
        assets = self.asset_repository.get_all_assets_in_club(club_id)
        for asset in assets:
            writer.writerow([
                asset.name,
                asset.description,
                asset.total_quantity,
                asset.available_quantity,
                asset.location,
                asset.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            ])
        csv_content = output.getvalue()
        output.close()
        return csv_content