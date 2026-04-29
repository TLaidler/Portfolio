@echo off
setlocal EnableDelayedExpansion
chcp 65001 > nul
cd /d "%~dp0"

echo.
echo ====================================================
echo   Calculadora Imobiliaria - inicializacao (Windows)
echo ====================================================
echo.

where python > nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado no PATH.
    echo Instale Python 3.11+ em https://www.python.org/downloads/
    pause
    exit /b 1
)

if not exist ".venv\" (
    echo [1/4] Criando ambiente virtual em .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERRO] Falha ao criar venv.
        pause
        exit /b 1
    )
) else (
    echo [1/4] Ambiente virtual ja existe.
)

call .venv\Scripts\activate.bat

echo [2/4] Verificando dependencias...
python -c "import flask, pydantic, httpx, tenacity" > nul 2>&1
if errorlevel 1 (
    echo       Instalando requirements.txt ...
    python -m pip install --quiet --upgrade pip
    python -m pip install --quiet -r requirements.txt
    if errorlevel 1 (
        echo [ERRO] Falha ao instalar dependencias.
        pause
        exit /b 1
    )
) else (
    echo       Dependencias OK.
)

if not exist ".env" (
    echo [3/4] Criando .env a partir de .env.example ...
    copy /Y .env.example .env > nul
) else (
    echo [3/4] .env ja existe.
)

echo [4/4] Iniciando servidor Flask em http://127.0.0.1:5000
echo.
echo Pressione Ctrl+C para encerrar.
echo.

start "" http://127.0.0.1:5000/

python run.py

endlocal
