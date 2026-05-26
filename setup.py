import os
import getpass
import bcrypt

slownik_tekstow = {
    "en": {
        "lang_prompt": "Select language (1: EN, 2: PL, 3: ES, 4: FR, 5: ZH) [1]: ",
        "port": "Enter application port [13008]: ",
        "movies_path": "Enter physical path to movies: ",
        "series_path": "Enter physical path to series: ",
        "tmdb_mode": "Select metadata mode (TMDB/MANUAL/BASIC) [TMDB]: ",
        "tmdb_key": "Enter TMDB API Key (leave empty if not TMDB): ",
        "downloads": "Enable downloads? (true/false) [false]: ",
        "pg_user": "Enter PostgreSQL user [postgres]: ",
        "pg_pass": "Enter PostgreSQL password: ",
        "pg_db": "Enter PostgreSQL database name [vod_db]: ",
        "redis_url": "Enter Redis URL [redis://redis_cache:6379/0]: ",
        "admin_user": "Enter Admin username [admin]: ",
        "admin_pass": "Enter Admin password: ",
        "demo_db": "Enable DEMO_DB with test data? (true/false) [false]: ",
        "delivery": "Select Delivery Method (STREAMING/DIRECT_FILE) [STREAMING]: ",
        "ets3": "Enable ETS3_SUPPORT for older devices? (true/false) [false]: ",
        "done": ".env file generated successfully."
    },
    "pl": {
        "lang_prompt": "Wybierz język (1: EN, 2: PL, 3: ES, 4: FR, 5: ZH) [1]: ",
        "port": "Podaj port aplikacji [13008]: ",
        "movies_path": "Podaj fizyczną ścieżkę do filmów: ",
        "series_path": "Podaj fizyczną ścieżkę do seriali: ",
        "tmdb_mode": "Wybierz tryb metadanych (TMDB/MANUAL/BASIC) [TMDB]: ",
        "tmdb_key": "Podaj klucz API TMDB (zostaw puste, jeśli inny tryb): ",
        "downloads": "Włączyć pobieranie plików? (true/false) [false]: ",
        "pg_user": "Podaj użytkownika PostgreSQL [postgres]: ",
        "pg_pass": "Podaj hasło PostgreSQL: ",
        "pg_db": "Podaj nazwę bazy PostgreSQL [vod_db]: ",
        "redis_url": "Podaj adres Redis [redis://redis_cache:6379/0]: ",
        "admin_user": "Podaj nazwę administratora [admin]: ",
        "admin_pass": "Podaj hasło administratora: ",
        "demo_db": "Włączyć DEMO_DB z danymi testowymi? (true/false) [false]: ",
        "delivery": "Wybierz metodę dostarczania (STREAMING/DIRECT_FILE) [STREAMING]: ",
        "ets3": "Włączyć ETS3_SUPPORT dla starszych urządzeń? (true/false) [false]: ",
        "done": "Plik .env wygenerowany pomyślnie."
    },
    "es": {
        "lang_prompt": "Seleccione el idioma (1: EN, 2: PL, 3: ES, 4: FR, 5: ZH) [1]: ",
        "port": "Ingrese el puerto de la aplicación [13008]: ",
        "movies_path": "Ingrese la ruta física a las películas: ",
        "series_path": "Ingrese la ruta física a las series: ",
        "tmdb_mode": "Seleccione el modo (TMDB/MANUAL/BASIC) [TMDB]: ",
        "tmdb_key": "Ingrese la clave API de TMDB: ",
        "downloads": "Habilitar descargas? (true/false) [false]: ",
        "pg_user": "Usuario de PostgreSQL [postgres]: ",
        "pg_pass": "Contraseña de PostgreSQL: ",
        "pg_db": "Base de datos PostgreSQL [vod_db]: ",
        "redis_url": "URL de Redis [redis://redis_cache:6379/0]: ",
        "admin_user": "Usuario administrador [admin]: ",
        "admin_pass": "Contraseña administrador: ",
        "demo_db": "Habilitar DEMO_DB? (true/false) [false]: ",
        "delivery": "Método de entrega (STREAMING/DIRECT_FILE) [STREAMING]: ",
        "ets3": "Habilitar ETS3_SUPPORT? (true/false) [false]: ",
        "done": "Archivo .env generado con éxito."
    },
    "fr": {
        "lang_prompt": "Sélectionnez la langue (1: EN, 2: PL, 3: ES, 4: FR, 5: ZH) [1]: ",
        "port": "Entrez le port de l'application [13008]: ",
        "movies_path": "Chemin physique des films: ",
        "series_path": "Chemin physique des séries: ",
        "tmdb_mode": "Mode de métadonnées (TMDB/MANUAL/BASIC) [TMDB]: ",
        "tmdb_key": "Clé API TMDB: ",
        "downloads": "Activer les téléchargements? (true/false) [false]: ",
        "pg_user": "Utilisateur PostgreSQL [postgres]: ",
        "pg_pass": "Mot de passe PostgreSQL: ",
        "pg_db": "Base de données PostgreSQL [vod_db]: ",
        "redis_url": "URL Redis [redis://redis_cache:6379/0]: ",
        "admin_user": "Nom d'utilisateur admin [admin]: ",
        "admin_pass": "Mot de passe admin: ",
        "demo_db": "Activer DEMO_DB? (true/false) [false]: ",
        "delivery": "Méthode de livraison (STREAMING/DIRECT_FILE) [STREAMING]: ",
        "ets3": "Activer ETS3_SUPPORT? (true/false) [false]: ",
        "done": "Fichier .env généré avec succès."
    },
    "zh": {
        "lang_prompt": "选择语言 (1: EN, 2: PL, 3: ES, 4: FR, 5: ZH) [1]: ",
        "port": "输入应用程序端口 [13008]: ",
        "movies_path": "输入电影的物理路径: ",
        "series_path": "输入系列剧的物理路径: ",
        "tmdb_mode": "选择元数据模式 (TMDB/MANUAL/BASIC) [TMDB]: ",
        "tmdb_key": "输入 TMDB API 密钥: ",
        "downloads": "启用下载？(true/false) [false]: ",
        "pg_user": "输入 PostgreSQL 用户 [postgres]: ",
        "pg_pass": "输入 PostgreSQL 密码: ",
        "pg_db": "输入 PostgreSQL 数据库名称 [vod_db]: ",
        "redis_url": "输入 Redis URL [redis://redis_cache:6379/0]: ",
        "admin_user": "输入管理员用户名 [admin]: ",
        "admin_pass": "输入管理员密码: ",
        "demo_db": "启用 DEMO_DB？(true/false) [false]: ",
        "delivery": "选择交付方法 (STREAMING/DIRECT_FILE) [STREAMING]: ",
        "ets3": "启用 ETS3_SUPPORT？(true/false) [false]: ",
        "done": ".env 文件成功生成。"
    }
}


