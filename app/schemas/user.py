from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime
from typing import Optional
import re

class UserRegister(BaseModel):
    email: str = Field(..., description="Địa chỉ email của người dùng")
    username: str = Field(..., min_length=3, max_length=50, description="Tên đăng nhập")
    password: str = Field(..., min_length=6, description="Mật khẩu của tài khoản")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        # Kiểm tra regex email cơ bản để không phụ thuộc vào email-validator nếu chưa cài
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_regex, v):
            raise ValueError("Email không hợp lệ")
        return v.lower()

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        # Tên đăng nhập không chứa khoảng trắng và ký tự đặc biệt
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Tên đăng nhập chỉ được chứa chữ cái, số, dấu gạch dưới và gạch ngang")
        return v.lower()


class UserLogin(BaseModel):
    identity: str = Field(..., description="Tên đăng nhập hoặc địa chỉ email")
    password: str = Field(..., description="Mật khẩu")


class UserResponse(BaseModel):
    id: str = Field(..., description="ID duy nhất của tài khoản")
    email: str = Field(..., description="Địa chỉ email")
    username: str = Field(..., description="Tên đăng nhập")
    created_at: datetime = Field(..., description="Thời gian tạo tài khoản")

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT Access Token (hiệu lực 5 phút)")
    refresh_token: str = Field(..., description="JWT Refresh Token (hiệu lực 1 ngày)")
    token_type: str = Field("bearer", description="Loại token")


class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="JWT Refresh Token")
