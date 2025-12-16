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
- Predicciones locales (beta): `POST /api/reportes/predicciones/`

## Predicciones locales con ML (solo desarrollo)

1. **Instala las dependencias nuevas** (ya incluidas en `requirements.txt`): `pip install -r requirements.txt`.
2. **Entrena el modelo local** usando tus datos reales:
   ```bash
   cd backend
   python manage.py train_prediction_model --min-samples 15
   ```
   El modelo se guarda en `reportes/ml/artifacts/`.
3. **Consume el endpoint local**:
   ```bash
   curl -X POST http://localhost:8000/api/reportes/predicciones/ \
     -H "Content-Type: application/json" \
     -d '{
       "categoria": 1,
       "lat": -33.45,
       "lng": -70.66,
       "descripcion": "Residuos en la esquina norte",
       "tiene_foto": true
     }'
   ```
   La respuesta incluye `probability`, `estimated_resolution_days`, `risk_level` y metadatos del modelo.
   - En el **Dashboard Municipal → vista “Estadísticas”** verás automáticamente los reportes críticos según el modelo, y (opcional) un formulario para simular escenarios manuales.
4. **Solo local:** En producción el endpoint responde `503` a menos que definas `ENABLE_LOCAL_PREDICTIONS=1` explícitamente.
5. **Sin PostgreSQL?** Exporta `USE_SQLITE_LOCAL=1` antes de ejecutar `manage.py` para usar automáticamente `db.sqlite3` durante entrenamiento o pruebas.

### Predicciones en Azure

- Para habilitarlas en App Service (variables, entrenamiento automático, logs) revisa **[docs/ML_AZURE.md](docs/ML_AZURE.md)**.

## 🚀 Despliegue en Azure con CI/CD

Este proyecto está configurado para desplegarse automáticamente en Azure usando GitHub Actions.

### Configuración Rápida

1. **Ejecuta el script de configuración:**
   ```bash
   ./setup-azure.sh
   ```

2. **Configura los secrets en GitHub:**
   - Ve a tu repositorio → Settings → Secrets and variables → Actions
   - Agrega los secrets necesarios (ver `AZURE_DEPLOY.md`)

3. **Haz push a `main`:**
   - Los cambios se desplegarán automáticamente

### Documentación Completa

Para instrucciones detalladas, consulta: **[AZURE_DEPLOY.md](AZURE_DEPLOY.md)**

### Recursos Creados

- **Backend**: Azure App Service (Django)
- **Frontend**: Azure Static Web Apps (React)
- **Base de datos**: Azure PostgreSQL (ya configurado)

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

### Azure
- **Error de despliegue**: Revisa los logs en GitHub Actions y Azure Portal
- **CORS errors**: Verifica que `AZURE_FRONTEND_URL` esté configurado correctamente
- **Base de datos no conecta**: Verifica las credenciales y el firewall de PostgreSQL
