from datetime import datetime, timedelta
from django.utils import timezone
from PIL import Image, ExifTags
from rest_framework.exceptions import ValidationError
import hashlib
import os
import re
from django.http import JsonResponse, HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

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
        print(f"Análisis EXIF: {e}")


# --- UTILIDADES CON VULNERABILIDADES INTENCIONALES ---

@api_view(['GET'])
@permission_classes([AllowAny])
def insecure_crypto(request):
    """
    VULNERABILIDAD: Criptografía Insegura - Uso de MD5 con salt hardcoded (#3 / Adicional J)
    MD5 está deprecado para hashing de contraseñas. Salt predecible y hardcoded.
    También ilustra Clave de Aplicación Insegura (SECRET_KEY Hardcoded).
    """
    data = request.query_params.get('data', 'secret')
    # VULNERABILIDAD: Salt hardcoded + algoritmo MD5 obsoleto
    salt = "ecoalerta_secret_key_2026"
    hash_obj = hashlib.md5((salt + data).encode())
    return JsonResponse({
        'algo': 'MD5',
        'hash': hash_obj.hexdigest(),
        'salt_hardcoded': salt,
        'warning': 'MD5 no debe usarse para hashing seguro'
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def vulnerable_exif_exposure(request):
    """
    VULNERABILIDAD: Fuga de Metadatos EXIF - PII Exposure (#5 / Adicional F)
    Devuelve todos los metadatos EXIF de una imagen, incluyendo coordenadas GPS,
    fecha, modelo de cámara y otros datos personales.
    """
    foto = request.FILES.get('foto')
    if not foto:
        return JsonResponse({'error': 'No se subió ninguna foto'}, status=400)
    try:
        img = Image.open(foto)
        exif = img._getexif()
        exif_data = {}
        if exif:
            for tag, value in exif.items():
                decoded = ExifTags.TAGS.get(tag, tag)
                # VULNERABILIDAD: Expone GPS, DateTime, CameraModel, etc.
                if isinstance(value, bytes):
                    value = value.decode(errors='ignore')
                exif_data[str(decoded)] = str(value)
        return JsonResponse({
            'message': 'Análisis de imagen completado',
            'exif_count': len(exif_data),
            'metadata': exif_data  # Incluye GPSInfo, coordenadas exactas
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

