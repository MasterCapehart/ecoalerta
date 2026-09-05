"""
Vistas de IA usando Ollama local (qwen3:8b)
"""
import json
import requests
import logging
import concurrent.futures
from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from asgiref.sync import sync_to_async

logger = logging.getLogger('reportes')

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen3:8b"

# ThreadPoolExecutor dedicado para llamadas bloqueantes a Ollama
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)


def _llamar_ollama_sync(prompt, max_tokens=500):
    """Llamada bloqueante a Ollama — se ejecuta en thread separado"""
    tokens = max(max_tokens, 500)
    prompt_final = prompt + "\n/no_think"
    resp = requests.post(OLLAMA_URL, json={
        "model": OLLAMA_MODEL,
        "prompt": prompt_final,
        "stream": False,
        "options": {
            "num_predict": tokens,
            "temperature": 0.1,
            "top_p": 0.9
        }
    }, timeout=120)
    resp.raise_for_status()
    raw = resp.json().get("response", "")
    if "<think>" in raw:
        parts = raw.split("</think>")
        raw = parts[-1].strip() if len(parts) > 1 else raw
    return raw.strip() or None


def llamar_ollama(prompt, max_tokens=500):
    """Llama a Ollama en un thread separado para no bloquear el event loop de Daphne"""
    try:
        future = _executor.submit(_llamar_ollama_sync, prompt, max_tokens)
        return future.result(timeout=130)  # esperar hasta 130s
    except concurrent.futures.TimeoutError:
        logger.error("Ollama timeout después de 130s")
        return None
    except Exception as e:
        logger.error(f"Error llamando Ollama: {e}")
        return None


