from typing import Annotated

from fastapi import APIRouter, Depends

from asset_management.app.statistics.schemas import AssetStatistics
from asset_management.app.statistics.services import StatisticsService

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/{asset_id}")
def get_statistics(asset_id: int, stat_service: Annotated[StatisticsService, Depends()]) -> AssetStatistics:
  '''통계를 불러옵니다.'''
  statistics = stat_service.get_statistics_for_asset(asset_id)

  return statistics

@router.get("/{asset_id}/update")
def update_statistics(asset_id: int, stat_service: Annotated[StatisticsService, Depends()]) -> AssetStatistics:
  '''통계를 갱신합니다.'''
  statistics = stat_service.update_statistics_for_asset(asset_id)
  return statistics