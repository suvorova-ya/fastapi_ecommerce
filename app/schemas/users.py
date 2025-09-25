from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreate(BaseModel):
    email: EmailStr = Field(description="Email пользователя")
    password: str = Field(min_length=8, description="Пароль (минимум 8 символов)")
    role: str = Field(default="buyer", pattern="^(buyer|seller|admin)$", description="Роль:'buyer'|'seller'|'admin")


class User(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    role: str

    model_config = ConfigDict(from_attributes=True)
