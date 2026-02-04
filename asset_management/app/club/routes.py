from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from asset_management.app.auth.dependencies import get_current_user
from asset_management.app.auth.utils import login_with_header
from asset_management.app.club.models import Club
from asset_management.app.club.schemas import ClubResponse, ClubUpdate
from asset_management.app.user.models import User, UserClublist
from asset_management.database.session import get_session

router = APIRouter(prefix="/clubs", tags=["clubs"])


@router.get("", response_model=List[ClubResponse], summary="List clubs")
def list_clubs(session: Session = Depends(get_session)):
    return session.query(Club).order_by(Club.id.asc()).all()

@router.get("/me",)
def my_clubs(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> List[ClubResponse]:
    user_clublists = session.query(UserClublist).filter(UserClublist.user_id == current_user.id).all()
    club_ids = [clublist.club_id for clublist in user_clublists]
    clubs = session.query(Club).filter(Club.id.in_(club_ids)).all()
    return clubs

@router.get(
    "/{club_id}",
    response_model=ClubResponse,
    summary="Get club by id",
)
def get_club(club_id: int, session: Session = Depends(get_session)):
    club = session.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Club not found")
    return club


def _check_club_admin(session: Session, user_id: str, club_id: int) -> bool:
    """사용자가 해당 동아리의 관리자인지 확인"""
    membership = session.query(UserClublist).filter(
        UserClublist.user_id == user_id,
        UserClublist.club_id == club_id,
        UserClublist.permission == 1  # 관리자
    ).first()
    return membership is not None


@router.put(
    "/{club_id}",
    response_model=ClubResponse,
    summary="Update a club",
)
def update_club(
    club_id: int,
    payload: ClubUpdate,
    user_id: str = Depends(login_with_header),
    session: Session = Depends(get_session),
):
    """동아리 정보 수정 (관리자만 가능)"""
    club = session.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Club not found")

    # 관리자 권한 체크
    if not _check_club_admin(session, user_id, club_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="관리자만 동아리 정보를 수정할 수 있습니다")

    if payload.name is not None:
        club.name = payload.name
        
    if payload.description is not None:
        club.description = payload.description
    if payload.location_lat is not None:
        club.location_lat = payload.location_lat
    if payload.location_lng is not None:
        club.location_lng = payload.location_lng

    session.commit()
    session.refresh(club)
    return club


@router.delete(
    "/{club_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a club",
)
def delete_club(
    club_id: int,
    user_id: str = Depends(login_with_header),
    session: Session = Depends(get_session),
):
    """동아리 삭제 (관리자만 가능) - 연관된 모든 데이터 및 관리자 계정도 함께 삭제됩니다"""
    club = session.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Club not found")

    # 관리자 권한 체크
    if not _check_club_admin(session, user_id, club_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="관리자만 동아리를 삭제할 수 있습니다")
    
    # 관리자 계정 찾기 (본인)
    admin_user = session.query(User).filter(User.id == user_id).first()
    
    # 동아리 삭제 (cascade로 UserClublist, Asset, Schedule 등 삭제됨)
    session.delete(club)
    
    # 관리자 계정 삭제
    if admin_user:
        session.delete(admin_user)
    
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
