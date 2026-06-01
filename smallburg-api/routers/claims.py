from fastapi import APIRouter, HTTPException, Header, Depends
from datetime import datetime, timezone, timedelta
from bson import ObjectId

from models.claim import ClaimSubmit
from utils.tokens import generate_magic_token, hash_token, make_magic_link
from utils.email import send_claim_notification, send_magic_link
from config import get_settings, get_db

router = APIRouter(prefix="/api/claims", tags=["claims"])


def require_operator_key(x_operator_key: str = Header(...)):
    settings = get_settings()
    if x_operator_key != settings.operator_api_key:
        raise HTTPException(status_code=401, detail="Invalid operator key")
    return x_operator_key


@router.post("")
async def submit_claim(body: ClaimSubmit):
    """Receives claim form submission. Replaces Cloudflare Worker once live."""
    db = get_db()
    settings = get_settings()

    # Idempotent — don't create duplicate pending claims
    existing = await db.claims.find_one({
        "email": body.email,
        "workspace_id": body.workspace_id,
        "status": "pending",
    })
    if existing:
        return {"ok": True}

    now = datetime.now(timezone.utc)
    result = await db.claims.insert_one({
        "email": body.email,
        "postal": body.postal,
        "municipality": body.municipality,
        "workspace_id": body.workspace_id,
        "slug": body.slug,
        "status": "pending",
        "requested_at": now,
        "granted_at": None,
        "token": None,
        "token_expires_at": None,
        "token_used": False,
    })

    send_claim_notification(
        operator_email=settings.operator_notification_email,
        claim_email=body.email,
        postal=body.postal,
        municipality=body.municipality,
        workspace_id=body.workspace_id,
        slug=body.slug,
        claim_id=str(result.inserted_id),
        requested_at=now.strftime("%Y-%m-%d %H:%M UTC"),
    )

    return {"ok": True}


@router.post("/{claim_id}/grant")
async def grant_claim(claim_id: str, _key: str = Depends(require_operator_key)):
    """Operator grants access — generates and emails magic link."""
    db = get_db()
    settings = get_settings()

    try:
        oid = ObjectId(claim_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid claim ID")

    claim = await db.claims.find_one({"_id": oid})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim["status"] not in ("pending", "expired"):
        raise HTTPException(status_code=409, detail=f"Claim is already '{claim['status']}'")

    raw_token = generate_magic_token()
    hashed = hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.magic_link_expiry_hours)

    await db.claims.update_one({"_id": oid}, {"$set": {
        "status": "granted",
        "granted_at": datetime.now(timezone.utc),
        "token": hashed,
        "token_expires_at": expires_at,
        "token_used": False,
    }})

    magic_link = make_magic_link(settings.magic_link_base_url, raw_token)
    send_magic_link(
        claimant_email=claim["email"],
        municipality=claim["municipality"],
        magic_link_url=magic_link,
        expiry_hours=settings.magic_link_expiry_hours,
    )

    return {"ok": True, "claim_id": claim_id}


@router.post("/{claim_id}/decline")
async def decline_claim(claim_id: str, _key: str = Depends(require_operator_key)):
    """Operator declines. No email sent."""
    db = get_db()

    try:
        oid = ObjectId(claim_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid claim ID")

    result = await db.claims.update_one(
        {"_id": oid, "status": "pending"},
        {"$set": {"status": "declined"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Claim not found or not pending")

    return {"ok": True}
