from loguru import logger
from uuid import uuid4
from fastapi import Request
from fastapi.responses import JSONResponse


logger.add("info.log", format="Log: [{extra[log_id]}:{time} - {level} - {message}]", level="INFO", enqueue = True,
           rotation="10 MB", retention="10 days")



async def log_middleware(request:Request, call_next):
    """
      Middleware для логирования HTTP-запросов и обработки ошибок.
       Аргументы:
           request: Объект HTTP-запроса для обработки
           call_next: Функция для передачи запроса следующему обработчику в цепочке
       Возвращает:
           Response: HTTP-ответ, сгенерированный обработчиком запроса
       Исключения:
           500 Internal Server Error: Если в процессе обработки запроса возникает непредвиденная ошибка
       Логирование:
           - INFO: Успешные запросы (статус 200-399, кроме 401-404)
           - WARNING: Запросы с кодами 401, 402, 403, 404
           - ERROR: Необработанные исключения с деталями ошибки
       """
    log_id = str(uuid4())
    with logger.contextualize(log_id=log_id):
        try:
            response = await call_next(request)
            if response.status_code in [401,402,403,404]:
                logger.warning(f"Request to {request.url.path} failed")
            else:
                logger.info('Successfully accessed ' + request.url.path)

        except Exception as e:
            logger.error(f"Request to {request.url.path} failed : {e}")
            response = JSONResponse(content={"success": False}, status_code=500)
        return response


