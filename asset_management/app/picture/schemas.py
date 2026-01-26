from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

class PictureResponse(BaseModel):
    id: int
    date: datetime
    asset_id: int
    is_main: bool
    user_id: str
    
    content_type: str
    filename: str
    size: int

    class Config:
        from_attributes = True

class PictureCreateRequest(BaseModel):
    asset_id: int
    is_main: Optional[bool] = False