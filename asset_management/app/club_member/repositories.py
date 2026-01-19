from asset_management.database.session import get_session
from typing import Annotated, List
from sqlalchemy.orm import Session, joinedload
from fastapi import Depends
from asset_management.app.user.models import UserClublist
from sqlalchemy_pagination import paginate
from asset_management.app.club.models import Club


class ClubMemberRepository:
    def __init__(self, db_session: Annotated[Session, Depends(get_session)]):
        self.db_session = db_session

    def get_club_members(
        self,
        id: int | None = None,
        user_id: int | None = None,
        club_id: int | None = None,
        permission: int | None = None,
        page: int = 1,
        size: int = 10,
    ) -> List[UserClublist]:
        query = self.db_session.query(UserClublist).options(joinedload(UserClublist.user))
        if id is not None:
            query = query.filter(UserClublist.id == id)
        if club_id is not None:
            query = query.filter(UserClublist.club_id == club_id)
        if user_id is not None:
            query = query.filter(UserClublist.user_id == user_id)
        if permission is not None:
            query = query.filter(UserClublist.permission == permission)
        return paginate(query, page, size)
    
    def create_club_member(
        self, user_id: str, permission: int, club_id: int
    ) -> UserClublist:
        new_member = UserClublist(
            user_id=user_id,
            club_id=club_id,
            permission=permission,
        )
        self.db_session.add(new_member)
        self.db_session.commit()
        self.db_session.refresh(new_member)
        # Load the user relationship
        self.db_session.refresh(new_member, ["user"])
        return new_member
    
    def create_club_member_with_code(
        self, user_id: str, permission: int, club_code: str | None
    ) -> UserClublist:
        club = (
            self.db_session.query(Club)
            .filter(Club.code == club_code)
            .first()
        )
        if club is None:
            return None
        new_member = UserClublist(
            user_id=user_id,
            club_id=club.id,
            permission=permission,
        )
        self.db_session.add(new_member)
        self.db_session.commit()
        self.db_session.refresh(new_member)
        # Load the user relationship
        self.db_session.refresh(new_member, ["user"])
        return new_member

    def edit_club_member(
        self, member_id: int, new_permission: int
    ) -> UserClublist | None:
        member = (
            self.db_session.query(UserClublist)
            .options(joinedload(UserClublist.user))
            .filter(
                UserClublist.id == member_id,
            )
            .first()
        )
        if member:
            member.permission = new_permission
            self.db_session.commit()
        return member

    def delete_club_member(self, member_id: int) -> bool:
        member = (
            self.db_session.query(UserClublist)
            .filter(UserClublist.id == member_id)
            .first()
        )
        if member:
            self.db_session.delete(member)
            self.db_session.commit()
            return True
        return False
    def check_club_permission(self, user_club_id: int, resource_club_id: int) -> int | None:
        club_member = (
            self.db_session.query(UserClublist)
            .filter(
                UserClublist.club_id == resource_club_id,
                UserClublist.user_id == user_club_id,
            )
            .first()
        )
        if club_member:
            return club_member.permission
        return None