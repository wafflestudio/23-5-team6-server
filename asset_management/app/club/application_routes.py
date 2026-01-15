from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from asset_management.app.user.models import User, UserClublist, UserPermission
from asset_management.app.club.models import Club
from asset_management.app.club.schemas import ClubApplicationRequest, ClubApplicationResponse
from asset_management.database.session import get_session
from asset_management.app.auth.dependencies import get_current_user

router = APIRouter(prefix="/club", tags=["clubs"])


@router.post(
    "/apply",
    status_code=status.HTTP_200_OK,
    response_model=ClubApplicationResponse,
    summary="Apply to join a club",
)
def apply_to_club(
    payload: ClubApplicationRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Find club by code
    club = session.query(Club).filter(Club.club_code == payload.club_code).first()
    if not club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid club code"
        )
    
    # Check if user already applied or is member
    existing = session.query(UserClublist).filter(
        UserClublist.user_id == current_user.id,
        UserClublist.club_id == club.id
    ).first()
    
    if existing:
        if existing.permission == UserPermission.USER.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Already a member of this club"
            )
        elif existing.permission == UserPermission.APPLICANT.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Application already pending"
            )
    
    # Create application
    application = UserClublist(
        user_id=current_user.id,
        club_id=club.id,
        permission=UserPermission.APPLICANT.value,
    )
    session.add(application)
    session.commit()
    session.refresh(application)
    
    return ClubApplicationResponse(
        application_id=application.id,
        club_name=club.name,
        status="pending",
    )
