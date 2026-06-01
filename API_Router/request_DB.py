import jwt
import os
import asyncio
import yt_dlp
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from model_DB import Uzytkownik, Media, Gatunek, Film, Serial, tworca_sesji, HistoriaOgladania, Odcinek, StatusOgladania
from API_Router.interfaces import I_Film, I_Serial, I_Konta, I_Szukane_Media, I_Ostatnio_Ogladane, I_Postep, \
    I_Zmiana_Statusu, I_Nastepny_Wideo

sekretny_klucz = os.getenv("KEY_S", "tymczasowy_sekretny_klucz")
algorytm_jwt = "HS256"


async def loguj_przez_id(id_uzytkownika: int) -> Optional[Tuple[str, str]]:
    return await generuj_tokeny_jwt(id_uzytkownika)


async def autoryzuj_uzytkownika(nazwa: str, haslo: Optional[str] = None) -> Optional[Tuple[str, str]]:
    async with tworca_sesji() as sesja:
        zapytanie = select(Uzytkownik).where(Uzytkownik.nazwa_uzytkownika == nazwa)
        wynik = await sesja.execute(zapytanie)
        uzytkownik = wynik.scalar_one_or_none()

        if not uzytkownik:
            return None

        if uzytkownik.czy_admin:
            if not haslo or uzytkownik.haslo_hash != haslo:
                return None

        return await generuj_tokeny_jwt(uzytkownik.id)


async def pobierz_uzytkownika_db(id_uzytkownika: int):
    async with tworca_sesji() as sesja:
        uzytkownik = await sesja.get(Uzytkownik, id_uzytkownika)
        return uzytkownik


async def pobierz_uzytkownikow_nie_adminow() -> List[I_Konta]:
    async with tworca_sesji() as sesja:
        zapytanie = select(Uzytkownik).where(Uzytkownik.czy_admin == False)
        wynik = await sesja.execute(zapytanie)
        uzytkownicy = wynik.scalars().all()

        return [
            I_Konta(
                id=u.id,
                path_avatar=u.sciezka_awatar,
                nazwa=u.nazwa_uzytkownika
            ) for u in uzytkownicy
        ]


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
                ocena=f.ocena_srednia,
                liczba_glosow=f.ocena_glosy,
                czas_trwania=f.czas_trwania,
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
                release_date=s.data_premiery.date() if s.data_premiery else None,
                poster_path=s.plakat_url,
                trailer_url=s.trailer_url,
                ocena=s.ocena_srednia,
                liczba_glosow=s.ocena_glosy,
                czas_trwania=s.czas_trwania,
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
                    numer_odcinka=wpis.odcinek.numer_odcinka if wpis.odcinek else None,
                    odcinek_id=wpis.odcinek_id
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


async def aktualizuj_postep(id_uzytkownika: int, dane_postepu: I_Postep) -> None:
    async with tworca_sesji() as sesja:
        zapytanie_historia = select(HistoriaOgladania).where(
            HistoriaOgladania.uzytkownik_id == id_uzytkownika,
            HistoriaOgladania.media_id == dane_postepu.media_id,
            HistoriaOgladania.odcinek_id == dane_postepu.odcinek_id
        )
        wynik_historia = await sesja.execute(zapytanie_historia)
        historia = wynik_historia.scalar_one_or_none()

        if dane_postepu.calkowity_czas > 0:
            procent = (dane_postepu.aktualny_czas / dane_postepu.calkowity_czas) * 100
        else:
            procent = 5.0

        if procent < 2.0:
            if historia:
                await sesja.delete(historia)
                await sesja.commit()
            return

        status = StatusOgladania.ZAKONCZONE if procent >= 80.0 else StatusOgladania.W_TRAKCIE

        if historia:
            historia.obejrzany_czas = dane_postepu.aktualny_czas
            historia.status = status
        else:
            nowa_historia = HistoriaOgladania(
                uzytkownik_id=id_uzytkownika,
                media_id=dane_postepu.media_id,
                odcinek_id=dane_postepu.odcinek_id,
                obejrzany_czas=dane_postepu.aktualny_czas,
                status=status
            )
            sesja.add(nowa_historia)

        await sesja.commit()


