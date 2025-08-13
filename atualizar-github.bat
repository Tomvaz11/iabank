@echo off
echo ===== Atualizando seu codigo no GitHub =====
echo.

echo 1. Obtendo alteracoes mais recentes...
git pull origin main
if %errorlevel% neq 0 (
    echo AVISO: Nao foi possivel obter as alteracoes mais recentes.
    echo Isso pode acontecer se o repositorio remoto estiver vazio ou se houver conflitos.
    echo Continuando com o processo...
)
echo.

echo 2. Adicionando suas alteracoes...
git add .
if %errorlevel% neq 0 (
    echo ERRO: Nao foi possivel adicionar suas alteracoes.
    pause
    exit /b %errorlevel%
)
echo.

echo 3. Descricao das alteracoes:
set /p commit_msg="Digite uma breve descricao do que voce fez: "
echo.

echo 4. Salvando suas alteracoes...
git commit -m "%commit_msg%"
if %errorlevel% neq 0 (
    echo ERRO: Nao foi possivel salvar suas alteracoes.
    pause
    exit /b %errorlevel%
)
echo.

echo 5. Enviando para o GitHub...
git push -u origin main
if %errorlevel% neq 0 (
    echo ERRO: Nao foi possivel enviar para o GitHub.
    echo Verifique suas credenciais e permissoes de acesso ao repositorio.
    pause
    exit /b %errorlevel%
)
echo.

echo ===== SUCESSO! =====
echo Suas alteracoes foram enviadas para o GitHub no branch main.
echo Voce pode verificar o status em: https://github.com/Tomvaz11/iabank
echo.
pause
