#!/bin/bash

echo "🚀 Iniciando EcoAlerta..."
echo ""

mkdir -p logs

# Verificar Ollama
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama ya está corriendo"
else
    echo "🤖 Iniciando Ollama..."
    ollama serve > logs/ollama.log 2>&1 &
    sleep 3
    echo "✅ Ollama iniciado"
fi

# Verificar PostgreSQL
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "✅ PostgreSQL ya está corriendo"
else
    echo "🗄️  Iniciando PostgreSQL..."
    /opt/homebrew/opt/postgresql@17/bin/pg_ctl -D /opt/homebrew/var/postgresql@17 start -l logs/postgres.log 2>/dev/null
    sleep 3
    echo "✅ PostgreSQL iniciado"
fi

# Backend con Daphne con timeout extendido (necesario para IA local)
echo "📦 Iniciando Backend..."
cd backend
source venv/bin/activate
daphne -b 0.0.0.0 -p 8000 -t 300 --application-close-timeout 300 \
    ecoalerta.asgi:application \
    > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..
echo "✅ Backend iniciado (PID: $BACKEND_PID) en http://localhost:8000"

sleep 3

# Frontend
echo "⚛️  Iniciando Frontend..."
cd frontend
npx vite --host 0.0.0.0 --port 5173 > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "✅ Frontend iniciado (PID: $FRONTEND_PID) en http://localhost:5173"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌱 EcoAlerta está corriendo!"
echo ""
echo "   📡 Backend:  http://localhost:8000"
echo "   🎨 Frontend: http://localhost:5173"
echo "   🤖 Chat IA:  Dashboard → 🤖 Chat IA (admin)"
echo ""
echo "   🔑 Credenciales:"
echo "      administrador / Admin1234!"
echo "      inspector     / Admin1234!"
echo ""
echo "   📝 Logs: logs/backend.log | logs/frontend.log"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "$BACKEND_PID $FRONTEND_PID" > logs/pids.txt

cleanup() {
    echo ""
    echo "🛑 Deteniendo servidores..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    rm -f logs/pids.txt
    echo "✅ Servidores detenidos"
    exit 0
}

trap cleanup INT TERM
echo "Presiona Ctrl+C para detener..."
wait
