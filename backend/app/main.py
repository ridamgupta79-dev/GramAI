"""GramAI FastAPI app — ARCHITECTURE.md §2/§5.

Legacy v1 routers (feasibility/dashboard) kept for compatibility; the
architecture-spec API surface lives under /api per §5.
"""
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from app.api import admin, analyses, auth, business, chat, finance, geo, reports, schemes, users  # noqa: E402
from app.db import DB_KIND, init_db  # noqa: E402
from app.routers import dashboard, feasibility, finance as legacy_finance, location, chat as legacy_chat  # noqa: E402

init_db()
print(f"[GramAI] Database: {DB_KIND}")

app = FastAPI(
    title="GramAI — AI Rural Business Intelligence Platform",
    description="Hyper-local business intelligence, financial planning and "
                "government scheme routing for rural entrepreneurs.",
    version="1.0.0",
)

_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Architecture-spec API surface (§5) ----
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(analyses.router, prefix="/api/analyses", tags=["analyses"])
app.include_router(finance.router, prefix="/api/finance", tags=["finance"])
app.include_router(geo.router, prefix="/api/geo", tags=["geo"])
app.include_router(schemes.router, prefix="/api/schemes", tags=["schemes"])
app.include_router(business.router, prefix="/api/business", tags=["business"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(admin.i18n_router, prefix="/api", tags=["i18n"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])


# ---- Legacy v1 surface (kept working) ----
app.include_router(legacy_finance.router, prefix="/api/v1/finance", tags=["v1-finance"])
app.include_router(location.router, prefix="/api/v1/location", tags=["v1-location"])
app.include_router(feasibility.router, prefix="/api/v1/feasibility", tags=["v1-feasibility"])
app.include_router(legacy_chat.router, prefix="/api/v1/chat", tags=["v1-chat"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["v1-dashboard"])


@app.get("/health")
def health():
    return {"status": "ok"}
