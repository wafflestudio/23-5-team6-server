from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from asset_management.app.user.models import User
from asset_management.app.user.schemas import UserCreate, UserResponse
from asset_management.app.auth.utils import hash_password
from asset_management.database.session import get_session

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
    summary="Register with email/password",
)
def signup(payload: UserCreate, session: Session = Depends(get_session)):
    """Register a new user with email and password."""
    existing = session.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
