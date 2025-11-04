#!/bin/bash

echo "🌱 Instalando Backend EcoAlerta..."
echo ""

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
fi

# Activitar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias
echo "📥 Instalando dependencias..."
pip install -r requirements.txt

# Copiar archivo de entorno si no existe
if [ ! -f ".env" ]; then
    echo "📝 Copiando archivo de configuración..."
    cp env.example.txt .env
    echo "⚠️  Recuerda editar el archivo .env con tus credenciales de PostgreSQL"
fi

# Crear migraciones
echo "🗄️  Creando migraciones..."
python manage.py makemigrations

# Aplicar migraciones
echo "🔨 Aplicando migraciones..."
python manage.py migrate

# Crear superusuario
echo ""
echo "👤 Creando superusuario..."
python manage.py createsuperuser

# Cargar datos iniciales
echo "📊 Cargando datos iniciales..."
python manage.py load_initial_data

echo ""
echo "✅ ¡Instalación completada!"
echo ""
echo "Para ejecutar el servidor:"
echo "  source venv/bin/activate"
echo "  python manage.py runserver"
echo ""

