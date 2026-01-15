from fastapi import APIRouter, Depends
from asset_management.app.schedule.services import ScheduleService
from asset_management.app.auth.utils import login_with_header

router = APIRouter(prefix="/schedules", tags=["schedules"])

@router.get("/")
def get_schedules(
  status: int | None = None,
  user_id: str | None = None,
  asset_id: int | None = None,
  page: int = 1,
  size: int = 10,
  schedule_service: ScheduleService = Depends(),
  my_id=Depends(login_with_header),
):
  """대여일정 목록 조회
  
  일반 사용자는 자신의 대여일정, 관리자는 모든 사용자의 대여일정을 조회할 수 있습니다."""
  pass

@router.post("/", status_code=201)
def new_schedule(
  request: dict,
  schedule_service: ScheduleService = Depends(),
  user=Depends(login_with_header),
):
  """대여일정 추가"""
  pass

@router.put("/{schedule_id}")
def update_schedule(
  schedule_id: int,
  request: dict,
  schedule_service: ScheduleService = Depends(),
  user=Depends(login_with_header),
) -> :
  """대여일정 수정
  
  승인/반납/취소 등의 상태 변경이 가능하며, 날짜 변경 또한 가능합니다."""
  pass

@router.delete("/{schedule_id}", status_code=204)
def delete_schedule(
  schedule_id: int,
  schedule_service: ScheduleService = Depends(),
  user=Depends(login_with_header),
):
  """대여일정 삭제"""
  pass