async def reczna_zmiana_statusu(id_uzytkownika: int, dane_zmiany: I_Zmiana_Statusu) -> None:
    async with tworca_sesji() as sesja:
        zapytanie_odcinki = select(Odcinek).where(Odcinek.serial_id == dane_zmiany.media_id)

        if dane_zmiany.numer_sezonu is not None:
            zapytanie_odcinki = zapytanie_odcinki.where(Odcinek.numer_sezonu == dane_zmiany.numer_sezonu)
            if dane_zmiany.numer_odcinka is not None:
                zapytanie_odcinki = zapytanie_odcinki.where(Odcinek.numer_odcinka <= dane_zmiany.numer_odcinka)

        wynik_odcinki = await sesja.execute(zapytanie_odcinki)
        odcinki = wynik_odcinki.scalars().all()

        zapytanie_historia = select(HistoriaOgladania).where(
            HistoriaOgladania.uzytkownik_id == id_uzytkownika,
            HistoriaOgladania.media_id == dane_zmiany.media_id
        )
        wynik_historia = await sesja.execute(zapytanie_historia)
        historia_istniejaca = {h.odcinek_id: h for h in wynik_historia.scalars().all()}

        status_docelowy = StatusOgladania.ZAKONCZONE if dane_zmiany.czy_obejrzane else StatusOgladania.W_TRAKCIE

        for odcinek in odcinki:
            if odcinek.id in historia_istniejaca:
                if not dane_zmiany.czy_obejrzane:
                    await sesja.delete(historia_istniejaca[odcinek.id])
                else:
                    historia_istniejaca[odcinek.id].status = status_docelowy
            elif dane_zmiany.czy_obejrzane:
                nowa_historia = HistoriaOgladania(
                    uzytkownik_id=id_uzytkownika,
                    media_id=dane_zmiany.media_id,
                    odcinek_id=odcinek.id,
                    obejrzany_czas=0.0,
                    status=status_docelowy
                )
                sesja.add(nowa_historia)

        if not odcinki and dane_zmiany.numer_sezonu is None:
            zapytanie_historia_film = select(HistoriaOgladania).where(
                HistoriaOgladania.uzytkownik_id == id_uzytkownika,
                HistoriaOgladania.media_id == dane_zmiany.media_id
            )
            wynik_historia_film = await sesja.execute(zapytanie_historia_film)
            historia_film = wynik_historia_film.scalar_one_or_none()

            if historia_film:
                if not dane_zmiany.czy_obejrzane:
                    await sesja.delete(historia_film)
                else:
                    historia_film.status = status_docelowy
            elif dane_zmiany.czy_obejrzane:
                nowa_historia = HistoriaOgladania(
                    uzytkownik_id=id_uzytkownika,
                    media_id=dane_zmiany.media_id,
                    obejrzany_czas=0.0,
                    status=status_docelowy
                )
                sesja.add(nowa_historia)

        await sesja.commit()


async def pobierz_nastepny_film(id_uzytkownika: int, aktualne_id: int) -> Optional[I_Nastepny_Wideo]:
    async with tworca_sesji() as sesja:
        zapytanie_film = select(Film).where(Film.id > aktualne_id).order_by(Film.id.asc())
        wynik_film = await sesja.execute(zapytanie_film)
        nastepny_film = wynik_film.scalars().first()

        if not nastepny_film:
            zapytanie_film_pierwszy = select(Film).order_by(Film.id.asc())
            wynik_film_pierwszy = await sesja.execute(zapytanie_film_pierwszy)
            nastepny_film = wynik_film_pierwszy.scalars().first()

        if not nastepny_film:
            return None

        czas = await pobierz_czas_wideo(id_uzytkownika, nastepny_film.id)

        return I_Nastepny_Wideo(
            id=nastepny_film.id,
            sciezka_pliku=nastepny_film.sciezka_pliku,
            zapisany_czas=czas
        )


async def pobierz_nastepny_odcinek(id_uzytkownika: int, serial_id: int, numer_sezonu: int, numer_odcinka: int) -> \
Optional[I_Nastepny_Wideo]:
    async with tworca_sesji() as sesja:
        zapytanie_odcinek = select(Odcinek).where(
            Odcinek.serial_id == serial_id,
            Odcinek.numer_sezonu == numer_sezonu,
            Odcinek.numer_odcinka > numer_odcinka
        ).order_by(Odcinek.numer_odcinka.asc())

        wynik_odcinek = await sesja.execute(zapytanie_odcinek)
        nastepny = wynik_odcinek.scalars().first()

        if not nastepny:
            zapytanie_nowy_sezon = select(Odcinek).where(
                Odcinek.serial_id == serial_id,
                Odcinek.numer_sezonu > numer_sezonu
            ).order_by(Odcinek.numer_sezonu.asc(), Odcinek.numer_odcinka.asc())

            wynik_nowy_sezon = await sesja.execute(zapytanie_nowy_sezon)
            nastepny = wynik_nowy_sezon.scalars().first()

        if not nastepny:
            return None

        czas = await pobierz_czas_wideo(id_uzytkownika, serial_id, nastepny.id)

        return I_Nastepny_Wideo(
            id=serial_id,
            sciezka_pliku=nastepny.sciezka_pliku,
            odcinek_id=nastepny.id,
            numer_sezonu=nastepny.numer_sezonu,
            numer_odcinka=nastepny.numer_odcinka,
            zapisany_czas=czas
        )

async def pobierz_czas_wideo(id_uzytkownika: int, media_id: int, odcinek_id: Optional[int] = None) -> float:
    async with tworca_sesji() as sesja:
        zapytanie = select(HistoriaOgladania).where(
            HistoriaOgladania.uzytkownik_id == id_uzytkownika,
            HistoriaOgladania.media_id == media_id,
            HistoriaOgladania.odcinek_id == odcinek_id
        )
        wynik = await sesja.execute(zapytanie)
        historia = wynik.scalar_one_or_none()

        if historia and historia.status == StatusOgladania.W_TRAKCIE:
            return historia.obejrzany_czas
        return 0.0