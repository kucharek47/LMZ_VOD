import asyncio
import os
import enum
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import String, Boolean, ForeignKey, Integer, Float, DateTime, Text, Table, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from dotenv import load_dotenv

load_dotenv()

uzytkownik_bazy = os.getenv("POSTGRES_USER", "postgres")
haslo_bazy = os.getenv("POSTGRES_PASSWORD", "postgres")
nazwa_bazy = os.getenv("POSTGRES_DB", "vod_db")
host_bazy = os.getenv("POSTGRES_HOST", "localhost")
port_bazy = os.getenv("POSTGRES_PORT", "5432")

url_bazy_danych = f"postgresql+asyncpg://{uzytkownik_bazy}:{haslo_bazy}@{host_bazy}:{port_bazy}/{nazwa_bazy}"

silnik_bazy = create_async_engine(url_bazy_danych, echo=False)
tworca_sesji = async_sessionmaker(silnik_bazy, class_=AsyncSession, expire_on_commit=False)

async def pobierz_baze():
    async with tworca_sesji() as sesja:
        yield sesja

class Base(DeclarativeBase):
    pass

media_genres = Table(
    "media_genres",
    Base.metadata,
    Column("media_id", ForeignKey("media.id", ondelete="CASCADE"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)

class MediaType(str, enum.Enum):
    MOVIE = "movie"
    TV = "tv"

class EventType(str, enum.Enum):
    PLAY = "PLAY"
    PAUSE = "PAUSE"
    SEEK = "SEEK"
    HOVER_HERO = "HOVER_HERO"

class WatchStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    avatar_path: Mapped[str] = mapped_column(String(255), default="default.png")

    watch_history: Mapped[List["WatchHistory"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    telemetry_events: Mapped[List["TelemetryEvent"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)

    media: Mapped[List["Media"]] = relationship(secondary=media_genres, back_populates="genres")

class Media(Base):
    __tablename__ = "media"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    media_type: Mapped[MediaType] = mapped_column(String(10), index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    release_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    poster_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    trailer_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    genres: Mapped[List["Genre"]] = relationship(secondary=media_genres, back_populates="media")
    seasons: Mapped[List["Season"]] = relationship(back_populates="media", cascade="all, delete-orphan")
    subtitles: Mapped[List["Subtitle"]] = relationship(back_populates="media", cascade="all, delete-orphan")
    watch_history: Mapped[List["WatchHistory"]] = relationship(back_populates="media", cascade="all, delete-orphan")
    telemetry_events: Mapped[List["TelemetryEvent"]] = relationship(back_populates="media", cascade="all, delete-orphan")

class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    media_id: Mapped[int] = mapped_column(ForeignKey("media.id", ondelete="CASCADE"), index=True)
    season_number: Mapped[int] = mapped_column(Integer)

    media: Mapped["Media"] = relationship(back_populates="seasons")
    episodes: Mapped[List["Episode"]] = relationship(back_populates="season", cascade="all, delete-orphan")

class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id", ondelete="CASCADE"), index=True)
    episode_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_path: Mapped[str] = mapped_column(String(512))

    season: Mapped["Season"] = relationship(back_populates="episodes")
    watch_history: Mapped[List["WatchHistory"]] = relationship(back_populates="episode", cascade="all, delete-orphan")
    subtitles: Mapped[List["Subtitle"]] = relationship(back_populates="episode", cascade="all, delete-orphan")

class Subtitle(Base):
    __tablename__ = "subtitles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    media_id: Mapped[Optional[int]] = mapped_column(ForeignKey("media.id", ondelete="CASCADE"), index=True, nullable=True)
    episode_id: Mapped[Optional[int]] = mapped_column(ForeignKey("episodes.id", ondelete="CASCADE"), index=True, nullable=True)
    file_path: Mapped[str] = mapped_column(String(512))
    language: Mapped[str] = mapped_column(String(10), default="en")
    intro_skip_offset: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    outro_skip_offset: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    media: Mapped[Optional["Media"]] = relationship(back_populates="subtitles")
    episode: Mapped[Optional["Episode"]] = relationship(back_populates="subtitles")

class WatchHistory(Base):
    __tablename__ = "watch_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    media_id: Mapped[int] = mapped_column(ForeignKey("media.id", ondelete="CASCADE"), index=True)
    episode_id: Mapped[Optional[int]] = mapped_column(ForeignKey("episodes.id", ondelete="CASCADE"), index=True, nullable=True)
    watched_time: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[WatchStatus] = mapped_column(String(20), default=WatchStatus.IN_PROGRESS)

    user: Mapped["User"] = relationship(back_populates="watch_history")
    media: Mapped["Media"] = relationship(back_populates="watch_history")
    episode: Mapped[Optional["Episode"]] = relationship(back_populates="watch_history")

class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    media_id: Mapped[int] = mapped_column(ForeignKey("media.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[EventType] = mapped_column(String(20))
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="telemetry_events")
    media: Mapped["Media"] = relationship(back_populates="telemetry_events")

class UnmatchedMedia(Base):
    __tablename__ = "unmatched_media"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    file_path: Mapped[str] = mapped_column(String(512), unique=True)
    detected_title: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


async def create_tables():
    url_bazy_danych_async = f"postgresql+asyncpg://{uzytkownik_bazy}:{haslo_bazy}@{host_bazy}:{port_bazy}/{nazwa_bazy}"
    print(url_bazy_danych_async)

    silnik_bazy_async = create_async_engine(url_bazy_danych_async, echo=False)

    async with silnik_bazy_async.begin() as polaczenie:
        await polaczenie.run_sync(Base.metadata.create_all)

    await silnik_bazy_async.dispose()


if __name__ == '__main__':
    asyncio.run(create_tables())