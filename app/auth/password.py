from argon2 import PasswordHasher, exceptions

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

