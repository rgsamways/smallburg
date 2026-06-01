from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class UserRole(str, Enum):
    inspector = "inspector"
    municipal_staff = "municipal_staff"
    community_member = "community_member"


class UserCreate(BaseModel):
    token: str
    name: str
    role: UserRole
    certifications: List[str] = []
    workspaces: List[str]
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    name: Optional[str] = None
    certifications: Optional[List[str]] = None
    workspaces: Optional[List[str]] = None
