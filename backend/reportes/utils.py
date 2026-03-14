from datetime import datetime, timedelta
from django.utils import timezone
from PIL import Image, ExifTags
from rest_framework.exceptions import ValidationError

def validate_image_metadata(image_file):
    """
    Valida metadatos de la imagen.
    - Rechaza si es una imagen muy antigua (> 1 año).
    - Puede expandirse para validar GPS.
    """
    try:
        img = Image.open(image_file)
        exif_data = img._getexif()
        
        if not exif_data:
            return  # Si no tiene EXIF, lo dejamos pasar (muchas cámaras no lo guardan)

        # Buscar fecha de creación
        # DateTimeOriginal ID = 36867
        date_str = exif_data.get(36867)
        
        if date_str:
            # Formato EXIF: "YYYY:MM:DD HH:MM:SS"
            try:
                dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                # Si hoy es 2025, y la foto es de 2023, alertar.
                year_ago = datetime.now() - timedelta(days=365)
                if dt < year_ago:
                    # Opcional: Rechazar o solo marcar flag
                    # Por ahora rechazamos para cumplir política estricta
                    raise ValidationError("La fotografía es demasiado antigua (> 1 año). Por favor toma una foto actual.")
            except ValueError:
                pass # Formato irreconocible, ignorar
                
    except ValidationError:
        raise
    except Exception as e:
        # Error leyendo imagen, no bloqueamos x esto
        print(f"Error analizando EXIF: {e}")
