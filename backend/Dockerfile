FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_HOME=/opt/poetry \
    POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    PATH="/opt/poetry/bin:${PATH}"

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential curl libpq-dev git && \
    rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app

COPY pyproject.toml poetry.lock* /app/
RUN poetry install --with dev --no-ansi --no-interaction --no-root

COPY backend /app/backend
COPY contracts /app/contracts
COPY docs /app/docs
COPY observabilidade /app/observabilidade

# Cria usuário não-root e ajusta permissões do diretório de trabalho
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["poetry", "run", "python", "backend/manage.py", "runserver", "0.0.0.0:8000"]
