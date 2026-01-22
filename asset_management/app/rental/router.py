from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Body, Depends, status
from fastapi import Depends as FastAPIDepends

from asset_management.app.assets.repositories import AssetRepository
from asset_management.app.auth.utils import login_with_header
from asset_management.app.club_member.services import ClubMemberService
from asset_management.app.rental.schemas import (
    RentalBorrowRequest,
    RentalReturnRequest,
    RentalResponse,
)
from asset_management.app.rental.services import RentalService
from asset_management.database.session import get_session

router = APIRouter(prefix="/rentals", tags=["rentals"])


@router.post("/borrow", status_code=status.HTTP_201_CREATED)
def borrow_item(
    request: RentalBorrowRequest,
    rental_service: Annotated[RentalService, Depends()],
    user_id: str = Depends(login_with_header),
) -> RentalResponse:
    """물품 대여
    
    물품을 대여합니다. 대여 가능한 수량이 있는 경우에만 대여가 가능합니다.
    """
    return rental_service.borrow_item(user_id, request.item_id, request.expected_return_date)


@router.post("/{rental_id}/return", status_code=status.HTTP_200_OK)
def return_item(
    rental_id: int,
    rental_service: Annotated[RentalService, Depends()],
    user_id: str = Depends(login_with_header),
    request: Optional[RentalReturnRequest] = Body(default=None),
) -> RentalResponse:
    """물품 반납
    
    대여한 물품을 반납합니다.
    """
    location_lat = request.location_lat if request else None
    location_lng = request.location_lng if request else None
    return rental_service.return_item(
        rental_id=rental_id,
        user_id=user_id,
        location_lat=location_lat,
        location_lng=location_lng,
    )
