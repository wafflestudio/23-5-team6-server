from pydantic import BaseModel, ConfigDict
from datetime import datetime

class AssetStatistics(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    total_rental_count: int
    average_rental_duration: float  # 초 단위
    recent_rental_count: int  # 30일
    recent_avg_duration: float  # 30일, 초 단위
    unique_borrower_count: int
    last_borrowed_at: datetime | None
    last_updated_at: datetime

