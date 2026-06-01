from pydantic_settings import BaseSettings
from functools import lru_cache
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List

_db_client: Optional[AsyncIOMotorClient] = None
_db = None


class Settings(BaseSettings):
    mongodb_uri: str
    jwt_secret: str
    resend_api_key: str
    operator_api_key: str
    operator_notification_email: str = "hello@smallburg.ca"
    magic_link_base_url: str = "https://smallburg.ca/onboarding"
    magic_link_expiry_hours: int = 24
    cors_origins: str = "https://smallburg.ca"

    def get_cors_origins(self) -> List[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        # Always include localhost for dev
        if "http://localhost:3000" not in origins:
            origins.append("http://localhost:3000")
        if "http://localhost:8080" not in origins:
            origins.append("http://localhost:8080")
        return origins

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_db():
    return _db


async def connect_db():
    global _db_client, _db
    settings = get_settings()
    _db_client = AsyncIOMotorClient(settings.mongodb_uri)
    _db = _db_client["smallburg"]

    await _db.claims.create_index("email")
    await _db.claims.create_index("workspace_id")
    await _db.claims.create_index("token")
    await _db.claims.create_index("status")
    await _db.users.create_index("email", unique=True)
    await _db.sessions.create_index("token")
    await _db.sessions.create_index("expires_at", expireAfterSeconds=0)


async def disconnect_db():
    global _db_client
    if _db_client:
        _db_client.close()
