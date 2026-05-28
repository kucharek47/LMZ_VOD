import asyncio
import os
import enum
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Boolean, ForeignKey, Integer, Float, DateTime, Text, Table, Column
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
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


class Baza(DeclarativeBase):
    pass


media_gatunki = Table(
    "media_gatunki",
    Baza.metadata,
    Column("media_id", ForeignKey("media.id", ondelete="CASCADE"), primary_key=True),
    Column("gatunek_id", ForeignKey("gatunki.id", ondelete="CASCADE"), primary_key=True),
)


class StatusOgladania(str, enum.Enum):
    W_TRAKCIE = "w_trakcie"
    ZAKONCZONE = "zakonczone"


class TypZdarzenia(str, enum.Enum):
    PLAY = "PLAY"
    PAUSE = "PAUSE"
    SEEK = "SEEK"
    HOVER_HERO = "HOVER_HERO"


class Uzytkownik(Baza):
    __tablename__ = "uzytkownicy"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nazwa_uzytkownika: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    haslo_hash: Mapped[str] = mapped_column(String(255), nullable=True)
    czy_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    sciezka_awatar: Mapped[str] = mapped_column(String(255), default="default.png")
    refresh_token: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    historia_ogladania: Mapped[List["HistoriaOgladania"]] = relationship(back_populates="uzytkownik",
                                                                         cascade="all, delete-orphan")
    telemetria: Mapped[List["Telemetria"]] = relationship(back_populates="uzytkownik", cascade="all, delete-orphan")


class Gatunek(Baza):
    __tablename__ = "gatunki"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tmdb_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=True)
    nazwa: Mapped[str] = mapped_column(String(50), unique=True)

    media: Mapped[List["Media"]] = relationship(secondary=media_gatunki, back_populates="gatunki")


class Osoba(Baza):
    __tablename__ = "osoby"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tmdb_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=True)
    imie_nazwisko: Mapped[str] = mapped_column(String(150), index=True)
    zdjecie_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    role_wideo: Mapped[List["RolaWideo"]] = relationship(back_populates="osoba", cascade="all, delete-orphan")


class Media(Baza):
    __tablename__ = "media"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tmdb_id: Mapped[Optional[int]] = mapped_column(Integer, unique=True, index=True, nullable=True)
    typ_media: Mapped[str] = mapped_column(String(20), index=True)
    tytul: Mapped[str] = mapped_column(String(255), index=True)
    opis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data_premiery: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    plakat_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    trailer_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ocena_srednia: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ocena_glosy: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    czas_trwania: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    data_dodania: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __mapper_args__ = {
        "polymorphic_on": "typ_media",
        "polymorphic_identity": "media",
    }

    gatunki: Mapped[List["Gatunek"]] = relationship(secondary=media_gatunki, back_populates="media")
    role_wideo: Mapped[List["RolaWideo"]] = relationship(back_populates="media", cascade="all, delete-orphan")
    historia_ogladania: Mapped[List["HistoriaOgladania"]] = relationship(back_populates="media",
                                                                         cascade="all, delete-orphan")
    telemetria: Mapped[List["Telemetria"]] = relationship(back_populates="media", cascade="all, delete-orphan")
    napisy: Mapped[List["Napisy"]] = relationship(back_populates="media", cascade="all, delete-orphan")


class Film(Media):
    __mapper_args__ = {
        "polymorphic_identity": "film",
    }

    sciezka_pliku: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    offset_intro: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    offset_outro: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class Serial(Media):
    __mapper_args__ = {
        "polymorphic_identity": "serial",
    }

    odcinki: Mapped[List["Odcinek"]] = relationship(back_populates="serial", cascade="all, delete-orphan")


