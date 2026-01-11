from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
import secrets
import string

from asset_management.app.club.models import Club
from asset_management.app.club.schemas import ClubCreate, ClubResponse, ClubUpdate
from asset_management.database.session import get_session

router = APIRouter(prefix="/clubs", tags=["clubs"])


def generate_club_code(length: int = 6) -> str:
    """랜덤 동아리 코드 생성 (대문자 + 숫자)"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ClubResponse,
    summary="Create a club",
)
def create_club(payload: ClubCreate, session: Session = Depends(get_session)):
    while True:
        club_code = generate_club_code()
        existing = session.query(Club).filter(Club.club_code == club_code).first()
        if not existing:
            break

    club = Club(
        name=payload.name,
        description=payload.description,
        club_code=club_code,
    )
    session.add(club)
    session.commit()
    session.refresh(club)
    return club


@router.get("", response_model=List[ClubResponse], summary="List clubs")
def list_clubs(session: Session = Depends(get_session)):
    return session.query(Club).order_by(Club.id.asc()).all()


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
    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Club not found")

    session.delete(club)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
