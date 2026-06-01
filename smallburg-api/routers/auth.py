from fastapi import APIRouter, HTTPException, Request, Response, Cookie
from datetime import datetime, timezone, timedelta
from typing import Optional
from bson import ObjectId
import bcrypt
import jwt as pyjwt

from models.user import UserCreate
from utils.tokens import hash_token, token_is_valid
from config import get_settings, get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])

SESSION_COOKIE = "sb_session"
SESSION_DAYS = 30


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _create_jwt(user_id: str, secret: str) -> str:
    return pyjwt.encode({
        "sub": user_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS),
    }, secret, algorithm="HS256")


def decode_jwt(token: str, secret: str) -> Optional[str]:
    try:
        return pyjwt.decode(token, secret, algorithms=["HS256"]).get("sub")
    except pyjwt.PyJWTError:
        return None


def doc_to_profile(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "email": doc["email"],
        "name": doc["name"],
        "role": doc["role"],
        "certifications": doc.get("certifications", []),
        "workspaces": doc.get("workspaces", []),
        "primary_workspace": doc.get("primary_workspace", ""),
        "created_at": doc["created_at"].isoformat(),
        "last_login": doc["last_login"].isoformat() if doc.get("last_login") else None,
        "status": doc.get("status", "active"),
    }


async def get_current_user(session_token: Optional[str]):
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    settings = get_settings()
    db = get_db()
    user_id = decode_jwt(session_token, settings.jwt_secret)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    session = await db.sessions.find_one({"token": session_token})
    if not session:
        raise HTTPException(status_code=401, detail="Session not found")
    expires_at = session["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/verify")
async def verify_token(token: str):
    db = get_db()
    raw = token.removeprefix("sb_")
    claim = await db.claims.find_one({"token": hash_token(raw)})
    valid, error = token_is_valid(claim)
    if not valid:
        raise HTTPException(status_code=400, detail=error)
    return {
        "valid": True,
        "email": claim["email"],
        "municipality": claim["municipality"],
        "workspace_id": claim["workspace_id"],
        "claim_id": str(claim["_id"]),
    }


@router.post("/register")
async def register(body: UserCreate, request: Request, response: Response):
    db = get_db()
    settings = get_settings()

    raw = body.token.removeprefix("sb_")
    claim = await db.claims.find_one({"token": hash_token(raw)})
    valid, error = token_is_valid(claim)
    if not valid:
        raise HTTPException(status_code=400, detail=error)

    if await db.users.find_one({"email": claim["email"]}):
        raise HTTPException(status_code=409, detail="Account already exists for this email")

    now = datetime.now(timezone.utc)
    result = await db.users.insert_one({
        "email": claim["email"],
        "name": body.name,
        "password_hash": _hash_password(body.password),
        "role": body.role.value,
        "certifications": body.certifications,
        "workspaces": body.workspaces,
        "primary_workspace": claim["workspace_id"],
        "created_at": now,
        "last_login": now,
        "status": "active",
    })
    user_id = str(result.inserted_id)

    await db.claims.update_one({"_id": claim["_id"]}, {"$set": {"token_used": True}})

    jwt_token = _create_jwt(user_id, settings.jwt_secret)
    await db.sessions.insert_one({
        "user_id": ObjectId(user_id),
        "token": jwt_token,
        "created_at": now,
        "expires_at": now + timedelta(days=SESSION_DAYS),
        "ip": request.client.host if request.client else "",
        "user_agent": request.headers.get("user-agent", ""),
    })

    response.set_cookie(SESSION_COOKIE, jwt_token, httponly=True, samesite="lax", secure=True, max_age=SESSION_DAYS * 86400)

    return {
        "ok": True,
        "user": {
            "name": body.name,
            "role": body.role.value,
            "workspaces": body.workspaces,
            "primary_workspace": claim["workspace_id"],
        }
    }


@router.post("/login")
async def login(request: Request, response: Response):
    db = get_db()
    settings = get_settings()
    data = await request.json()
    email = data.get("email", "").lower().strip()
    password = data.get("password", "")

    user = await db.users.find_one({"email": email})
    if not user or not _verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user.get("status") == "suspended":
        raise HTTPException(status_code=403, detail="Account suspended")

    now = datetime.now(timezone.utc)
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"last_login": now}})

    jwt_token = _create_jwt(str(user["_id"]), settings.jwt_secret)
    await db.sessions.insert_one({
        "user_id": user["_id"],
        "token": jwt_token,
        "created_at": now,
        "expires_at": now + timedelta(days=SESSION_DAYS),
        "ip": request.client.host if request.client else "",
        "user_agent": request.headers.get("user-agent", ""),
    })

    response.set_cookie(SESSION_COOKIE, jwt_token, httponly=True, samesite="lax", secure=True, max_age=SESSION_DAYS * 86400)
    return {"ok": True, "user": doc_to_profile(user)}


@router.post("/logout")
async def logout(response: Response, sb_session: Optional[str] = Cookie(default=None)):
    if sb_session:
        await get_db().sessions.delete_one({"token": sb_session})
    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True}


@router.get("/me")
async def me(sb_session: Optional[str] = Cookie(default=None)):
    user = await get_current_user(sb_session)
    return doc_to_profile(user)
