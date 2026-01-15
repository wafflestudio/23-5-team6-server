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
      club_id=club_id,
      status=status,
      user_id=user_id,
      asset_id=asset_id,
      start_date=start_date,
      end_date=end_date,
    )

    return ScheduleListResponse(
      schedules=[ScheduleResponse(**x) for x in schedules],
      total=schedules.total,
      page=schedules.page,
      size=schedules.size,
      pages=schedules.pages,
    )

  def create_schedule(
    self, club_id: int, schedule_data: ScheduleCreate
  ) -> ScheduleResponse:
    self.repository.get_schedules(
      club_id=club_id,
      asset_id=schedule_data.asset_id,
      status=Status.APPROVED.value,
    )
    schedule = self.repository.add_schedule(
      Schedule(club_id=club_id, **schedule_data.model_dump())
    )
    return ScheduleResponse(**schedule)

  def update_schedule(self, schedule: ScheduleUpdate) -> ScheduleResponse:
    updated_schedule = self.repository.update_schedule(schedule)
    return ScheduleResponse(**updated_schedule)

  def delete_schedule(self, schedule_id: int, user_id: str) -> None:
    schedule = self.repository.get_schedules(schedule_id=schedule_id)
    if schedule.user_id != user_id and not self.is_admin(user_id):
      raise HTTPException(status_code=403, detail="Not authorized to delete this schedule")
    self.repository.delete_schedule(schedule_id)

  def is_admin(self, user_id: str) -> bool:
    return self.repository.is_admin(user_id)
