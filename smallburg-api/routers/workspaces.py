from fastapi import APIRouter, HTTPException, Cookie
from typing import Optional

from config import get_db
from routers.auth import get_current_user

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


@router.get("/{workspace_id}")
async def get_workspace(workspace_id: str, sb_session: Optional[str] = Cookie(default=None)):
    user = await get_current_user(sb_session)
    if workspace_id not in user.get("workspaces", []):
        raise HTTPException(status_code=403, detail="Not a member of this workspace")

    db = get_db()
    workspace = await db.workspaces.find_one({"workspace_id": workspace_id})
    if not workspace:
        return {"workspace_id": workspace_id, "name": workspace_id, "asset_count": 0, "commons_task_count": 0}

    return {
        "workspace_id": workspace_id,
        "name": workspace.get("name", workspace_id),
        "slug": workspace.get("slug", ""),
        "asset_count": workspace.get("asset_count", 0),
        "commons_task_count": workspace.get("commons_task_count", 0),
    }
