from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from asset_management.database.session import get_session
from asset_management.app.statistics.model import Statistic

class StatisticsRepository:
    def __init__(self, db_session: Session):
        self.session = db_session
    
    def get(self, id):
        statistics = self.session.query(Statistic).filter(Statistic.asset_id == id).first()
        return statistics
    
    def create(self, asset_id: int):
        statistics = Statistic(asset_id=asset_id)
        self.session.add(statistics)
        self.session.commit()
        self.session.refresh(statistics)
        return statistics
    
    def update(self, asset_id: int, **kwargs):
        statistics = self.get(asset_id)
        if not statistics:
            return None
        for key, value in kwargs.items():
            setattr(statistics, key, value)
        self.session.commit()
        return statistics