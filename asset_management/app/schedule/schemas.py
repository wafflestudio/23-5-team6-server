from fastapi import HTTPException
from pydantic import BaseModel, field_validator
from datetime import datetime
from asset_management.app.schedule.models import Status


class ScheduleBase(BaseModel):
  start_date: datetime
  end_date: datetime
  asset_id: int
  user_id: str
  status: str

  @field_validator("status")
  def validate_status(cls, value):
    if value not in map(lambda x: x.value, Status):
      raise HTTPException(status_code=400, detail="Invalid status value")
    return value

class ScheduleCreate(ScheduleBase):
  pass

class ScheduleResponse(ScheduleBase):
  id: int

class ScheduleUpdate(BaseModel):
  start_date: datetime | None = None
  end_date: datetime | None = None
  asset_id: int | None = None
  user_id: str | None = None
  status: str | None = None

class ScheduleListResponse(BaseModel):
  schedules: list[ScheduleResponse]
  total: int
  page: int
  size: int
  pages: int