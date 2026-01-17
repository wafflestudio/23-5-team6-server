from datetime import datetime
from typing import Annotated
from fastapi import Depends, HTTPException
from asset_management.app.schedule.models import Schedule, Status
from asset_management.app.schedule.repositories import ScheduleRepository
from asset_management.app.schedule.schemas import (
  ScheduleCreate,
  ScheduleListResponse,
  ScheduleResponse,
  ScheduleUpdate,
)


class ScheduleService:
  def __init__(self, repository: Annotated[ScheduleRepository, Depends()]):
    self.repository = repository

  def get_schedule(
    self,
    club_id: int,
    status: str = None,
    user_id: str = None,
    asset_id: int = None,
    start_date: datetime = None,
    end_date: datetime = None,
    page: int = 1,
    size: int = 10,
  ):
    schedules = self.repository.get_schedules(
      page=page,
      size=size,
      status=status,
      user_id=user_id,
      asset_id=asset_id,
      start_date=start_date,
      end_date=end_date,
    )

    return ScheduleListResponse(
      schedules=[
        ScheduleResponse(
          id=s.id,
          start_date=s.start_date,
          end_date=s.end_date,
          asset_id=s.asset_id,
          user_id=s.user_id,
          status=s.status,
        ) for s in schedules.items
      ],
      total=schedules.total,
      page=page,
      size=size,
      pages=schedules.pages,
    )

  def create_schedule(
    self, club_id: int, schedule_data: ScheduleCreate
  ) -> ScheduleResponse:
    # 중복 스케줄 체크 (선택적)
    schedule = self.repository.add_schedule(
      Schedule(**schedule_data.model_dump())
    )
    return ScheduleResponse(
      id=schedule.id,
      start_date=schedule.start_date,
      end_date=schedule.end_date,
      asset_id=schedule.asset_id,
      user_id=schedule.user_id,
      status=schedule.status,
    )

  def update_schedule(self, schedule_id: int, schedule_data: ScheduleUpdate) -> ScheduleResponse:
    # 업데이트할 필드만 추출
    update_dict = {k: v for k, v in schedule_data.model_dump().items() if v is not None}
    updated_schedule = self.repository.update_schedule(schedule_id, **update_dict)
    if not updated_schedule:
      raise HTTPException(status_code=404, detail="Schedule not found")
    return ScheduleResponse(
      id=updated_schedule.id,
      start_date=updated_schedule.start_date,
      end_date=updated_schedule.end_date,
      asset_id=updated_schedule.asset_id,
      user_id=updated_schedule.user_id,
      status=updated_schedule.status,
    )

  def delete_schedule(self, schedule_id: int, user_id: str) -> None:
    schedule = self.repository.get_schedule_by_id(schedule_id)
    if not schedule:
      raise HTTPException(status_code=404, detail="Schedule not found")
    if schedule.user_id != user_id and not self.is_admin(user_id):
      raise HTTPException(status_code=403, detail="Not authorized to delete this schedule")
    self.repository.delete_schedule(schedule_id)

  def is_admin(self, user_id: str) -> bool:
    return self.repository.is_admin(user_id)
