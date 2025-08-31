FROM python:3.11-slim

# Configurações de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instala Poetry
RUN pip install poetry==1.6.1

# Configura Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Cria diretório de trabalho
WORKDIR /app

# Copia arquivos de dependências
COPY pyproject.toml poetry.lock* ./

# Instala dependências
RUN poetry install --no-dev && rm -rf $POETRY_CACHE_DIR

# Copia código fonte
COPY . .

# Cria usuário não-root
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expõe porta
EXPOSE 8000

# Comando padrão
CMD ["poetry", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]