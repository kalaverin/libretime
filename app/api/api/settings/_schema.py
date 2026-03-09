from typing import Literal

from pydantic import BaseModel
from sdk.config import (
    BaseConfig,
    DatabaseConfig,
    GeneralConfig,
    RabbitMQConfig,
    StorageConfig,
)


class EmailConfig(BaseModel):
    from_email: str = "no-reply@libretime.org"

    host: str = "localhost"
    port: int = 25
    user: str = ""
    password: str = ""
    encryption: Literal["ssl/tls", "starttls"] | None = None
    timeout: int | None = None
    key_file: str | None = None
    cert_file: str | None = None


class Config(BaseConfig):
    general: GeneralConfig
    database: DatabaseConfig = DatabaseConfig()
    rabbitmq: RabbitMQConfig = RabbitMQConfig()
    storage: StorageConfig = StorageConfig()
    email: EmailConfig = EmailConfig()
