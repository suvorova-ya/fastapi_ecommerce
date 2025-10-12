# syntax=docker/dockerfile:1.4

FROM python:3.12-slim

ENV HOME=/home/fast \
    APP_HOME=/home/fast/app \
    PYTHONPATH="$PYTHONPATH:/home/fast" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_HOME="/opt/poetry" \
    PATH="$POETRY_HOME/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && update-ca-certificates \
    && mkdir -p $APP_HOME \
    && groupadd --system fast \
    && useradd --system --gid fast --home-dir $HOME fast

WORKDIR $HOME

# Устанавливаем Poetry
RUN pip install --upgrade pip && pip install poetry

# Копируем файлы зависимостей сначала (для кэширования)
COPY pyproject.toml poetry.lock* ./

# Настраиваем Poetry
RUN poetry config virtualenvs.create false

#  Устанавливаем зависимости с кэшированием
RUN --mount=type=cache,target=/root/.cache/pypoetry \
    --mount=type=cache,target=/root/.cache/pip \
    poetry install --no-root --no-interaction --no-ansi



# копируем приложение
COPY app app
COPY alembic.ini ./

RUN chown -R fast:fast $HOME

USER fast
