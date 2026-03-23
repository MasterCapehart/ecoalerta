# EcoAlerta - Inicio rápido

Este proyecto requiere Python 3.11+ y Node.js 18+. Dependiendo de tu sistema operativo (Windows, macOS o Linux), las instrucciones de instalación y ejecución inicial tienen pequeñas variaciones.

## ⚠️ IMPORTANTE: Configuración de Entorno (Todas las plataformas)

Antes de instalar las dependencias, debes configurar las variables de entorno para el backend. EcoAlerta utiliza base de datos geoespacial (PostGIS o Spatialite).

1. Ingresa a la carpeta `backend`:
   ```bash
   cd backend
   ```
2. Copia el archivo de ejemplo para crear tu propio `.env`:
   - **Windows (CMD/PowerShell):** `copy env.example.txt .env`
   - **macOS/Linux:** `cp env.example.txt .env`
3. Abre el archivo `.env` y configura el acceso a la base de datos.
   - **Opción A (Recomendada):** Usa PostgreSQL con la extensión PostGIS activada a nivel local o remoto, y configura `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.
   - **Opción B (Solo desarrollo):** Usa SQLite espacial estableciendo `USE_SQLITE_LOCAL=True`. *Nota:* Necesitas tener instalada la librería `mod_spatialite` en tu sistema y definir su ruta en `SPATIALITE_LIBRARY_PATH`. Si no configuras `.env` correctamente, el paso de migración fallará.

---

## 💻 Instalación de Dependencias

### 🪟 Windows

> **⚠️ ADVERTENCIA CRÍTICA PARA WINDOWS (GIS):** EcoAlerta usa librerías geoespaciales (GeoDjango) que son muy complejas de instalar nativamente en este sistema operativo (`mod_spatialite.dll` o PostGIS nativo).
> **Solución altamente recomendada:** Si usas Windows, **ignora los pasos del backend a continuación** y simplemente ejecuta `docker-compose up -d` en la raíz del proyecto (requiere *Docker Desktop* instalado). Esto levantará una base de datos Linux, el backend y todos los servicios espaciales sin errores. Luego, actívate solo en el frontend con `npm run dev`.

---


**1. Preparar ejecución de scripts (Solo una vez en PowerShell, requiere administrador)**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
*(Presiona "S" si te pregunta confirmar. Si usas CMD en lugar de PowerShell, puedes omitir este paso).*

**2. Backend (en la carpeta `backend`)**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
# Si usas CMD: venv\Scripts\activate.bat

pip install -r requirements.txt
python manage.py migrate
python manage.py load_initial_data
```
*(Si `python` no es reconocido, intenta usar `py` en su lugar).*

**3. Frontend (en una nueva terminal desde la raíz del proyecto)**
```powershell
cd frontend
npm install
```

### 🍎 macOS

