import os

from dotenv import load_dotenv
from urllib.parse import urlparse


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
    redis_db = int(os.getenv("REDIS_DB", "0"))

    jwt_secret_key = os.getenv("JWT_SECRET_KEY", "dev-secret")
    jwt_expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
    oauth_refresh_token_ttl_seconds = int(os.getenv("OAUTH_REFRESH_TOKEN_TTL_SECONDS", str(60 * 60 * 24 * 30)))

    yandex_client_id = os.getenv("YANDEX_CLIENT_ID", "")
    yandex_client_secret = os.getenv("YANDEX_CLIENT_SECRET", "")
    yandex_client_redirect_uri = os.getenv("YANDEX_REDIRECT_URI", "")
    yandex_auth_url = os.getenv("YANDEX_AUTH_URL", "https://oauth.yandex.ru/authorize")
    yandex_token_url = os.getenv("YANDEX_TOKEN_URL", "https://oauth.yandex.ru/token")
    yandex_user_info_url = os.getenv("YANDEX_USER_INFO_URL", "https://login.yandex.ru/info")

    dadata_api_key = os.getenv("DADATA_API_KEY", "")
    dadata_secret_key = os.getenv("DADATA_SECRET_KEY", "")
    dadata_timeout = float(os.getenv("DADATA_TIMEOUT", "5"))
    dadata_retry_count = int(os.getenv("DADATA_RETRY_COUNT", "3"))
    dadata_retry_delay = float(os.getenv("DADATA_RETRY_DELAY", "1"))

    openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    openrouter_model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    openrouter_timeout = float(os.getenv("OPENROUTER_TIMEOUT", "30"))
    openrouter_temperature = float(os.getenv("OPENROUTER_TEMPERATURE", "0.2"))
    openrouter_prompt_version = os.getenv("OPENROUTER_PROMPT_VERSION", "v1")

    celery_broker_url = os.getenv("CELERY_BROKER_URL", "")
    celery_result_backend = os.getenv("CELERY_RESULT_BACKEND", "")
    celery_task_time_limit = int(os.getenv("CELERY_TASK_TIME_LIMIT", "120"))
    celery_task_soft_time_limit = int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "90"))
    celery_retry_count = int(os.getenv("CELERY_RETRY_COUNT", "3"))
    celery_retry_backoff = int(os.getenv("CELERY_RETRY_BACKOFF", "2"))
    celery_retry_backoff_max = int(os.getenv("CELERY_RETRY_BACKOFF_MAX", "30"))
    generation_lock_ttl_seconds = int(os.getenv("GENERATION_LOCK_TTL_SECONDS", "300"))

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def resolved_celery_broker_url(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def resolved_celery_result_backend(self) -> str:
        return self.celery_result_backend or self.redis_url

    @property
    def openrouter_referer(self) -> str:
        return os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost")

    @property
    def openrouter_title(self) -> str:
        parsed = urlparse(self.openrouter_referer)
        return os.getenv("OPENROUTER_X_TITLE", parsed.netloc or self.app_name)




settings = Settings()
