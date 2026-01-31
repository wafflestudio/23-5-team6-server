from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from asset_management.app.auth.dependencies import get_current_user
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


@router.put(
    "/{club_id}",
    response_model=ClubResponse,
    summary="Update a club",
)
def update_club(
    club_id: int, payload: ClubUpdate, session: Session = Depends(get_session)
):
    club = session.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Club not found")

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
def delete_club(club_id: int, session: Session = Depends(get_session)):
    club = session.query(Club).filter(Club.id == club_id).first()
    club_members = session.query(UserClublist).filter(UserClublist.club_id == club_id).all()
    for member in club_members:
        session.delete(member)
    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Club not found")

    session.delete(club)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
