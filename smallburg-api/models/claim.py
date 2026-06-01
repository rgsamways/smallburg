from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum


class ClaimStatus(str, Enum):
    pending = "pending"
    granted = "granted"
    expired = "expired"
    declined = "declined"


class ClaimSubmit(BaseModel):
    email: EmailStr
    postal: str
    municipality: str
    workspace_id: str
    slug: str
