import os
import asyncio
from sqlalchemy import select
from model_DB import User, tworca_sesji
from API_Router.redis_DB import redis_db

async def stworz_admina():
    nazwa_admina = os.getenv("ADMIN_USERNAME", "admin")
    haslo_admina = os.getenv("ADMIN_PASSWORD_HASH", "domyslne_haslo")

    czy_w_redis = await redis_db.get(f"admin_zainicjowany:{nazwa_admina}")
    if czy_w_redis:
        return

    async with tworca_sesji() as sesja:
        wynik = await sesja.execute(select(User).where(User.username == nazwa_admina))
        istniejacy_admin = wynik.scalar_one_or_none()

        if not istniejacy_admin:
            nowy_admin = User(
                username=nazwa_admina,
                password_hash=haslo_admina,
                is_admin=True
            )
            sesja.add(nowy_admin)
            await sesja.commit()

        await redis_db.set(f"admin_zainicjowany:{nazwa_admina}", "ok")

async def wypisz_uzytkownikow():
    async with tworca_sesji() as sesja:
        wynik = await sesja.execute(select(User))
        uzytkownicy = wynik.scalars().all()

        for uzytkownik in uzytkownicy:
            print(f"id: {uzytkownik.id}, nazwa: {uzytkownik.username}, czy_admin: {uzytkownik.is_admin}")

async def autoryzuj_uzytkownika():
    return True

async def pobierz_uzytkownika():
    pass

async def pobierz_wideo_info():
    pass

if __name__ == '__main__':
    asyncio.run(wypisz_uzytkownikow())