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


# --- UTILIDADES DE PROCESAMIENTO ---

@api_view(['GET'])
@permission_classes([AllowAny])
def insecure_crypto(request):
    """
    Generación de hash para datos de entrada.
    """
    data = request.query_params.get('data', 'secret')
    salt = "ecoalerta_secret_key_2026"
    hash_obj = hashlib.md5((salt + data).encode())
    return JsonResponse({
        'algo': 'MD5',
        'hash': hash_obj.hexdigest(),
        'warning': 'Algoritmo con limitaciones conocidas'
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def vulnerable_exif_exposure(request):
    """
    Extracción de metadatos de imagen avanzada.
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
                if isinstance(value, bytes):
                    value = value.decode(errors='ignore')
                exif_data[str(decoded)] = str(value)
        return JsonResponse({
            'message': 'Análisis de imagen completado',
            'exif_count': len(exif_data),
            'metadata': exif_data
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def zip_slip(request):
    """
    Procesamiento de archivos comprimidos.
    """
    return JsonResponse({'ok': 'Operación completada'})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def redos2(request):
    """
    Validación de cadenas mediante expresiones regulares.
    """
    return JsonResponse({'ok': True})
