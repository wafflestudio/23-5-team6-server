from typing import Annotated, Optional
from datetime import datetime, date
from fastapi import Depends, HTTPException, status
from asset_management.app.schedule.repositories import ScheduleRepository
from asset_management.app.schedule.models import Schedule, Status
from asset_management.app.assets.repositories import AssetRepository
from asset_management.app.rental.schemas import RentalResponse
from asset_management.database.session import get_session
from sqlalchemy.orm import Session


class RentalService:
    """Schedule 모델을 사용하여 Rental API 제공"""
    
    def __init__(
        self,
        schedule_repo: Annotated[ScheduleRepository, Depends()],
        asset_repo: Annotated[AssetRepository, Depends()],
        db_session: Annotated[Session, Depends(get_session)],
    ):
        self.schedule_repo = schedule_repo
        self.asset_repo = asset_repo
        self.db_session = db_session

    def _schedule_to_rental(self, schedule: Schedule) -> RentalResponse:
        """Schedule 모델을 RentalResponse로 변환"""
        # status 매핑: IN_USE -> borrowed, RETURNED -> returned
        status_map = {
            Status.IN_USE.value: "borrowed",
            Status.RETURNED.value: "returned",
        }
        
        return RentalResponse(
            id=f"rental-{schedule.id:03d}",
            item_id=schedule.asset_id,
            user_id=schedule.user_id,
            status=status_map.get(schedule.status, "borrowed"),
            borrowed_at=schedule.start_date,
            expected_return_date=schedule.end_date.date() if schedule.end_date else None,
            returned_at=schedule.end_date if schedule.status == Status.RETURNED.value else None,
        )

    def borrow_item(
        self,
        user_id: str,
        item_id: int,
        club_id: int,
        expected_return_date: Optional[date] = None,
    ) -> RentalResponse:
        """물품 대여"""
        # 물품 존재 확인
        asset = self.asset_repo.get_asset_by_id(item_id)
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="존재하지 않는 물품 ID",
            )

        # 대여 가능 수량 확인
        if asset.available_quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="대여 가능한 수량 없음",
            )

        # Schedule 생성 (borrowed 상태)
        borrowed_at = datetime.now()
        end_date = datetime.combine(expected_return_date, datetime.max.time()) if expected_return_date else datetime.now()
        
        schedule = Schedule(
            start_date=borrowed_at,
            end_date=end_date,
            asset_id=item_id,
            user_id=user_id,
            club_id=club_id,
            status=Status.IN_USE.value,  # 대여 중
        )
        
        self.db_session.add(schedule)
        
        # 수량 감소
        asset.available_quantity -= 1
        
        self.db_session.commit()
        self.db_session.refresh(schedule)

        return self._schedule_to_rental(schedule)

    def return_item(self, rental_id: str, user_id: str) -> RentalResponse:
        """물품 반납"""

        schedule = self.db_session.query(Schedule).filter(Schedule.id == rental_id).first()
        
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="존재하지 않는 대여 기록",
            )

        if schedule.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="본인이 대여한 물품이 아님",
            )

        if schedule.status == Status.RETURNED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 반납된 물품",
            )

        # 반납 처리
        returned_at = datetime.now()
        schedule.status = Status.RETURNED.value
        schedule.end_date = returned_at  # 반납 시각 기록
        
        # 수량 증가
        asset = self.asset_repo.get_asset_by_id(schedule.asset_id)
        if asset:
            asset.available_quantity += 1
        
        self.db_session.commit()
        self.db_session.refresh(schedule)

        return self._schedule_to_rental(schedule)