def glowna_funkcja():
    wybor_jezyka = input(slownik_tekstow["en"]["lang_prompt"]).strip()
    mapa_jezykow = {"1": "en", "2": "pl", "3": "es", "4": "fr", "5": "zh"}
    wybrany_jezyk = mapa_jezykow.get(wybor_jezyka, "en")
    teksty = slownik_tekstow[wybrany_jezyk]

    port_aplikacji = input(teksty["port"]).strip() or "13008"
    sciezka_filmy = input(teksty["movies_path"]).strip()
    sciezka_seriale = input(teksty["series_path"]).strip()
    tryb_tmdb = input(teksty["tmdb_mode"]).strip().upper() or "TMDB"

    klucz_tmdb = ""
    if tryb_tmdb == "TMDB":
        klucz_tmdb = input(teksty["tmdb_key"]).strip()

    pobieranie_plikow = input(teksty["downloads"]).strip().lower() or "false"
    uzytkownik_pg = input(teksty["pg_user"]).strip() or "postgres"
    haslo_pg = input(teksty["pg_pass"]).strip()
    baza_pg = input(teksty["pg_db"]).strip() or "vod_db"

    nazwa_admina = input(teksty["admin_user"]).strip() or "admin"
    haslo_admina = input(teksty["admin_pass"]).strip()

    tryb_demo = input(teksty["demo_db"]).strip().lower() or "false"
    metoda_dostarczania = input(teksty["delivery"]).strip().upper() or "STREAMING"
    wsparcie_ets3 = input(teksty["ets3"]).strip().lower() or "false"

    zawartosc_env = f"""APP_PORT={port_aplikacji}
PATH_FILMS={sciezka_filmy}
PATH_SERIALS={sciezka_seriale}
METADATA_MODE={tryb_tmdb}
TMDB_API_KEY={klucz_tmdb}
ENABLE_DOWNLOADS={pobieranie_plikow}
POSTGRES_USER={uzytkownik_pg}
POSTGRES_PASSWORD={haslo_pg}
POSTGRES_DB={baza_pg}
ADMIN_USERNAME={nazwa_admina}
ADMIN_PASSWORD_HASH={haslo_admina}
DEMO_DB={tryb_demo}
DELIVERY_METHOD={metoda_dostarczania}
ETS3_SUPPORT={wsparcie_ets3}
"""

    with open(".env", "w", encoding="utf-8") as plik_env:
        plik_env.write(zawartosc_env)

    print(teksty["done"])


if __name__ == "__main__":
    glowna_funkcja()