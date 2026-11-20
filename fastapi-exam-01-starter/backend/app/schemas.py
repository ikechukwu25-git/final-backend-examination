
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Literal, Optional


# ==================================
# DELIVERY OPTIONS
# ==================================

City = Literal[
    "Awka",
    "Onitsha",
    "Nnewi",
    "Enugu",
    "Asaba",
    "Owerri"
]

ParcelStatus = Literal[
    "BOOKED",
    "PICKED_UP",
    "IN_TRANSIT",
    "ARRIVED_AT_DESTINATION",
    "OUT_FOR_DELIVERY",
    "DELIVERED",
    "FAILED"
]


# ==================================
# USER SCHEMAS
# ==================================

class UserCreate(BaseModel):
    full_name: str = Field(min_length=3, max_length=100)

    email: EmailStr

    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================================
# TOKEN SCHEMA
# ==================================

class Token(BaseModel):
    access_token: str
    token_type: str


# ==================================
# PARCEL SCHEMAS
# ==================================

class ParcelCreate(BaseModel):
    sender_name: str = Field(min_length=2, max_length=100)
    sender_phone: str = Field(min_length=7, max_length=20)

    receiver_name: str = Field(min_length=2, max_length=100)
    receiver_phone: str = Field(min_length=7, max_length=20)

    description: str = Field(min_length=3)

    # Weight is recorded in grams
    weight: int = Field(gt=0)

    origin: City
    destination: City


class TrackingUpdate(BaseModel):
    status: ParcelStatus

    location: City

    description: Optional[str] = None


# ==================================
# TRACKING RESPONSE SCHEMAS
# ==================================

class TrackingResponse(BaseModel):
    id: int
    status: str
    location: str
    description: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================================
# PARCEL RESPONSE SCHEMA
# ==================================

class ParcelResponse(BaseModel):
    id: int
    tracking_code: str

    sender_name: str
    sender_phone: str

    receiver_name: str
    receiver_phone: str

    description: str
    weight: int

    origin: str
    destination: str

    status: str

    staff_id: int

    created_at: datetime
    updated_at: datetime

    tracking_history: list[TrackingResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ==================================
# PUBLIC TRACKING RESPONSE
# ==================================

class PublicTrackingResponse(BaseModel):
    tracking_code: str
    sender_name: str
    receiver_name: str
    origin: str
    destination: str
    status: str
    created_at: datetime
    tracking_history: list[TrackingResponse] = []

    model_config = ConfigDict(from_attributes=True)