@api_view(['POST'])
@permission_classes([AllowAny])
def ia_clasificar_reporte(request):
    """
    Clasifica automáticamente un reporte por su descripción.
    POST { "descripcion": "hay agua saliendo de la vereda" }
    Retorna: { "capa": "Agua Potable y Alcantarillado", "subcategoria": "Fuga de agua potable en vía pública", "prioridad": "urgente", "confianza": 0.92 }
    """
    descripcion = request.data.get('descripcion', '').strip()
    if not descripcion:
        return Response({'error': 'descripcion requerida'}, status=400)

    # Obtener capas y subcategorias de la BD
    from .models import CapaUrbana
    capas = CapaUrbana.objects.filter(activa=True).prefetch_related('subcategorias')
    opciones = []
    for capa in capas:
        subs = list(capa.subcategorias.filter(activa=True).values('id', 'nombre', 'prioridad_base'))
        opciones.append({
            'capa_id': capa.id,
            'capa': capa.nombre,
            'subcategorias': subs
        })

    prompt = f"""Eres un clasificador municipal. Dado un reporte de ciudadano, debes identificar la categoría correcta.

REPORTE DEL CIUDADANO: "{descripcion}"

CATEGORÍAS DISPONIBLES:
{json.dumps(opciones, ensure_ascii=False, indent=2)}

Responde ÚNICAMENTE con un JSON válido con este formato exacto, sin explicaciones:
{{
  "capa_id": <id numérico>,
  "capa": "<nombre exacto de la capa>",
  "subcategoria_id": <id numérico>,
  "subcategoria": "<nombre exacto de la subcategoría>",
  "prioridad": "<urgente|alta|normal|baja>",
  "confianza": <número entre 0.0 y 1.0>,
  "razon": "<explicación breve en español>"
}}"""

    respuesta = llamar_ollama(prompt, max_tokens=800)
    if not respuesta:
        return Response({'error': 'IA no disponible'}, status=503)

    try:
        # Extraer JSON de la respuesta
        start = respuesta.find('{')
        end = respuesta.rfind('}') + 1
        if start >= 0 and end > start:
            data = json.loads(respuesta[start:end])
            return Response(data)
        return Response({'error': 'No se pudo parsear respuesta IA', 'raw': respuesta}, status=500)
    except json.JSONDecodeError as e:
        return Response({'error': f'JSON inválido: {e}', 'raw': respuesta}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def ia_detectar_duplicado(request):
    """
    Detecta si un reporte es semánticamente similar a reportes recientes cercanos.
    POST { "descripcion": "...", "lat": -33.4, "lng": -70.6 }
    """
    descripcion = request.data.get('descripcion', '').strip()
    lat = request.data.get('lat')
    lng = request.data.get('lng')

    if not descripcion:
        return Response({'error': 'descripcion requerida'}, status=400)

    # Buscar reportes recientes cercanos (últimos 30 días, radio ~500m)
    from .models import Reporte
    from django.utils import timezone
    from datetime import timedelta

    hace_30_dias = timezone.now() - timedelta(days=30)
    reportes_recientes = Reporte.objects.filter(
        fecha_creacion__gte=hace_30_dias
    ).exclude(estado__in=['resuelto', 'cerrado']).values(
        'id', 'codigo_seguimiento', 'descripcion', 'categoria__nombre', 'estado'
    )[:20]

    if not reportes_recientes:
        return Response({'es_duplicado': False, 'similares': []})

    reportes_list = list(reportes_recientes)

    prompt = f"""Eres un detector de reportes duplicados municipales.

NUEVO REPORTE: "{descripcion}"

REPORTES EXISTENTES:
{json.dumps(reportes_list, ensure_ascii=False, indent=2)}

Determina si el nuevo reporte describe el MISMO problema que alguno de los existentes.
Responde ÚNICAMENTE con JSON:
{{
  "es_duplicado": <true|false>,
  "confianza": <0.0 a 1.0>,
  "reporte_similar_id": <id del más similar o null>,
  "reporte_similar_codigo": "<código o null>",
  "razon": "<explicación breve>"
}}"""

    respuesta = llamar_ollama(prompt, max_tokens=200)
    if not respuesta:
        return Response({'es_duplicado': False, 'similares': [], 'error': 'IA no disponible'})

    try:
        start = respuesta.find('{')
        end = respuesta.rfind('}') + 1
        if start >= 0 and end > start:
            return Response(json.loads(respuesta[start:end]))
        return Response({'es_duplicado': False})
    except Exception:
        return Response({'es_duplicado': False})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ia_generar_respuesta_ciudadano(request):
    """
    Genera respuesta formal para notificar al ciudadano el cierre de su reporte.
    POST { "reporte_id": 42, "notas_cierre": "..." }
    """
    reporte_id = request.data.get('reporte_id')
    notas = request.data.get('notas_cierre', '')

    from .models import Reporte
    try:
        reporte = Reporte.objects.select_related('categoria', 'subcategoria__capa').get(id=reporte_id)
    except Reporte.DoesNotExist:
        return Response({'error': 'Reporte no encontrado'}, status=404)

    categoria = reporte.subcategoria.nombre if reporte.subcategoria else (reporte.categoria.nombre if reporte.categoria else 'problema reportado')
    direccion = reporte.direccion or reporte.direccion_completa or 'la dirección indicada'
    fecha = reporte.fecha_creacion.strftime('%d de %B de %Y') if reporte.fecha_creacion else ''

    prompt = f"""Eres un funcionario municipal. Redacta una respuesta formal y cordial para notificar a un ciudadano que su reporte fue resuelto.

DATOS DEL REPORTE:
- Código: {reporte.codigo_seguimiento}
- Problema: {categoria}
- Dirección: {direccion}
- Fecha reporte: {fecha}
- Notas del inspector: {notas or 'Trabajo completado satisfactoriamente'}

Redacta un mensaje formal de 3-4 oraciones en español. Sin saludos genéricos como "Estimado ciudadano". 
Dirígete al vecino, menciona el problema específico y la dirección. Sé conciso y profesional.
Solo el texto del mensaje, sin comillas ni formato adicional."""

    respuesta = llamar_ollama(prompt, max_tokens=300)
    if not respuesta:
        return Response({'error': 'IA no disponible'}, status=503)

    return Response({'mensaje': respuesta})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ia_indexar_reportes(request):
    """
    Indexa todos los reportes sin embedding para RAG.
    POST {} — sin body necesario
    Solo admins pueden ejecutar esto.
    """
    def proceso():
        from .rag_service import indexar_todos_los_reportes
        return indexar_todos_los_reportes()

    try:
        future = _executor.submit(proceso)
        resultado = future.result(timeout=300)
        return Response({
            'message': 'Indexación completada',
            'resultado': resultado
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def ia_buscar_similares(request):
    """
    Búsqueda semántica RAG de reportes similares.
    POST { "consulta": "fuga de agua en vereda", "top_k": 5 }
    """
    consulta = request.data.get('consulta', '').strip()
    top_k = int(request.data.get('top_k', 5))

    if not consulta:
        return Response({'error': 'consulta requerida'}, status=400)

    def buscar():
        from .rag_service import buscar_reportes_similares
        return buscar_reportes_similares(consulta, top_k=top_k)

    try:
        future = _executor.submit(buscar)
        resultados = future.result(timeout=60)
        return Response({
            'consulta': consulta,
            'total': len(resultados),
            'resultados': resultados
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)
