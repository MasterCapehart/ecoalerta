# EcoAlerta - Inicio rápido

## ⚠️ IMPORTANTE para Windows

Antes de empezar, ejecuta esto en PowerShell (solo una vez):

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Presiona "S" cuando te pregunte si estás seguro.

**Alternativa:** Si prefieres evitar PowerShell, usa Command Prompt (cmd.exe) en su lugar.

## Requisitos
- Python 3.11+
- Node.js 18+ y npm
- macOS/Linux/Windows

## Instalar dependencias

### Windows (PowerShell o CMD)

```powershell
# Backend
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1  # PowerShell
# O si usas CMD: venv\Scripts\activate.bat
pip install -r requirements.txt
python manage.py migrate
python manage.py load_initial_data

# Frontend
cd ..\frontend
npm install
```

**Si tienes problemas con `.\venv\Scripts\Activate.ps1` en PowerShell:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Si tienes problemas con npm en PowerShell:**
```powershell
# Opción 1: Ejecutar el comando de política (arriba)
# Opción 2: Usar CMD en lugar de PowerShell
# Opción 3: Usar npm.cmd directamente
& "C:\Program Files\nodejs\npm.cmd" install
```

### macOS/Linux

```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py load_initial_data

# Frontend
cd ../frontend
npm install
```

## Ejecutar ambos servicios (recomendado)

### Windows
```powershell
# Desde la raíz del proyecto
.\start.sh
# Para detener
.\stop.sh
```

**Nota:** Si `start.sh` no funciona en Windows, ejecuta manualmente:

```powershell
# Terminal 1 - Backend
cd backend
.\venv\Scripts\Activate.ps1
python manage.py runserver

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### macOS/Linux
```bash
# Desde la raíz del proyecto
./start.sh
# Para detener
./stop.sh
```

**URLs:**
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- Logs: `logs/backend.log`, `logs/frontend.log`

## Ejecutar por separado (opcional)

### Windows
```powershell
# Backend
cd backend
.\venv\Scripts\Activate.ps1
python manage.py runserver

# Frontend (en otra terminal)
cd frontend
npm run dev
```

### macOS/Linux
```bash
# Backend
cd backend
source venv/bin/activate
python manage.py runserver

# Frontend
cd frontend
npm run dev
```

## Credenciales de prueba
- Usuario: `inspector` o `inspector1`
- Password: `1234`

## Endpoints principales
- Autenticación: `POST /api/auth/login/`
- Reportes: `GET/POST /api/reportes/`
- Categorías: `GET /api/categorias/`
- Estadísticas: `GET /api/reportes/estadisticas/`

## Solución de problemas

### Windows
- **Error con `source venv/bin/activate`**: En Windows usa `.\venv\Scripts\Activate.ps1` (PowerShell) o `venv\Scripts\activate.bat` (CMD)
- **Error de política de ejecución en PowerShell**: Ejecuta `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- **npm no funciona en PowerShell**: Ejecuta el comando de política de arriba o usa CMD en su lugar
- **`python` no reconocido**: Prueba con `py` en lugar de `python`, o asegúrate de tener Python instalado y en el PATH

### General
- El puerto 5173 ocupado: Vite arrancará en otro puerto (p. ej. 5174).
- 404 en `/`: es normal. Usa `/api/` o el frontend.
- Si falta `venv`: vuelve a crear y reinstalar dependencias del backend.
