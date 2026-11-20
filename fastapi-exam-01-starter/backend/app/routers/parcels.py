
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session
import secrets

from app.database import get_db
from app.models import User, Parcel, ParcelTracking
from app import schemas
from app.routers.auth import get_current_user


router = APIRouter(
    prefix="/parcels",
    tags=["Parcel Management"]
)


# ==================================
# TRACKING CODE GENERATOR
# ==================================

def generate_tracking_code(db: Session):
    while True:
        tracking_code = (
            f"OKW-{secrets.token_hex(4).upper()}"
        )

        existing_parcel = db.query(Parcel).filter(
            Parcel.tracking_code == tracking_code
        ).first()

        if existing_parcel is None:
            return tracking_code


# ==================================
# BOOK A NEW PARCEL
# ==================================

@router.post(
    "/",
    response_model=schemas.ParcelResponse,
    status_code=status.HTTP_201_CREATED
)
def book_parcel(
    parcel_data: schemas.ParcelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # Prevent same-city deliveries
    if parcel_data.origin == parcel_data.destination:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Origin and destination cannot be the same"
        )

    # Generate unique tracking code
    tracking_code = generate_tracking_code(db)

    # Create parcel
    new_parcel = Parcel(
        tracking_code=tracking_code,
        sender_name=parcel_data.sender_name,
        sender_phone=parcel_data.sender_phone,
        receiver_name=parcel_data.receiver_name,
        receiver_phone=parcel_data.receiver_phone,
        description=parcel_data.description,
        weight=parcel_data.weight,
        origin=parcel_data.origin,
        destination=parcel_data.destination,
        status="BOOKED",
        staff_id=current_user.id
    )

    db.add(new_parcel)
    db.flush()

    # Create initial tracking record
    initial_tracking = ParcelTracking(
        parcel_id=new_parcel.id,
        status="BOOKED",
        location=parcel_data.origin,
        description="Parcel successfully booked"
    )

    db.add(initial_tracking)
    db.commit()
    db.refresh(new_parcel)

    return new_parcel


# ==================================
# GET ALL PARCELS
# ==================================

@router.get(
    "/",
    response_model=list[schemas.ParcelResponse]
)
def get_all_parcels(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    parcels = db.query(Parcel).order_by(
        Parcel.created_at.desc()
    ).all()

    return parcels


# ==================================
# GET SINGLE PARCEL
# ==================================

@router.get(
    "/{parcel_id}",
    response_model=schemas.ParcelResponse
)
def get_parcel(
    parcel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    parcel = db.query(Parcel).filter(
        Parcel.id == parcel_id
    ).first()

    if parcel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parcel not found"
        )

    return parcel


# ==================================
# UPDATE PARCEL STATUS
# ==================================

@router.patch(
    "/{parcel_id}/status",
    response_model=schemas.ParcelResponse
)
def update_parcel_status(
    parcel_id: int,
    update_data: schemas.TrackingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # Find parcel
    parcel = db.query(Parcel).filter(
        Parcel.id == parcel_id
    ).first()

    if parcel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parcel not found"
        )

    # Prevent updates after final status
    if parcel.status in ["DELIVERED", "FAILED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This parcel has reached a final status"
        )

    allowed_transitions = {
        "BOOKED": ["PICKED_UP", "FAILED"],
        "PICKED_UP": ["IN_TRANSIT", "FAILED"],
        "IN_TRANSIT": ["ARRIVED_AT_DESTINATION", "FAILED"],
        "ARRIVED_AT_DESTINATION": ["OUT_FOR_DELIVERY", "FAILED"],
        "OUT_FOR_DELIVERY": ["DELIVERED", "FAILED"]
    }

    if update_data.status not in allowed_transitions.get(
        parcel.status, []
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot change status from {parcel.status} to {update_data.status}"
        )

    # Update current parcel status
    parcel.status = update_data.status

    # Record movement history
    tracking_record = ParcelTracking(
        parcel_id=parcel.id,
        status=update_data.status,
        location=update_data.location,
        description=update_data.description
    )

    db.add(tracking_record)

    db.commit()
    db.refresh(parcel)

    return parcel
