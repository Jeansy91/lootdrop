from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # SMTP
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "Free Games"
    smtp_from_email: str = ""
    smtp_use_tls: bool = True

    # Admin
    admin_username: str = "admin"
    admin_password: str = "changeme123"

    # App
    secret_key: str = "change-this-to-a-long-random-secret-string"
    base_url: str = "http://localhost:8000"
    database_path: str = "/data/lootdrop.db"

    # Scheduler
    email_hour: int = 9
    email_minute: int = 0

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
