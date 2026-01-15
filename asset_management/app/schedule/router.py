from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends
from asset_management.app.schedule.models import Status
from asset_management.app.schedule.services import ScheduleService
from asset_management.app.auth.utils import login_with_header
from asset_management.app.schedule.schemas import (
  ScheduleListResponse,
  ScheduleResponse,
  ScheduleUpdate,
  ScheduleCreate,
)

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("/{club_id}")
def get_schedules(
  schedule_service: Annotated[ScheduleService, Depends()] ,
  club_id: int,
  status: int | None = None,
  user_id: str | None = None,
  asset_id: int | None = None,
  start_date: datetime | None = None,
  end_date: datetime | None = None,
  page: int = 1,
  size: int = 10,
  my_id=Depends(login_with_header),
) -> ScheduleListResponse:
  """대여 목록 조회

  일반 사용자는 자신의 대여, 관리자는 모든 사용자의 대여를 조회할 수 있습니다."""
  if schedule_service.is_admin(my_id) is False:
    user_id = my_id
  
  return schedule_service.get_schedule(
    club_id=club_id,
    status=status,
    user_id=user_id,
    asset_id=asset_id,
    start_date=start_date,
    end_date=end_date,
    page=page,
    size=size,
  )


@router.post("/{club_id}", status_code=201)
def new_schedule(
  request: ScheduleCreate,
  club_id: int, 
  schedule_service: Annotated[ScheduleService, Depends()] ,
  user=Depends(login_with_header),
) -> ScheduleResponse:
  """대여 추가"""
  return schedule_service.create_schedule(club_id, request)


@router.put("/{schedule_id}")
def update_schedule(
  schedule_id: int,
  request: ScheduleUpdate,
  schedule_service: Annotated[ScheduleService, Depends()] ,
  user=Depends(login_with_header),
) -> ScheduleResponse:
  """대여 수정

  승인/반납/취소 등의 상태 변경이 가능하며, 날짜 변경 또한 가능합니다."""
  return schedule_service.update_schedule(request)


@router.delete("/{schedule_id}", status_code=204)
def delete_schedule(
  schedule_id: int,
  schedule_service: Annotated[ScheduleService, Depends()] ,
  user=Depends(login_with_header),
) -> None:
  """대여 삭제"""
  return schedule_service.delete_schedule(schedule_id, user)