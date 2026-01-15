from datetime import datetime
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from asset_management.app.user.models import User
from asset_management.database.session import get_session
from asset_management.app.schedule.models import Schedule
from sqlalchemy_pagination import paginate, Page

class ScheduleRepository:
    def __init__(self, db_session: Annotated[Session, Depends(get_session)]):
        self.db_session = db_session

    def get_schedules(self, page: int, size: int, start_date: datetime = None, end_date: datetime = None, **filters) -> Page:
        query = self.db_session.query(Schedule)
        for attr, value in filters.items():
            if value is not None:
                query = query.filter(getattr(Schedule, attr) == value)
        if start_date is not None:
            query = query.filter(Schedule.start_date >= start_date)
        if end_date is not None:
            query = query.filter(Schedule.end_date <= end_date)
        return paginate(query, page, size)

    def add_schedule(self, schedule: Schedule) -> Schedule:
        self.db_session.add(schedule)
        self.db_session.commit()
        self.db_session.refresh(schedule)
        return schedule
    
    def update_schedule(self, schedule_id: int, **updates) -> Schedule | None:
        schedule = self.db_session.query(Schedule).filter(Schedule.id == schedule_id).first()
        if not schedule:
            return None
        for key, value in updates.items():
            setattr(schedule, key, value)
        self.db_session.commit()
        self.db_session.refresh(schedule)
        return schedule

    def delete_schedule(self, schedule_id: int) -> bool:
        schedule = self.db_session.query(Schedule).filter(Schedule.id == schedule_id).first()
        if not schedule:
            return False
        self.db_session.delete(schedule)
        self.db_session.commit()
        return True
    
    def is_admin(self, user_id: str) -> bool:
        return self.db_session.query(User).filter(User.id == user_id).first().is_admin