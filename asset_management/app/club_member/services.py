from asset_management.app.club_member.schemas import ClubMember, ClubMemberResponse
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from asset_management.app.club_member.repositories import ClubMemberRepository
from asset_management.database.session import get_session


class ClubMemberService:
  def __init__(self, db_session: Session = Depends(get_session)):
    self.repository = ClubMemberRepository(db_session)

  def get_club_members(
    self,
    id: int | None = None,
    user_id: int | None = None,
    club_id: int | None = None,
    permission: int | None = None,
    page: int = 1,
    size: int = 10,
  ) -> ClubMemberResponse:
    members = self.repository.get_club_members(
      id, user_id, club_id, permission, page, size
    )
    return ClubMemberResponse(
      total=members.total,
      page=page,
      size=size,
      pages=members.pages,
      items=[
        ClubMember(
          id=member.id,
          user_id=member.user_id,
          name=member.user.name,
          club_id=member.club_id,
          permission=member.permission,
        )
        for member in members.items
      ],
    )

  def get_my_membership(
    self, user_id: str, page: int = 1, size: int = 10
  ) -> ClubMemberResponse:
    members = self.repository.get_club_members(user_id=user_id, page=page, size=size)
    return ClubMemberResponse(
      total=members.total,
      page=page,
      size=size,
      pages=members.pages,
      items=[
        ClubMember(
          id=member.id,
          user_id=member.user_id,
          name=member.user.name,
          club_id=member.club_id,
          permission=member.permission,
        )
        for member in members.items
      ],
    )

  def edit_club_member(
    self, member_id: int, club_id: int, new_permission: int
  ) -> ClubMember:
    member = self.repository.edit_club_member(member_id, new_permission)
    if not member:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
      )
    return ClubMember(
      id=member.id,
      user_id=member.user_id,
      name=member.user.name,
      club_id=member.club_id,
      permission=member.permission,
    )

  def delete_club_member(self, member_id: int) -> None:
    success = self.repository.delete_club_member(member_id)
    if not success:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
      )

  def create_club_member(
    self,
    user_id: str,
    permission: int,
    club_id: int,
  ) -> ClubMember:
    if self.repository.get_club_members(user_id = user_id, club_id = club_id).items:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Already a member of the club"
      )
    member = self.repository.create_club_member(user_id, permission, club_id)
    if member is None:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Club not found"
      )
    return ClubMember(
      id=member.id,
      user_id=member.user_id,
      name=member.user.name,
      club_id=member.club_id,
      permission=member.permission,
    )

  def create_club_member_with_code(
    self,
    user_id: str,
    permission: int,
    club_code: str,
  ) -> ClubMember:
    member = self.repository.create_club_member_with_code(
      user_id, permission, club_code
    )
    if member is None:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Club not found"
      )
    return ClubMember(
      id=member.id,
      user_id=member.user_id,
      name=member.user.name,
      club_id=member.club_id,
      permission=member.permission,
    )

  def check_club_permission(self, user_club_id: int, resource_club_id: int) -> int:
    permission = self.repository.check_club_permission(user_club_id, resource_club_id)
    
    if permission is None:
      raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
      )
    return permission