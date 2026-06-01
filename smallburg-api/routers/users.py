from fastapi import APIRouter, Cookie
from typing import Optional

from models.user import UserUpdate
from config import get_db
from routers.auth import get_current_user, doc_to_profile

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me")
async def get_profile(sb_session: Optional[str] = Cookie(default=None)):
    user = await get_current_user(sb_session)
    return doc_to_profile(user)


@router.patch("/me")
async def update_profile(body: UserUpdate, sb_session: Optional[str] = Cookie(default=None)):
    user = await get_current_user(sb_session)
    db = get_db()
    updates = body.model_dump(exclude_none=True)
    if updates:
        await db.users.update_one({"_id": user["_id"]}, {"$set": updates})
        user = await db.users.find_one({"_id": user["_id"]})
    return doc_to_profile(user)