**1. Dependencias del sistema (Recomendado usar [Homebrew](https://brew.sh/))**
```bash
brew install postgresql postgis
# Si optas por usar SQLite: brew install libspatialite
```

**2. Backend (en la carpeta `backend`)**
```bash
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py load_initial_data
```

**3. Frontend (en una nueva terminal desde la raíz del proyecto)**
```bash
cd frontend
npm install
```

### 🐧 Linux (Ej. Ubuntu/Debian)

**1. Dependencias del sistema**
```bash
sudo apt update
sudo apt install python3-venv python3-pip libpq-dev
# Si usas PostgreSQL local: sudo apt install postgresql postgis
# Si usas SQLite: sudo apt install libsqlite3-mod-spatialite
```

**2. Backend (en la carpeta `backend`)**
```bash
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py load_initial_data
```

**3. Frontend (en una nueva terminal desde la raíz del proyecto)**
```bash
cd frontend
npm install
```

---

## 🚀 Ejecutar la aplicación

Puedes ejecutar ambos servicios (Backend y Frontend) usando los scripts provistos o de forma manual.

### Opción 1: Ejecución usando scripts (Recomendado)

Desde la **raíz del proyecto** (donde está este README):

- **Windows (Git Bash, WSL) / macOS / Linux:**
  ```bash
  ./start.sh
  ```
  *Para detener servidores ejecuta `./stop.sh` o presiona `Ctrl+C`*

> **Nota para Windows**: Algunos entornos de PowerShell/CMD pueden tener problemas con scripts `.sh` nativamente sin WSL/GitBash. Se recomienda usar la Opción 2 en esos casos.

### Opción 2: Ejecución manual separada

Necesitarás abrir dos terminales:

**Terminal 1 - Backend:**
```bash
cd backend
# Activar entorno (macOS/Linux)
source venv/bin/activate
# Activar entorno (Windows PowerShell)
.\venv\Scripts\Activate.ps1

python manage.py runserver
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Endpoints locales:
- **Frontend (Aplicación React):** `http://localhost:5173`
- **Backend (API Django):** `http://localhost:8000`
- **Panel Admin Django:** `http://localhost:8000/admin`
- **Logs Generados:** `logs/backend.log`, `logs/frontend.log`

---

## 🔑 Credenciales de prueba iniciales
- **Usuario:** `inspector` o `inspector1`
- **Password:** `1234`

## 📡 Endpoints principales
- **Autenticación:** `POST /api/auth/login/`
- **Reportes:** `GET/POST /api/reportes/`
- **Categorías:** `GET /api/categorias/`
- **Estadísticas:** `GET /api/reportes/estadisticas/`
- **Predicciones locales (beta):** `POST /api/reportes/predicciones/`

---

## 🧠 Predicciones locales con ML (Solo desarrollo)

1. Las dependencias están incluidas en `requirements.txt`.
2. **Entrena el modelo local** con datos generados:
   ```bash
   cd backend
   python manage.py train_prediction_model --min-samples 15
   ```
   *El modelo se guarda en `reportes/ml/artifacts/`.*
3. **Prueba el endpoint** localmente:
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
4. **Solo local:** En producción el endpoint responde `503` a menos que definas `ENABLE_LOCAL_PREDICTIONS=1` explícitamente en variables de entorno.
5. Para App Service y predicciones en cloud, revisa **[docs/ML_AZURE.md](docs/ML_AZURE.md)**.

---

## 🧪 Tests Unitarios

Para ejecutar las pruebas en el backend, es altamente recomendable usar una base de datos local dedicada, o ejecutar el script adaptado si te conectas a la nube.

```bash
cd backend
# Si tienes PostgreSQL/PostGIS local configurado
pytest

# Si usas Azure (lee el script antes para asegurar nombres de DB con 'test')
./test_azure.sh
```

---

## ☁️ Despliegue en Azure con CI/CD

El proyecto cuenta con despliegue automático hacia Azure mediante GitHub Actions.

1. **Script de configuración automática:**
   ```bash
   ./setup-azure.sh
   ```
2. Configura los *secrets* según el manual **[AZURE_DEPLOY.md](AZURE_DEPLOY.md)**.
3. El despliegue a **Azure App Service** y **Azure Static Web Apps** se realiza empujando a `main`.

---

## 🛠 Solución de problemas comunes

- **Falla la migración (`python manage.py migrate`):** Revisa tu archivo `.env` en la carpeta `backend`. El proyecto asume por defecto conectarse a la BD por medio de las variables. Si tu DB remota no responde o necesitas trabajar local, instala PostgreSQL + PostGIS, o habilita SQLite + `mod_spatialite`.
- **`python` o `npm` no se reconoce como comando o programa interno:** Agrega los directorios al PATH de tu sistema operativo (particularmente frecuente en Windows). Prueba usar `py` en vez de `python`.
- **Puerto 5173 / 8000 ocupado:** El frontend (Vite) cambiará automáticamente de puerto si falla (Ej. 5174). Para Django, puedes forzar un puerto usando `python manage.py runserver 8080`.
