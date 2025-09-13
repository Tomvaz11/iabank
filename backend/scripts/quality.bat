@echo off
REM IABANK Backend - Script de qualidade para Windows
REM Automatização de ferramentas de linting, formatação e testes

setlocal EnableDelayedExpansion

REM Cores para output (Windows 10+)
set "RED=[31m"
set "GREEN=[32m"
set "YELLOW=[33m"
set "BLUE=[34m"
set "RESET=[0m"

REM Diretório do projeto
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

echo %BLUE%🎯 IABANK Backend - Ferramentas de Qualidade de Código%RESET%
echo.

if "%1"=="" (
    echo %YELLOW%Uso: quality.bat [comando]%RESET%
    echo.
    echo Comandos disponíveis:
    echo   install     - Instalar dependências
    echo   lint        - Executar ruff linting
    echo   format      - Executar black formatação
    echo   typecheck   - Executar mypy verificação de tipos
    echo   quality     - Executar todas as verificações de qualidade
    echo   test        - Executar testes
    echo   test-cov    - Executar testes com cobertura
    echo   full        - Verificação completa
    echo   clean       - Limpar arquivos temporários
    echo   help        - Mostrar esta ajuda
    echo.
    echo Exemplos:
    echo   quality.bat quality
    echo   quality.bat test-cov
    echo   quality.bat full
    goto :eof
)

REM Mudar para o diretório do projeto
cd /d "%PROJECT_ROOT%"

if "%1"=="install" (
    echo %BLUE%📦 Instalando dependências...%RESET%
    pip install -r requirements.txt
    if %errorlevel% equ 0 (
        echo %GREEN%✅ Dependências instaladas com sucesso%RESET%
    ) else (
        echo %RED%❌ Erro ao instalar dependências%RESET%
        exit /b 1
    )
    goto :eof
)

if "%1"=="lint" (
    echo %BLUE%🔍 Executando ruff linting...%RESET%
    ruff check src tests --fix
    if %errorlevel% equ 0 (
        echo %GREEN%✅ Linting concluído%RESET%
    ) else (
        echo %RED%❌ Problemas encontrados no linting%RESET%
        exit /b 1
    )
    goto :eof
)

if "%1"=="format" (
    echo %BLUE%🎨 Executando formatação com black...%RESET%
    black src tests
    if %errorlevel% equ 0 (
        echo %GREEN%✅ Formatação concluída%RESET%
    ) else (
        echo %RED%❌ Problemas na formatação%RESET%
        exit /b 1
    )
    goto :eof
)

if "%1"=="typecheck" (
    echo %BLUE%📝 Executando verificação de tipos com mypy...%RESET%
    mypy src
    if %errorlevel% equ 0 (
        echo %GREEN%✅ Verificação de tipos concluída%RESET%
    ) else (
        echo %RED%❌ Problemas de tipagem encontrados%RESET%
        exit /b 1
    )
    goto :eof
)

if "%1"=="quality" (
    echo %BLUE%🎯 Executando verificações de qualidade...%RESET%

    echo %BLUE%🔍 1/3 - Ruff linting...%RESET%
    ruff check src tests --fix
    set "lint_result=%errorlevel%"

    echo %BLUE%🎨 2/3 - Black formatação...%RESET%
    black src tests
    set "format_result=%errorlevel%"

    echo %BLUE%📝 3/3 - MyPy verificação de tipos...%RESET%
    mypy src
    set "type_result=%errorlevel%"

    if !lint_result! equ 0 if !format_result! equ 0 if !type_result! equ 0 (
        echo %GREEN%🎉 Todas as verificações de qualidade passaram!%RESET%
    ) else (
        echo %RED%❌ Algumas verificações falharam%RESET%
        exit /b 1
    )
    goto :eof
)

if "%1"=="test" (
    echo %BLUE%🧪 Executando testes...%RESET%
    pytest
    if %errorlevel% equ 0 (
        echo %GREEN%✅ Testes concluídos%RESET%
    ) else (
        echo %RED%❌ Testes falharam%RESET%
        exit /b 1
    )
    goto :eof
)

if "%1"=="test-cov" (
    echo %BLUE%🧪 Executando testes com cobertura...%RESET%
    pytest --cov=src --cov-report=term-missing --cov-report=html
    if %errorlevel% equ 0 (
        echo %GREEN%✅ Testes com cobertura concluídos%RESET%
        echo %YELLOW%📊 Relatório HTML: coverage_html\index.html%RESET%
    ) else (
        echo %RED%❌ Testes falharam%RESET%
        exit /b 1
    )
    goto :eof
)

if "%1"=="full" (
    echo %BLUE%🚀 Executando verificação completa...%RESET%

    REM Qualidade
    call :run_quality
    set "quality_result=%errorlevel%"

    REM Testes
    echo %BLUE%🧪 Executando testes...%RESET%
    pytest --cov=src --cov-report=term-missing --cov-report=html
    set "test_result=%errorlevel%"

    if !quality_result! equ 0 if !test_result! equ 0 (
        echo %GREEN%🎉 VERIFICAÇÃO COMPLETA PASSOU!%RESET%
        echo %YELLOW%📋 Resumo:%RESET%
        echo   ✅ Linting (ruff)
        echo   ✅ Formatação (black)
        echo   ✅ Verificação de tipos (mypy)
        echo   ✅ Testes (pytest)
    ) else (
        echo %RED%❌ Verificação completa falhou%RESET%
        exit /b 1
    )
    goto :eof
)

if "%1"=="clean" (
    echo %BLUE%🧹 Limpando arquivos temporários...%RESET%

    REM Remover __pycache__
    for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

    REM Remover .pyc files
    del /s /q *.pyc 2>nul

    REM Remover diretórios de cache
    if exist .pytest_cache rd /s /q .pytest_cache
    if exist .mypy_cache rd /s /q .mypy_cache
    if exist .ruff_cache rd /s /q .ruff_cache
    if exist coverage_html rd /s /q coverage_html
    if exist .coverage del .coverage
    if exist htmlcov rd /s /q htmlcov

    echo %GREEN%✅ Limpeza concluída%RESET%
    goto :eof
)

if "%1"=="help" (
    call :show_help
    goto :eof
)

echo %RED%❌ Comando desconhecido: %1%RESET%
echo Use 'quality.bat help' para ver os comandos disponíveis
exit /b 1

:run_quality
echo %BLUE%🎯 Executando verificações de qualidade...%RESET%

echo %BLUE%🔍 1/3 - Ruff linting...%RESET%
ruff check src tests --fix
if %errorlevel% neq 0 exit /b 1

echo %BLUE%🎨 2/3 - Black formatação...%RESET%
black src tests
if %errorlevel% neq 0 exit /b 1

echo %BLUE%📝 3/3 - MyPy verificação de tipos...%RESET%
mypy src
if %errorlevel% neq 0 exit /b 1

echo %GREEN%🎉 Verificações de qualidade concluídas!%RESET%
exit /b 0

:show_help
echo %YELLOW%Uso: quality.bat [comando]%RESET%
echo.
echo Comandos disponíveis:
echo   install     - Instalar dependências
echo   lint        - Executar ruff linting
echo   format      - Executar black formatação
echo   typecheck   - Executar mypy verificação de tipos
echo   quality     - Executar todas as verificações de qualidade
echo   test        - Executar testes
echo   test-cov    - Executar testes com cobertura
echo   full        - Verificação completa (qualidade + testes)
echo   clean       - Limpar arquivos temporários
echo   help        - Mostrar esta ajuda
goto :eof