"""ARCHITECTURE.md §5 — Auth (phone OTP + JWT, DB-backed).

Demo mode: OTP is fixed '123456' (returned in response). Production swaps in
an SMS gateway; the API contract is unchanged. Tokens are signed JWTs carrying
the user id.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import User, get_db

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

router = APIRouter()

_JWT_SECRET = os.getenv("JWT_SECRET", "gramai-dev-secret-change-me")
_JWT_ALG = "HS256"
_TOKEN_TTL_HOURS = 24 * 7

_OTPS: dict[str, tuple[str, float]] = {}
_OTP_ATTEMPTS: dict[str, list[float]] = {}
_OTP_SENDS: dict[str, list[float]] = {}

_DEMO_OTP = "123456"

_MAX_OTP_SENDS_PER_HOUR = 5
_MAX_VERIFY_ATTEMPTS = 5

_IS_PROD = os.getenv("ENVIRONMENT") == "production"

if _IS_PROD and not os.getenv("JWT_SECRET"):
    raise RuntimeError("JWT_SECRET must be set when ENVIRONMENT=production")


class SendOtp(BaseModel):
    mobile: str = Field(pattern=r"^\d{10}$")


class VerifyOtp(BaseModel):
    mobile: str
    otp: str
    full_name: str = ""


class Register(BaseModel):
    full_name: str
    mobile: str
    lang: str = "en"


class Login(BaseModel):
    handle: str
    password: str = ""


def _create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(hours=_TOKEN_TTL_HOURS),
    }

    return jwt.encode(
        payload,
        _JWT_SECRET,
        algorithm=_JWT_ALG,
    )


def _tokens(user_id: int) -> dict:
    return {
        "access_token": _create_token(user_id),
        "token_type": "bearer",
    }


def get_current_user(
    authorization: str = Header(default=""),
    token: str = Query(default=""),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency — extracts JWT and loads the user.

    Normal API requests use the Authorization header.

    SSE requests may provide the token as a query parameter because the
    browser's native EventSource API cannot set a custom Authorization header.
    """

    # Normal API authentication.
    if authorization.startswith("Bearer "):
        token_value = authorization.removeprefix("Bearer ").strip()

    # SSE/EventSource fallback authentication.
    elif token:
        token_value = token.strip()

    else:
        raise HTTPException(401, "Missing bearer token")

    try:
        payload = jwt.decode(
            token_value,
            _JWT_SECRET,
            algorithms=[_JWT_ALG],
        )
    except JWTError:
        raise HTTPException(401, "Invalid or expired token")

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(401, "Invalid token")

    user = db.get(User, user_id)

    if not user:
        raise HTTPException(401, "User not found")

    return user


@router.post("/otp/send")
def otp_send(req: SendOtp) -> dict:
    now = time.time()

    sends = [
        t
        for t in _OTP_SENDS.get(req.mobile, [])
        if now - t < 3600
    ]

    if len(sends) >= _MAX_OTP_SENDS_PER_HOUR:
        raise HTTPException(
            429,
            "Too many OTP requests. Try again later.",
        )

    sends.append(now)

    _OTP_SENDS[req.mobile] = sends

    _OTPS[req.mobile] = (
        _DEMO_OTP,
        now + 300,
    )

    resp: dict = {
        "ok": True,
        "resend_in": 45,
    }

    if not _IS_PROD:
        resp["demo_otp"] = _DEMO_OTP

    return resp


@router.post("/otp/verify")
def otp_verify(
    req: VerifyOtp,
    db: Session = Depends(get_db),
) -> dict:
    now = time.time()

    attempts = [
        t
        for t in _OTP_ATTEMPTS.get(req.mobile, [])
        if now - t < 900
    ]

    if len(attempts) >= _MAX_VERIFY_ATTEMPTS:
        raise HTTPException(
            429,
            "Too many attempts. Try again in 15 minutes.",
        )

    entry = _OTPS.get(req.mobile)

    if (
        not entry
        or entry[0] != req.otp
        or now > entry[1]
    ):
        attempts.append(now)
        _OTP_ATTEMPTS[req.mobile] = attempts

        raise HTTPException(
            401,
            "Invalid or expired OTP",
        )

    _OTP_ATTEMPTS.pop(req.mobile, None)
    _OTPS.pop(req.mobile, None)

    user = (
        db.query(User)
        .filter(User.mobile == req.mobile)
        .first()
    )

    is_new = user is None

    if is_new:
        user = User(
            mobile=req.mobile,
            full_name=req.full_name or "New User",
        )

        db.add(user)

    elif req.full_name and user.full_name in ("", "New User"):
        user.full_name = req.full_name

    db.commit()
    db.refresh(user)

    return _tokens(user.id) | {
        "is_new_user": is_new,
        "user": {
            "id": user.id,
            "mobile": user.mobile,
            "full_name": user.full_name,
        },
    }


@router.post("/register")
def register(
    req: Register,
    db: Session = Depends(get_db),
) -> dict:
    user = (
        db.query(User)
        .filter(User.mobile == req.mobile)
        .first()
    )

    if user:
        user.full_name = req.full_name or user.full_name

    else:
        user = User(
            mobile=req.mobile,
            full_name=req.full_name,
        )

        db.add(user)

    db.commit()
    db.refresh(user)

    return {
        "ok": True,
        "mobile": req.mobile,
        "user_id": user.id,
    }


@router.post("/login")
def login(
    req: Login,
    db: Session = Depends(get_db),
) -> dict:
    mobile = req.handle if req.handle.isdigit() else None

    if mobile:
        user = (
            db.query(User)
            .filter(User.mobile == mobile)
            .first()
        )

        if user:
            return _tokens(user.id)

    raise HTTPException(
        401,
        "Invalid credentials",
    )


@router.post("/google")
def google_auth(
    body: dict,
    db: Session = Depends(get_db),
) -> dict:
    # Demo stub — production verifies id_token with Google certs.
    mobile = body.get(
        "mobile",
        "0000000000",
    )

    user = (
        db.query(User)
        .filter(User.mobile == mobile)
        .first()
    )

    if not user:
        user = User(
            mobile=mobile,
            full_name=body.get(
                "full_name",
                "",
            ),
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    return _tokens(user.id) | {
        "is_new_user": False,
    }
