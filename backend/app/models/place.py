"""ORM models: User, Place, PlaceEmbedding, RecognitionEvent, Itinerary."""
import uuid
from datetime import datetime
from sqlalchemy import String, Float, Integer, Text, DateTime, ForeignKey, JSON, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.database import Base


def _uuid():
    return str(uuid.uuid4())


# ── Users ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    itineraries: Mapped[list["Itinerary"]] = relationship(back_populates="user")
    recognition_events: Mapped[list["RecognitionEvent"]] = relationship(back_populates="user")


# ── Places ────────────────────────────────────────────────────────────────────

class Place(Base):
    __tablename__ = "places"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(100))
    lat: Mapped[float | None] = mapped_column(Float)
    lng: Mapped[float | None] = mapped_column(Float)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(50))
    place_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict)

    embeddings: Mapped[list["PlaceEmbedding"]] = relationship(back_populates="place")
    itineraries: Mapped[list["Itinerary"]] = relationship(back_populates="place")


class PlaceEmbedding(Base):
    __tablename__ = "place_embeddings"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    place_id: Mapped[str] = mapped_column(ForeignKey("places.id"), nullable=False)
    embedding: Mapped[list] = mapped_column(Vector(512), nullable=False)
    source_image_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    place: Mapped[Place] = relationship(back_populates="embeddings")


# ── Recognition Events ────────────────────────────────────────────────────────

class RecognitionEvent(Base):
    __tablename__ = "recognition_events"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    task_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    image_s3_key: Mapped[str | None] = mapped_column(Text)
    result_place_id: Mapped[str | None] = mapped_column(ForeignKey("places.id"))
    confidence: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User | None] = relationship(back_populates="recognition_events")


# ── Itineraries ───────────────────────────────────────────────────────────────

class Itinerary(Base):
    __tablename__ = "itineraries"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    place_id: Mapped[str | None] = mapped_column(ForeignKey("places.id"))
    title: Mapped[str | None] = mapped_column(String(255))
    duration_days: Mapped[int | None] = mapped_column(SmallInteger)
    plan: Mapped[dict] = mapped_column(JSON, nullable=False)
    preferences_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User | None] = relationship(back_populates="itineraries")
    place: Mapped[Place | None] = relationship(back_populates="itineraries")
