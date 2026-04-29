#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo
echo "===================================================="
echo "  Calculadora Imobiliaria - inicializacao (Unix)"
echo "===================================================="
echo

if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1; then
    PY=python
else
    echo "[ERRO] Python nao encontrado. Instale Python 3.11+."
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "[1/4] Criando ambiente virtual em .venv ..."
    "$PY" -m venv .venv
else
    echo "[1/4] Ambiente virtual ja existe."
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "[2/4] Verificando dependencias..."
if ! python -c "import flask, pydantic, httpx, tenacity" >/dev/null 2>&1; then
    echo "      Instalando requirements.txt ..."
    python -m pip install --quiet --upgrade pip
    python -m pip install --quiet -r requirements.txt
else
    echo "      Dependencias OK."
fi

if [ ! -f ".env" ]; then
    echo "[3/4] Criando .env a partir de .env.example ..."
    cp .env.example .env
else
    echo "[3/4] .env ja existe."
fi

echo "[4/4] Iniciando servidor Flask em http://127.0.0.1:5000"
echo
echo "Pressione Ctrl+C para encerrar."
echo

# Abre o navegador (best-effort, não trava se não conseguir).
URL="http://127.0.0.1:5000/"
( sleep 1 && {
    if command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" >/dev/null 2>&1
    elif command -v open       >/dev/null 2>&1; then open "$URL" >/dev/null 2>&1
    elif command -v wslview    >/dev/null 2>&1; then wslview "$URL" >/dev/null 2>&1
    fi
} ) &

exec python run.py
