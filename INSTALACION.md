# Guía de Instalación - EcoAlerta

## ⚠️ Error Detectado

El error indica que `axios` no está instalado. Aunque está en el `package.json`, necesitas ejecutar `npm install` para instalarlo.

## Solución Rápida

### En el directorio frontend:

```bash
cd frontend
npm install
```

Esto instalará todas las dependencias, incluyendo:
- `axios` (nuevo)
- `react-hook-form` (nuevo)
- Todas las demás dependencias existentes

## Instalación Completa

### 1. Backend (Python)

```bash
cd backend
python -m venv venv

# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows CMD
venv\Scripts\activate.bat

# macOS/Linux
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Frontend (Node.js)

```bash
cd frontend
npm install
```

### 3. Crear Migraciones (Backend)

```bash
cd backend
python manage.py makemigrations
python manage.py migrate
python manage.py load_initial_data
```

### 4. Iniciar Servidores

**Opción 1: Scripts**
```bash
# Desde la raíz del proyecto
./start.sh
```

**Opción 2: Manual**

Terminal 1 - Backend:
```bash
cd backend
source venv/bin/activate  # o .\venv\Scripts\Activate.ps1 en Windows
python manage.py runserver
```

Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

**Opción 3: Docker**
```bash
docker-compose up
```

## Verificación

Después de instalar, verifica que todo funcione:

1. **Backend**: http://localhost:8000/api/health/
2. **Frontend**: http://localhost:5173
3. **API Docs**: http://localhost:8000/api/docs/

## Dependencias Nuevas Agregadas

### Backend
- `djangorestframework-simplejwt` - Autenticación JWT
- `drf-spectacular` - Documentación API
- `django-redis` - Caché con Redis
- `pytest` y `pytest-django` - Testing
- `black` y `flake8` - Formateo y linting

### Frontend
- `axios` - Cliente HTTP
- `react-hook-form` - Validación de formularios (para futuras mejoras)

## Si el Error Persiste

1. Elimina `node_modules` y `package-lock.json`:
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

2. Verifica que Node.js esté instalado:
   ```bash
   node --version
   npm --version
   ```

3. Si estás en Windows y npm no se reconoce, asegúrate de que Node.js esté en el PATH.