class Odcinek(Baza):
    __tablename__ = "odcinki"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    serial_id: Mapped[int] = mapped_column(ForeignKey("media.id", ondelete="CASCADE"), index=True)
    numer_sezonu: Mapped[int] = mapped_column(Integer)
    numer_odcinka: Mapped[int] = mapped_column(Integer)
    tytul: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    opis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sciezka_pliku: Mapped[str] = mapped_column(String(512))
    offset_intro: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    offset_outro: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    data_dodania: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    serial: Mapped["Serial"] = relationship(back_populates="odcinki")
    historia_ogladania: Mapped[List["HistoriaOgladania"]] = relationship(back_populates="odcinek",
                                                                         cascade="all, delete-orphan")
    napisy: Mapped[List["Napisy"]] = relationship(back_populates="odcinek", cascade="all, delete-orphan")


class RolaWideo(Baza):
    __tablename__ = "role_wideo"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    media_id: Mapped[int] = mapped_column(ForeignKey("media.id", ondelete="CASCADE"), index=True)
    osoba_id: Mapped[int] = mapped_column(ForeignKey("osoby.id", ondelete="CASCADE"), index=True)
    funkcja: Mapped[str] = mapped_column(String(50))
    nazwa_postaci: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    media: Mapped["Media"] = relationship(back_populates="role_wideo")
    osoba: Mapped["Osoba"] = relationship(back_populates="role_wideo")


class Napisy(Baza):
    __tablename__ = "napisy"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    media_id: Mapped[Optional[int]] = mapped_column(ForeignKey("media.id", ondelete="CASCADE"), index=True,
                                                    nullable=True)
    odcinek_id: Mapped[Optional[int]] = mapped_column(ForeignKey("odcinki.id", ondelete="CASCADE"), index=True,
                                                      nullable=True)
    sciezka_pliku: Mapped[str] = mapped_column(String(512))
    jezyk: Mapped[str] = mapped_column(String(10), default="pl")

    media: Mapped[Optional["Media"]] = relationship(back_populates="napisy")
    odcinek: Mapped[Optional["Odcinek"]] = relationship(back_populates="napisy")


class HistoriaOgladania(Baza):
    __tablename__ = "historia_ogladania"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    uzytkownik_id: Mapped[int] = mapped_column(ForeignKey("uzytkownicy.id", ondelete="CASCADE"), index=True)
    media_id: Mapped[int] = mapped_column(ForeignKey("media.id", ondelete="CASCADE"), index=True)
    odcinek_id: Mapped[Optional[int]] = mapped_column(ForeignKey("odcinki.id", ondelete="CASCADE"), index=True,
                                                      nullable=True)
    obejrzany_czas: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[StatusOgladania] = mapped_column(String(20), default=StatusOgladania.W_TRAKCIE)
    data_aktualizacji: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                        default=lambda: datetime.now(timezone.utc),
                                                        onupdate=lambda: datetime.now(timezone.utc))

    uzytkownik: Mapped["Uzytkownik"] = relationship(back_populates="historia_ogladania")
    media: Mapped["Media"] = relationship(back_populates="historia_ogladania")
    odcinek: Mapped[Optional["Odcinek"]] = relationship(back_populates="historia_ogladania")


class Telemetria(Baza):
    __tablename__ = "telemetria"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    uzytkownik_id: Mapped[int] = mapped_column(ForeignKey("uzytkownicy.id", ondelete="CASCADE"), index=True)
    media_id: Mapped[Optional[int]] = mapped_column(ForeignKey("media.id", ondelete="CASCADE"), index=True,
                                                    nullable=True)
    typ_zdarzenia: Mapped[TypZdarzenia] = mapped_column(String(20))
    czas_trwania_sekundy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    data_zdarzenia: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                     default=lambda: datetime.now(timezone.utc))

    uzytkownik: Mapped["Uzytkownik"] = relationship(back_populates="telemetria")
    media: Mapped[Optional["Media"]] = relationship(back_populates="telemetria")


class NierozpoznaneMedia(Baza):
    __tablename__ = "nierozpoznane_media"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sciezka_pliku: Mapped[str] = mapped_column(String(512), unique=True)
    wykryty_tytul: Mapped[str] = mapped_column(String(255))
    data_wykrycia: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


async def utworz_tabele():
    async with silnik_bazy.begin() as polaczenie:
        await polaczenie.run_sync(Baza.metadata.create_all)
    await silnik_bazy.dispose()


if __name__ == '__main__':
    asyncio.run(utworz_tabele())