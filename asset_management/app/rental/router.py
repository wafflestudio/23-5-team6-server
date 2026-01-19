from typing import Annotated
from datetime import datetime
from fastapi import APIRouter, Depends, status
from asset_management.app.rental.services import RentalService
from asset_management.app.auth.utils import login_with_header
from asset_management.app.rental.schemas import RentalBorrowRequest, RentalResponse
from asset_management.app.club_member.services import ClubMemberService

router = APIRouter(prefix="/rentals", tags=["rentals"])


@router.post("/borrow", status_code=status.HTTP_201_CREATED)
def borrow_item(
    request: RentalBorrowRequest,
    rental_service: Annotated[RentalService, Depends()],
    club_member_service: Annotated[ClubMemberService, Depends()],
    user_id: str = Depends(login_with_header),
) -> RentalResponse:
    """물품 대여
    
    물품을 대여합니다. 대여 가능한 수량이 있는 경우에만 대여가 가능합니다.
    """
    # 물품의 club_id 조회 (asset 조회를 통해)
    from asset_management.app.assets.repositories import AssetRepository
    from asset_management.database.session import get_session
    from fastapi import Depends as FastAPIDepends
    
    # 임시로 club_id를 1로 설정 (실제로는 asset에서 가져와야 함)
    # TODO: asset에서 club_id를 가져오는 로직 추가 필요
    asset_repo = rental_service.asset_repo
    asset = asset_repo.get_asset_by_id(request.item_id)
    club_id = asset.club_id if asset else 1
    
    return rental_service.borrow_item(
        user_id=user_id,
        item_id=request.item_id,
        club_id=club_id,
        expected_return_date=request.expected_return_date,
    )


@router.post("/{rental_id}/return", status_code=status.HTTP_200_OK)
def return_item(
    rental_id: str,
    rental_service: Annotated[RentalService, Depends()],
    user_id: str = Depends(login_with_header),
) -> RentalResponse:
    """물품 반납
    
    대여한 물품을 반납합니다.
    """
    return rental_service.return_item(rental_id=rental_id, user_id=user_id)
