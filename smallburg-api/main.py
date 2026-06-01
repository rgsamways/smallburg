import resend
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import connect_db, disconnect_db, get_settings
from routers import claims, auth, users, workspaces


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    resend.api_key = settings.resend_api_key
    await connect_db()
    yield
    await disconnect_db()


app = FastAPI(title="smallburg-api", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(claims.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(workspaces.router)


@app.get("/health")
async def health():
    return {"ok": True, "service": "smallburg-api"}
