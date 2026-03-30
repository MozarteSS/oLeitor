#!/bin/bash

# Verifica se existe um virtual environment (.venv)
if [ -x ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
elif [ -x "venv/bin/python" ]; then
    PYTHON="venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON="python3"
elif command -v python &>/dev/null; then
    PYTHON="python"
else
    echo "[ERRO] Python não encontrado. Instale o Python 3.8+ e tente novamente."
    exit 1
fi

# Inicia o servidor em segundo plano usando o Python correto
"$PYTHON" server.py &
SERVER_PID=$!

# Aguarda o servidor iniciar
sleep 2

# Verifica se o servidor subiu
if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "[ERRO] O servidor falhou ao iniciar. Verifique se as dependências estão instaladas:"
    echo "  pip install -r requirements.txt"
    exit 1
fi

echo "Servidor iniciado (PID $SERVER_PID). Abrindo navegador..."

# Abre o navegador (compatível com Linux e macOS)
if command -v xdg-open &>/dev/null; then
    xdg-open http://localhost:5000
elif command -v open &>/dev/null; then
    open http://localhost:5000
else
    echo "Abra manualmente: http://localhost:5000"
fi
