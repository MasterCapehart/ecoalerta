#!/bin/bash

echo "🛑 Deteniendo EcoAlerta..."

# Detener usando PIDs guardados si existen
if [ -f logs/pids.txt ]; then
    PIDS=$(cat logs/pids.txt)
    for PID in $PIDS; do
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID 2>/dev/null
        fi
    done
    rm -f logs/pids.txt
fi

# Detener por nombre de proceso (por si acaso)
pkill -f "manage.py runserver" 2>/dev/null
pkill -f "vite" 2>/dev/null

sleep 1

# Verificar que se detuvieron
if pgrep -f "manage.py runserver" > /dev/null || pgrep -f "vite" > /dev/null; then
    echo "⚠️  Algunos procesos pueden seguir corriendo"
    echo "   Ejecuta manualmente: pkill -f 'manage.py runserver'; pkill -f 'vite'"
else
    echo "✅ Todos los servidores han sido detenidos"
fi

