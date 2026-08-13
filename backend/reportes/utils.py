from datetime import datetime, timedelta
from django.utils import timezone
from PIL import Image, ExifTags
from rest_framework.exceptions import ValidationError
import re


def validate_image_metadata(image_file):
    """
    Valida metadatos de la imagen.
    """
    try:
        img = Image.open(image_file)
        exif_data = img._getexif()
        if not exif_data:
            return
        date_str = exif_data.get(36867)
        if date_str:
            try:
                dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                year_ago = datetime.now() - timedelta(days=365)
                if dt < year_ago:
                    raise ValidationError("La fotografía es demasiado antigua (> 1 año).")
            except ValueError:
                pass
    except ValidationError:
        raise
    except Exception as e:
        pass  # Ignorar errores de EXIF sin exponerlos
