from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import secrets
import string

from asset_management.app.user.models import User, UserClublist, UserPermission
from asset_management.app.club.models import Club
from asset_management.app.admin.schemas import (
    AdminSignupRequest, 
    AdminSignupResponse,
    UserApprovalRequest,
    UserApprovalResponse,
    PendingUsersResponse,
    PendingUserDetail
)
from asset_management.database.session import get_session
from asset_management.app.auth.utils import hash_password
from asset_management.app.auth.dependencies import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])


def generate_club_code(length: int = 6) -> str:
    """Generate random club code (uppercase + digits)"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    response_model=AdminSignupResponse,
    summary="Admin signup with club creation",
)
def admin_signup(payload: AdminSignupRequest, session: Session = Depends(get_session)):
    # Check if email already exists
    existing_user = session.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Email already registered"
        )
    
    # Check if club name already exists
    existing_club = session.query(Club).filter(Club.name == payload.club_name).first()
    if existing_club:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Club name already exists"
        )
    
    # Generate unique club code
    while True:
        club_code = generate_club_code()
        existing = session.query(Club).filter(Club.club_code == club_code).first()
        if not existing:
            break
    
    # Create club
    club = Club(
        name=payload.club_name,
        description=payload.club_description,
        club_code=club_code,
    )
    session.add(club)
    session.flush()  # Get club.id without committing
    
    # Create admin user
    hashed_password = hash_password(payload.password)
    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hashed_password,
        is_admin=True,  # Mark as admin
    )
    session.add(user)
    session.flush()
    
    # Link admin user to club with ADMIN permission
    user_club = UserClublist(
        user_id=user.id,
        club_id=club.id,
        permission=UserPermission.ADMIN.value,
    )
    session.add(user_club)
    
    session.commit()
    session.refresh(user)
    session.refresh(club)
    
    return AdminSignupResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        club_id=club.id,
        club_name=club.name,
        club_code=club.club_code,
    )


@router.get(
    "/applylist",
    response_model=PendingUsersResponse,
    summary="Get pending user applications for admin's club",
)
def get_pending_applications(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get admin's club
    admin_club = session.query(UserClublist).filter(
        UserClublist.user_id == current_user.id,
        UserClublist.permission == UserPermission.ADMIN.value
    ).first()
    
    if not admin_club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin club not found"
        )
    
    # Get all applicants for this club
    applicants = session.query(User, UserClublist).join(
        UserClublist, User.id == UserClublist.user_id
    ).filter(
        UserClublist.club_id == admin_club.club_id,
        UserClublist.permission == UserPermission.APPLICANT.value
    ).all()
    
    pending_users = [
        PendingUserDetail(
            id=user.id,
            name=user.name,
            email=user.email,
            student_id=user.student_id,
        )
        for user, user_club in applicants
    ]
    
    return PendingUsersResponse(users=pending_users)


@router.patch(
    "/users/{user_id}/approve",
    response_model=UserApprovalResponse,
    summary="Approve or reject user application",
)
def approve_user(
    user_id: str,
    payload: UserApprovalRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get admin's club
    admin_club = session.query(UserClublist).filter(
        UserClublist.user_id == current_user.id,
        UserClublist.permission == UserPermission.ADMIN.value
    ).first()
    
    if not admin_club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin club not found"
        )
    
    # Get user's club application
    user_club = session.query(UserClublist).filter(
        UserClublist.user_id == user_id,
        UserClublist.club_id == admin_club.club_id
    ).first()
    
    if not user_club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User application not found"
        )
    
    # Get the user
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if payload.approved:
        # Approve: change permission to USER
        user_club.permission = UserPermission.USER.value
        status_text = "approved"
    else:
        # Reject: delete the application
        session.delete(user_club)
        status_text = "rejected"
    
    session.commit()
    session.refresh(user)
    
    return UserApprovalResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        status=status_text,
    )
