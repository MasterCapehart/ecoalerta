#!/bin/bash

echo "🚀 Iniciando EcoAlerta..."
echo ""

# Crear directorio de logs si no existe
mkdir -p logs

# Iniciar backend en background
echo "📦 Iniciando Backend Django..."
cd backend
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..
echo "✅ Backend iniciado (PID: $BACKEND_PID) en http://localhost:8000 (y 0.0.0.0:8000)"

# Esperar un poco para que el backend inicie
sleep 2

# Iniciar frontend en background
echo "⚛️  Iniciando Frontend React..."
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "✅ Frontend iniciado (PID: $FRONTEND_PID) en http://localhost:5173"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌱 EcoAlerta está corriendo!"
echo ""
echo "   📡 Backend:  http://localhost:8000 (0.0.0.0:8000)"
echo "   🎨 Frontend: http://localhost:5173"
echo "   📋 Admin:    http://localhost:8000/admin"
echo ""
echo "   📝 Logs:"
echo "      Backend:  logs/backend.log"
echo "      Frontend: logs/frontend.log"
echo ""
echo "   🔑 Credenciales:"
echo "      Usuario: inspector"
echo "      Password: 1234"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Para detener los servidores:"
echo "   ./stop.sh"
echo "   o presiona Ctrl+C"
echo ""

# Guardar PIDs en archivo para poder detenerlos
echo "$BACKEND_PID $FRONTEND_PID" > logs/pids.txt

# Función para limpiar al salir
cleanup() {
    echo ""
    echo "🛑 Deteniendo servidores..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    rm -f logs/pids.txt
    echo "✅ Servidores detenidos"
    exit 0
}

# Capturar Ctrl+C
trap cleanup INT TERM

# Esperar a que el usuario presione Ctrl+C
echo "Presiona Ctrl+C para detener los servidores..."
wait

