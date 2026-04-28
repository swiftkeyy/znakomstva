from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from geoalchemy2 import Geography
from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    age: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    height: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    relationship_goals: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    mbti_type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    attachment_style: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    about_me: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # PostGIS geography point (lon, lat)
    location: Mapped[Optional[object]] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=True
    )
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    verification_level: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    video_profile_file_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    voice_greeting_file_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    boost_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profile")
    photos: Mapped[List["ProfilePhoto"]] = relationship(
        "ProfilePhoto", back_populates="profile", cascade="all, delete-orphan", order_by="ProfilePhoto.position"
    )
    interests: Mapped[List["ProfileInterest"]] = relationship(
        "ProfileInterest", back_populates="profile", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Profile id={self.id} user_id={self.user_id}>"


class ProfilePhoto(Base):
    __tablename__ = "profile_photos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    file_id: Mapped[str] = mapped_column(String(256), nullable=False)
    position: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Integer, default=False, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    profile: Mapped["Profile"] = relationship("Profile", back_populates="photos")

    def __repr__(self) -> str:
        return f"<ProfilePhoto id={self.id} profile_id={self.profile_id}>"


class ProfileInterest(Base):
    __tablename__ = "profile_interests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    interest: Mapped[str] = mapped_column(String(64), nullable=False)

    profile: Mapped["Profile"] = relationship("Profile", back_populates="interests")

    __table_args__ = (
        Index("ix_profile_interests_profile_id", "profile_id"),
    )

    def __repr__(self) -> str:
        return f"<ProfileInterest id={self.id} interest={self.interest!r}>"
