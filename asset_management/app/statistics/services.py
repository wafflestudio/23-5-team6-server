from datetime import datetime, timedelta
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from asset_management.app.schedule.repositories import ScheduleRepository
from asset_management.app.statistics.repositories import StatisticsRepository
from asset_management.app.statistics.schemas import AssetStatistics
from asset_management.database.session import get_session


class StatisticsService:
  def __init__(self, db_session: Annotated[Session, Depends(get_session)]):
    self.schedule_repository = ScheduleRepository(db_session)
    self.statistics_repository = StatisticsRepository(db_session)
    self.db_session = db_session

  def get_statistics_for_asset(self, asset_id: int):
    statistics = self.statistics_repository.get(asset_id)
    if statistics is None:
      self.statistics_repository.create(asset_id)
      statistics = self.update_statistics_for_asset(asset_id)
    if statistics.last_updated_at > datetime.now() + timedelta(days=3):
      statistics = self.update_statistics_for_asset(asset_id)

    return AssetStatistics.model_validate(statistics)

  def update_statistics_for_asset(self, asset_id: int):
    schedules = []
    query_result = self.schedule_repository.get_schedules(page=1, size=100, asset_id=asset_id)
    schedules += query_result.items
    while query_result.has_next:
      query_result = query_result.next()
      schedules += query_result.items
    total_rental_count = len(schedules)
    average_rental_duration = (
      0
      if total_rental_count == 0
      else (sum([(sch.end_date - sch.start_date).total_seconds() for sch in schedules]) / total_rental_count)
    )

    recent_rentals = [sch for sch in schedules if (datetime.now() - sch.start_date).days <= 30]

    recent_rental_count = len([sch for sch in recent_rentals])
    recent_rental_duration = (
      0
      if recent_rental_count == 0
      else (sum([(sch.end_date - sch.start_date).total_seconds() for sch in recent_rentals]) / recent_rental_count)
    )

    unique_borrower_count = len(set([sch.user_id for sch in schedules]))

    last_borrowed_at = None if total_rental_count == 0 else max([sch.start_date for sch in schedules])
    last_updated_at = datetime.now()

    updated_statistics = self.statistics_repository.update(
      asset_id,
      total_rental_count=total_rental_count,
      average_rental_duration=average_rental_duration,
      recent_rental_count=recent_rental_count,
      recent_avg_duration=recent_rental_duration,
      unique_borrower_count=unique_borrower_count,
      last_borrowed_at=last_borrowed_at,
      last_updated_at=last_updated_at,
    )

    return AssetStatistics.model_validate(updated_statistics)
