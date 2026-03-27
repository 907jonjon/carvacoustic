from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    api_key: str = "dev-secret"
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    log_level: str = "INFO"


settings = Settings()
