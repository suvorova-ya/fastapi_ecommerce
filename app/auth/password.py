from argon2 import PasswordHasher, exceptions
from datetime import datetime,timedelta,timezone
import jwt

from app.auth.config import SECRET_KEY,ALGORITHM



# Создаём экземпляр PasswordHasher с настройками по умолчанию
ph = PasswordHasher()



def  hash_password(password:str) -> str:
    """
    Преобразует пароль в хеш с использованием Argon2.
    Аргументы:
        password (str): Пароль в виде строки
    Возвращает:
        str: Хешированная строка, содержащая:
             - Алгоритм (argon2id)
             - Версия
             - Параметры (время, память, параллелизм)
             - Соль (128 бит)
             - Хеш (256 бит)
    Пример результата:
        '$argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHQ$RdescudvJCsgt3ub+b+dWRWJTmaaJObG'
    """
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
        Проверяет соответствие полученного пароля и хранимого хэша.
        Аргументы:
            plain_password (str): Введённый пользователем пароль
            hashed_password (str): Хеш из базы данных
        Возвращает:
            bool: True если пароль верный, False если неверный
        Исключения:
            VerifyMismatchError: Пароль не совпадает
            VerificationError: Общая ошибка верификации
            InvalidHash: Неправильный формат хеша
        """
    try:
        return ph.verify(hashed_password,plain_password)
    except (exceptions.VerifyMismatchError, exceptions.VerificationError, exceptions.InvalidHash):
        return False



def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
       Генерация JWT токена с указанным временем жизни.
       Аргументы:
           data: Данные для payload
           expires_delta: Время жизни токена (по умолчанию 30 минут)
           token_type: Тип токена (access, refresh)
       Возвращает:
           str: Закодированный JWT токен
       """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt