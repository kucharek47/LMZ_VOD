import jwt
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from model_DB import Uzytkownik, Media, Gatunek, Film, Serial, tworca_sesji, HistoriaOgladania, Odcinek
from interfaces import I_Film, I_Serial, I_Konta, I_Szukane_Media, I_Ostatnio_Ogladane

sekretny_klucz = os.getenv("KEY_S", "tymczasowy_sekretny_klucz")
algorytm_jwt = "HS256"


async def loguj_przez_id(id_uzytkownika: int) -> Optional[Tuple[str, str]]:
    return await generuj_tokeny_jwt(id_uzytkownika)

async def autoryzuj_uzytkownika(nazwa: str, haslo: str) -> Optional[Tuple[str, str]]:
    async with tworca_sesji() as sesja:
        zapytanie = select(Uzytkownik).where(Uzytkownik.nazwa_uzytkownika == nazwa)
        wynik = await sesja.execute(zapytanie)
        uzytkownik = wynik.scalar_one_or_none()

        if not uzytkownik or not uzytkownik.haslo_hash:
            return None

        if uzytkownik.haslo_hash != haslo:
            return None

        return await generuj_tokeny_jwt(uzytkownik.id)

async def pobierz_uzytkownika_db(id_uzytkownika: int):
    async with tworca_sesji() as sesja:
        uzytkownik = await sesja.get(Uzytkownik, id_uzytkownika)
        return uzytkownik

async def generuj_tokeny_jwt(id_uzytkownika: int) -> Optional[Tuple[str, str]]:
    teraz = datetime.now(timezone.utc)

    payload_access = {
        "sub": str(id_uzytkownika),
        "exp": teraz + timedelta(minutes=45),
        "iat": teraz
    }
    access_token = jwt.encode(payload_access, sekretny_klucz, algorithm=algorytm_jwt)

    payload_refresh = {
        "sub": str(id_uzytkownika),
        "exp": teraz + timedelta(days=7),
        "iat": teraz
    }
    refresh_token = jwt.encode(payload_refresh, sekretny_klucz, algorithm=algorytm_jwt)

    async with tworca_sesji() as sesja:
        uzytkownik = await sesja.get(Uzytkownik, id_uzytkownika)
        if uzytkownik:
            uzytkownik.refresh_token = refresh_token
            await sesja.commit()
            return access_token, refresh_token
        return None


async def pobierz_filmy(limit_wynikow: int, nazwa_gatunku: Optional[str] = None) -> List[I_Film]:
    async with tworca_sesji() as sesja:
        zapytanie = select(Film)

        if nazwa_gatunku:
            zapytanie = zapytanie.join(Film.gatunki).where(Gatunek.nazwa == nazwa_gatunku)

        zapytanie = zapytanie.order_by(func.random()).limit(limit_wynikow)
        zapytanie = zapytanie.options(selectinload(Film.gatunki))

        wynik = await sesja.execute(zapytanie)
        filmy = wynik.scalars().all()

        return [
            I_Film(
                id=f.id,
                title=f.tytul,
                description=f.opis,
                release_date=f.data_premiery.date() if f.data_premiery else None,
                poster_path=f.plakat_url,
                trailer_url=f.trailer_url,
                file_path=f.sciezka_pliku,
                genres=[g.nazwa for g in f.gatunki]
            ) for f in filmy
        ]


async def pobierz_seriale(limit_wynikow: int) -> List[I_Serial]:
    async with tworca_sesji() as sesja:
        zapytanie = select(Serial)
        zapytanie = zapytanie.order_by(func.random()).limit(limit_wynikow)
        zapytanie = zapytanie.options(selectinload(Serial.gatunki), selectinload(Serial.odcinki))

        wynik = await sesja.execute(zapytanie)
        seriale = wynik.scalars().all()

        return [
            I_Serial(
                id=s.id,
                title=s.tytul,
                description=s.opis,
                poster_path=s.plakat_url,
                genres=[g.nazwa for g in s.gatunki],
                seasons_count=len(set(o.numer_sezonu for o in s.odcinki)) if s.odcinki else 0
            ) for s in seriale
        ]


async def pobierz_podstawowe_dane_uzytkownikow() -> List[I_Konta]:
    async with tworca_sesji() as sesja:
        zapytanie = select(Uzytkownik)
        wynik = await sesja.execute(zapytanie)
        uzytkownicy = wynik.scalars().all()

        return [
            I_Konta(
                id=u.id,
                path_avatar=u.sciezka_awatar,
                nazwa=u.nazwa_uzytkownika
            ) for u in uzytkownicy
        ]


async def pobierz_path_po_id(id_media: int) -> Optional[str]:
    async with tworca_sesji() as sesja:
        zapytanie = select(Film.sciezka_pliku).where(Film.id == id_media)
        wynik = await sesja.execute(zapytanie)

        return wynik.scalar_one_or_none()


async def szukaj_media_po_tytule(fraza: str) -> List[I_Szukane_Media]:
    async with tworca_sesji() as sesja:
        zapytanie = select(Media).where(Media.tytul.ilike(f"%{fraza}%"))
        zapytanie = zapytanie.options(selectinload(Media.gatunki))

        wynik = await sesja.execute(zapytanie)
        znalezione_media = wynik.scalars().all()

        return [
            I_Szukane_Media(
                id=m.id,
                media_type=m.typ_media,
                title=m.tytul,
                description=m.opis,
                poster_path=m.plakat_url,
                file_path=m.sciezka_pliku if isinstance(m, Film) else None,
                genres=[g.nazwa for g in m.gatunki]
            ) for m in znalezione_media
        ]


async def pobierz_ostatnio_ogladane(id_uzytkownika: int, limit_wynikow: int = 10) -> List[I_Ostatnio_Ogladane]:
    async with tworca_sesji() as sesja:
        zapytanie = (
            select(HistoriaOgladania)
            .where(HistoriaOgladania.uzytkownik_id == id_uzytkownika)
            .order_by(HistoriaOgladania.data_aktualizacji.desc())
            .limit(limit_wynikow)
            .options(
                selectinload(HistoriaOgladania.media),
                selectinload(HistoriaOgladania.odcinek)
            )
        )

        wynik = await sesja.execute(zapytanie)
        historia = wynik.scalars().all()

        lista_wynikow = []
        for wpis in historia:
            lista_wynikow.append(
                I_Ostatnio_Ogladane(
                    media_id=wpis.media.id,
                    tytul=wpis.media.tytul,
                    plakat_url=wpis.media.plakat_url,
                    typ_media=wpis.media.typ_media,
                    obejrzany_czas=wpis.obejrzany_czas,
                    data_aktualizacji=wpis.data_aktualizacji,
                    numer_sezonu=wpis.odcinek.numer_sezonu if wpis.odcinek else None,
                    numer_odcinka=wpis.odcinek.numer_odcinka if wpis.odcinek else None
                )
            )
        return lista_wynikow


async def pobierz_kategorie() -> List[str]:
    async with tworca_sesji() as sesja:
        zapytanie = select(Gatunek.nazwa)
        wynik = await sesja.execute(zapytanie)

        return wynik.scalars().all()


async def pobierz_sciezke_wideo(id_wideo: int, czy_serial: bool = False) -> Optional[str]:
    async with tworca_sesji() as sesja:
        if czy_serial:
            zapytanie = select(Odcinek.sciezka_pliku).where(Odcinek.id == id_wideo)
        else:
            zapytanie = select(Film.sciezka_pliku).where(Film.id == id_wideo)

        wynik = await sesja.execute(zapytanie)
        return wynik.scalar_one_or_none()