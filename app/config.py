import os

from dotenv import load_dotenv


load_dotenv()


class Settings:
    app_name = "Furs and Fur Coats API"
    
    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db = os.getenv("POSTGRES_DB", "furs")
    postgres_user = os.getenv("POSTGRES_USER", "postgres")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "1234")

    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    jwt_secret_key = os.getenv("JWT_SECRET_KEY", "dev-secret")
    jwt_expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

    yandex_client_id = os.getenv("YANDEX_CLIENT_ID", "")
    yandex_client_secret = os.getenv("YANDEX_CLIENT_SECRET", "")
    yandex_client_redirect_uri = os.getenv("YANDEX_REDIRECT_URI", "")
    yandex_auth_url = os.getenv("YANDEX_AUTH_URL", "https://oauth.yandex.ru/authorize")
    yandex_token_url = os.getenv("YANDEX_TOKEN_URL", "https://oauth.yandex.ru/token")
    yandex_user_info_url = os.getenv("YANDEX_USER_INFO_URL", "https://login.yandex.ru/info")

    oauth_refresh_token_ttl_seconds = int(os.getenv("OAUTH_REFRESH_TOKEN_TTL_SECONDS", str(60 * 60 * 24 * 30)))



settings = Settings()
