@echo off
REM IABANK - Script simplificado para configurar testes (Windows)
REM Vers├úo que funciona no Windows sem problemas de encoding

echo IABANK - Configurando ambiente de testes...

REM Verificar Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Docker nao encontrado
    exit /b 1
)

REM Navegar para raiz do projeto
cd /d "%~dp0\..\.."

echo [INFO] Parando containers existentes...
docker-compose down --remove-orphans >nul 2>&1

echo [INFO] Iniciando PostgreSQL e Redis...
docker-compose up -d postgres redis

echo [INFO] Aguardando 15 segundos para inicializacao...
timeout /t 15 /nobreak >nul

echo [INFO] Verificando PostgreSQL...
docker-compose exec postgres pg_isready -U iabank_user -d iabank

echo [INFO] Verificando Redis...
docker-compose exec redis redis-cli ping

echo [INFO] Aplicando migracoes...
cd backend
python src/manage.py migrate --verbosity=1

echo.
echo Ambiente configurado com sucesso!
echo PostgreSQL: localhost:5433
echo Redis: localhost:6379
echo.
echo Para executar testes:
echo   cd backend ^&^& python -m pytest tests/ --tb=short
echo.
pause