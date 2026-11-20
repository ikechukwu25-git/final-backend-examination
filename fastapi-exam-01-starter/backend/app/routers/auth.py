
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app import schemas
from app.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
    bearer_scheme
)

from fastapi.security import HTTPAuthorizationCredentials
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# ==================================
# GET CURRENT STAFF
# ==================================


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"}
    )

    # Extract JWT from Bearer credentials
    token = credentials.credentials

    # Decode JWT
    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")

    if user_id is None:
        raise credentials_exception

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise credentials_exception

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This staff account is inactive"
        )

    return user


# ==================================
# STAFF REGISTRATION
# ==================================

@router.post(
    "/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_staff(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db)
):

    # Check whether email already exists
    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )

    # Hash password
    hashed_password = get_password_hash(
        user_data.password
    )

    # Create staff account
    new_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# ==================================
# STAFF LOGIN
# ==================================

@router.post(
    "/login",
    response_model=schemas.Token
)
def login_staff(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    # Find staff by email
    user = db.query(User).filter(
        User.email == form_data.username
    ).first()

    # Verify credentials
    if not user or not verify_password(
        form_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This staff account is inactive"
        )

    # Generate JWT
    access_token = create_access_token(
        data={"sub": str(user.id)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ==================================
# CURRENT STAFF PROFILE
# ==================================

@router.get(
    "/me",
    response_model=schemas.UserResponse
)
def get_staff_profile(
    current_user: User = Depends(get_current_user)
):

    return current_user
