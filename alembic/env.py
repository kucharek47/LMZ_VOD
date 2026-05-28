import asyncio
import os
from logging.config import fileConfig
from dotenv import load_dotenv

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Dzieki zmiennej PYTHONPATH ustawionej w glownym skrypcie, ten import zadziala natywnie
from model_DB import Baza

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Baza.metadata

load_dotenv()
uzytkownik_bazy = os.getenv("POSTGRES_USER", "postgres")
haslo_bazy = os.getenv("POSTGRES_PASSWORD", "postgres")
nazwa_bazy = os.getenv("POSTGRES_DB", "vod_db")
host_bazy = os.getenv("POSTGRES_HOST", "localhost")
port_bazy = os.getenv("POSTGRES_PORT", "5432")

url_bazy_danych = f"postgresql+asyncpg://{uzytkownik_bazy}:{haslo_bazy}@{host_bazy}:{port_bazy}/{nazwa_bazy}"
config.set_main_option("sqlalchemy.url", url_bazy_danych)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    sekcja_konfiguracyjna = config.get_section(config.config_ini_section, {})
    # Wymuszamy nadpisanie URL, aby zignorowal fikcyjny wpis z pliku alembic.ini
    sekcja_konfiguracyjna["sqlalchemy.url"] = config.get_main_option("sqlalchemy.url")

    connectable = async_engine_from_config(
        sekcja_konfiguracyjna,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()