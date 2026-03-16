#!/bin/bash
# Inicia o servidor em segundo plano
python server.py &
# Aguarda um momento para o servidor iniciar (opcional)
sleep 2
# Abre o navegador no endereço do servidor
xdg-open http://localhost:5000
