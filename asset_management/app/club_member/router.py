from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from asset_management.app.club_member.schemas import (
  ClubMember,
  ClubMemberResponse,
  ClubMemberCreate,
  ClubMemberUpdate,
)
from asset_management.app.user.models import UserClublist
from asset_management.app.club_member.services import ClubMemberService
from asset_management.app.auth.utils import login_with_header

router = APIRouter(prefix="/club-members", tags=["club-members"])


@router.get("/")
def get_club_members(
  club_id: int | None = None,
  member_id: int | None = None,
  user_id: str | None = None,
  permission: int | None = None,
  page: int = Query(1, ge=1),
  size: int = Query(10, ge=1),
  club_member_service: ClubMemberService = Depends(),
  my_id=Depends(login_with_header),
) -> ClubMemberResponse:
  """동아리원 목록 조회

  permission은 일반 회원 0, 관리자 1, 가입대기 2의 값을 가집니다.
  """
  if club_id is not None:
    if club_member_service.check_club_permission(my_id, club_id) in [0, 1]:
      return club_member_service.get_club_members(
        id=member_id,
        user_id=user_id,
        club_id=club_id,
        permission=permission,
        page=page,
        size=size,
      )
    else:
      return club_member_service.get_club_members(
        id=member_id,
        user_id=my_id,
        club_id=club_id,
        permission=permission,
        page=page,
        size=size,
      )
  else:
    return club_member_service.get_club_members(
      id=member_id, permission=permission, user_id=my_id, page=page, size=size
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
def new_club_member(
  request: ClubMemberCreate,
  club_member_service: ClubMemberService = Depends(),
  user=Depends(login_with_header),
) -> ClubMember:
  """동아리원 추가"""
  if request.club_id is None and request.club_code is None:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Either club_id or club_code must be provided",
    )

  # permission이 2(가입대기)가 아닌 경우 관리자 권한 필요
  if request.permission != 2:
    # club_code 사용 시 먼저 club_id를 찾아서 권한 체크
    if request.club_id is not None:
      club_id_to_check = request.club_id
    else:
      # club_code로 club 찾기 (permission != 2일 때만)
      from asset_management.app.club.models import Club
      club = club_member_service.repository.db_session.query(Club).filter(
        Club.club_code == request.club_code
      ).first()
      if club is None:
        raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND, detail="Club not found"
        )
      club_id_to_check = club.id
    
    # 관리자 권한 체크
    if not club_member_service.check_club_permission(user, club_id_to_check) == 1:
      raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
      )

  # club_id 또는 club_code로 회원 생성
  if request.club_id is not None:
    return club_member_service.create_club_member(
      request.user_id, request.permission, request.club_id
    )
  else:
    return club_member_service.create_club_member_with_code(
      request.user_id, request.permission, request.club_code
    )


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_club_member(
  member_id: int,
  user=Depends(login_with_header),
  club_member_service: ClubMemberService = Depends(),
) -> None:
  """동아리원 삭제 (관리자 또는 본인 탈퇴)"""
  members_response = club_member_service.get_club_members(id=member_id)
  if not members_response.items:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
    )
  member = members_response.items[0]
  club_id = member.club_id
  user_id = member.user_id
  
  # 본인이거나 관리자면 삭제 가능
  is_admin = club_member_service.check_club_permission(user, club_id) == 1
  is_self = user == user_id
  
  if is_admin or is_self:
    club_member_service.delete_club_member(member_id)
  else:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
    )


@router.put("/{member_id}")
def update_club_member(
  member_id: int,
  request: ClubMemberUpdate,
  user=Depends(login_with_header),
  club_member_service: ClubMemberService = Depends(),
) -> ClubMember:
  """동아리원 권한 수정"""
  members_response = club_member_service.get_club_members(id=member_id)
  if not members_response.items:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
    )
  club_id = members_response.items[0].club_id
  if club_member_service.check_club_permission(user, club_id) == 1:
    member = club_member_service.edit_club_member(
      member_id, club_id, request.permission
    )
  else:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
    )

  return member
