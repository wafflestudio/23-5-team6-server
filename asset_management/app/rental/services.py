from typing import Annotated, Optional
import math
from datetime import datetime, date
from fastapi import Depends, HTTPException, status, UploadFile
from asset_management.app.schedule.repositories import ScheduleRepository
from asset_management.app.schedule.models import Schedule, Status
from asset_management.app.assets.repositories import AssetRepository
from asset_management.app.club.models import Club
from asset_management.app.assets.models import Asset
from asset_management.app.rental.schemas import RentalResponse
from asset_management.database.session import get_session
from asset_management.app.picture.models import Picture
from sqlalchemy.orm import Session
from sqlalchemy import update


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
        # status 판정: IN_USE + 기한 초과 -> overdue
        # end_date == start_date인 경우는 무기한 대여 (expected_return_date 미지정)
        if schedule.status == Status.IN_USE.value:
            has_due_date = schedule.end_date and schedule.end_date != schedule.start_date
            is_overdue = has_due_date and schedule.end_date < datetime.now()
            rental_status = "overdue" if is_overdue else "in_use"
        elif schedule.status == Status.RETURNED.value:
            rental_status = "returned"
        else:
            rental_status = "in_use"
        
        
        return RentalResponse(
            id=schedule.id,
            item_id=schedule.asset_id,
            user_id=schedule.user_id,
            status=rental_status,
            borrowed_at=schedule.start_date,
            expected_return_date=schedule.end_date.date() if schedule.end_date else None,
            returned_at=schedule.end_date if schedule.status == Status.RETURNED.value else None,
        )

    def borrow_item(
        self,
        user_id: str,
        item_id: int,
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
        
        borrowed_at = datetime.now()

        if expected_return_date is not None:
            if expected_return_date < borrowed_at.date():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="반납 예정일은 대여일 이후여야 합니다",
                )
            
            expected_end = datetime.combine(
                expected_return_date,
                datetime.max.time()
            )
            rental_days = (expected_end.date() - borrowed_at.date()).days + 1
            end_date = expected_end
        else:
            rental_days = asset.max_rental_days if asset.max_rental_days is not None else -1
            end_date = borrowed_at

        if asset.max_rental_days is not None:
            if rental_days > asset.max_rental_days:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "최대 대여 일수 초과",
                        "max_rental_days": asset.max_rental_days,
                        "requested_days": rental_days,
                    },
                )

        # 대여 가능 수량 확인 및 감소 (낙관적 락)
        result = self.db_session.execute(
            update(Asset)
            .where(Asset.id == item_id, Asset.available_quantity > 0)
            .values(available_quantity=Asset.available_quantity - 1)
        )
        
        if result.rowcount == 0:
            self.db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="대여 가능한 수량 없음",
            )


        
        schedule = Schedule(
            start_date=borrowed_at,
            end_date=end_date,
            asset_id=item_id,
            user_id=user_id,
            club_id=asset.club_id,  # asset에서 club_id 가져오기
            status=Status.IN_USE.value,  # 대여 중
        )
        
        self.db_session.add(schedule)
        
        self.db_session.commit()
        self.db_session.refresh(schedule)

        return self._schedule_to_rental(schedule)

    async def return_item(
        self,
        rental_id: int,
        user_id: str,
        file: Optional[UploadFile] = None,
        location_lat: Optional[int] = None,
        location_lng: Optional[int] = None,
    ) -> RentalResponse:
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

        # 위치 검증 먼저
        club = self.db_session.query(Club).filter(Club.id == schedule.club_id).first()
        club_lat = getattr(club, "location_lat", None) if club else None
        club_lng = getattr(club, "location_lng", None) if club else None
        if club_lat is not None and club_lng is not None:
            if location_lat is None or location_lng is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="반납 위치 정보가 필요합니다",
                )

            club_lat = club_lat / 1_000_000
            club_lng = club_lng / 1_000_000
            user_lat = location_lat / 1_000_000
            user_lng = location_lng / 1_000_000

            radius_m = 6_371_000
            phi1 = math.radians(club_lat)
            phi2 = math.radians(user_lat)
            dphi = math.radians(user_lat - club_lat)
            dlambda = math.radians(user_lng - club_lng)
            a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
            distance_m = 2 * radius_m * math.asin(math.sqrt(a))

            if distance_m > 15:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="반납 위치가 동아리 위치 반경 15m 밖입니다",
                )

        # 이미지 파일 검증
        if file is not None:
            if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unsupported image type"
                )
        
        # 파일 크기 검증 (5MB 제한) - 청크 단위로 읽기
        data = None
        if file is not None:
            max_size = 5 * 1024 * 1024  # 5MB
            chunks = []
            total_size = 0
            
            while True:
                chunk = await file.read(8192)  # 8KB씩 읽기
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > max_size:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="File too large"
                    )
                chunks.append(chunk)
            
            data = b''.join(chunks)

        # 반납 처리
        returned_at = datetime.now()
        

        try:
            return_picture_id = None
            if file is not None:
                new_picture = Picture(
                    asset_id=schedule.asset_id,
                    is_main=False,
                    user_id=user_id,
                    data=data,
                    content_type=file.content_type,
                    filename=file.filename or "upload",
                    size=len(data) if data is not None else 0,
                )

                self.db_session.add(new_picture)
                self.db_session.flush()
                return_picture_id = new_picture.id

            # 낙관적 락으로 반납 상태 업데이트
            result = self.db_session.execute(
                update(Schedule)
                .where(
                    Schedule.id == rental_id,
                    Schedule.user_id == user_id,
                    Schedule.status == Status.IN_USE.value,
                )
                .values(
                    status=Status.RETURNED.value,
                    end_date=returned_at,
                    return_picture_id=return_picture_id,
                    )
            )

            if result.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 반납되었거나 반납할 수 없는 상태",
                )

            self.db_session.execute(
                update(Asset)
                .where(Asset.id == schedule.asset_id)
                .values(available_quantity=Asset.available_quantity + 1)
            )
            self.db_session.commit()
        
        except Exception as e:
            self.db_session.rollback()
            raise e
        
        schedule = self.db_session.query(Schedule).filter(Schedule.id == rental_id).first()

        return self._schedule_to_rental(schedule)
