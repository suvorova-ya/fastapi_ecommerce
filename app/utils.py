import os
from dotenv import load_dotenv

load_dotenv()

# JWT
SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

ENV = os.getenv("ENV", "development")

# Cookie настройки
COOKIE_NAME = "refresh_token"
COOKIE_PATH = "/"
COOKIE_HTTPONLY = True
COOKIE_SAMESITE = "strict"
COOKIE_MAX_AGE = 60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS  # в секундах

# Secure — только в продакшене
COOKIE_SECURE = ENV == "production"