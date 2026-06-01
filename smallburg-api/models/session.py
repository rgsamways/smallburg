from pydantic import BaseModel
from datetime import datetime


class SessionCreate(BaseModel):
    user_id: str
    token: str
    ip: str
    user_agent: str
    created_at: datetime
    expires_at: datetime
