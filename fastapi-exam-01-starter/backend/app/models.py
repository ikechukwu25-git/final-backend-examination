
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


# ==================================
# USER MODEL
# ==================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String(100), nullable=False)

    email = Column(String(150), unique=True, index=True, nullable=False)

    hashed_password = Column(String(255), nullable=False)

    is_active = Column(Boolean, default=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationship with parcels
    parcels = relationship("Parcel", back_populates="staff")


# ==================================
# PARCEL MODEL
# ==================================

class Parcel(Base):
    __tablename__ = "parcels"

    id = Column(Integer, primary_key=True, index=True)

    tracking_code = Column(
        String(30),
        unique=True,
        index=True,
        nullable=False
    )

    # Sender information
    sender_name = Column(String(100), nullable=False)
    sender_phone = Column(String(20), nullable=False)

    # Receiver information
    receiver_name = Column(String(100), nullable=False)
    receiver_phone = Column(String(20), nullable=False)

    # Parcel information
    description = Column(Text, nullable=False)
    weight = Column(Integer, nullable=False)

    # Delivery locations
    origin = Column(String(50), nullable=False)
    destination = Column(String(50), nullable=False)

    # Current delivery status
    status = Column(String(50), default="BOOKED")

    # Staff member who booked the parcel
    staff_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    staff = relationship("User", back_populates="parcels")

    tracking_history = relationship(
        "ParcelTracking",
        back_populates="parcel",
        cascade="all, delete-orphan",
        order_by="ParcelTracking.created_at"
    )


# ==================================
# PARCEL TRACKING MODEL
# ==================================

class ParcelTracking(Base):
    __tablename__ = "parcel_tracking"

    id = Column(Integer, primary_key=True, index=True)

    parcel_id = Column(
        Integer,
        ForeignKey("parcels.id"),
        nullable=False
    )

    status = Column(String(50), nullable=False)

    location = Column(String(100), nullable=False)

    description = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationship
    parcel = relationship(
        "Parcel",
        back_populates="tracking_history"
    )
