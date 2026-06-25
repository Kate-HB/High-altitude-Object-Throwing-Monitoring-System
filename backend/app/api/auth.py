"""Login endpoint — no auth required."""

from fastapi import APIRouter, Depends

from backend.app.core.auth import generate_token
from backend.app.models.schemas import LoginRequest, success_response

router = APIRouter(tags=["auth"])


@router.post("/auth/login")
def login(body: LoginRequest) -> dict:
    if body.username == "admin" and body.password == "admin123":
        token = generate_token()
        return success_response(
            {
                "token": token,
                "username": "admin",
                "role": "admin",
            },
            message="login success",
        )
    return {
        "code": 401,
        "message": "login failed",
        "detail": "账号或密码错误",
    }
