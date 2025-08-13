@echo off
echo ===== Preparando ambiente para trabalhar =====
echo.

echo 0. Verificando se o repositorio Git esta configurado...
if not exist ".git" (
    echo Inicializando repositorio Git...
    git init
)
git remote -v | findstr "origin" > nul
if %errorlevel% neq 0 (
    echo Configurando o repositorio remoto...
    git remote add origin https://github.com/Tomvaz11/iabank.git
)

echo 1. Mudando para o branch main...
git checkout main 2>nul
if %errorlevel% neq 0 (
    echo Branch main nao existe localmente. Criando branch main...
    git checkout -b main
)

echo 2. Obtendo a versao mais recente do codigo...
git pull origin main --allow-unrelated-histories 2>nul
if %errorlevel% neq 0 (
    echo NOTA: Nao foi possivel obter a versao mais recente.
    echo Isso e normal se este for o primeiro uso ou se o repositorio remoto estiver vazio.
)
echo.

echo ===== PRONTO PARA TRABALHAR! =====
echo Voce esta trabalhando no branch main do projeto IABANK.
echo Faca suas alteracoes e depois execute o script "atualizar-github.bat"
echo.
pause
