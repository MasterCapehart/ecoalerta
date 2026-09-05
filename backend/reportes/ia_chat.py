"""
Chat IA para administrador - consulta BD en lenguaje natural via Ollama
"""
import json
import requests
import logging
import concurrent.futures
from django.db import connection
from django.utils import timezone
from datetime import timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger('reportes')

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen3:8b"

# ThreadPoolExecutor dedicado para no bloquear el event loop de Daphne
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

SCHEMA_CONTEXT = """
Base de datos PostgreSQL del sistema municipal EcoAlerta.

TABLAS PRINCIPALES:
- reportes_reporte: id, codigo_seguimiento, descripcion, direccion, estado, prioridad, fecha_creacion, fecha_actualizacion, tiempo_resolucion_horas, es_spam, sla_escalado, fecha_limite_resolucion, categoria_id, subcategoria_id, asignado_a_id, creado_por_id
- reportes_categoriaresiduo: id, nombre
- reportes_subcategoriaurbana: id, nombre, sla_horas, prioridad_base, capa_id
- reportes_capaurbana: id, nombre, slug, departamento_id
- reportes_departamentomunicipal: id, nombre
- reportes_usuario: id, username, email, tipo (valores: ciudadano, inspector, admin)

ESTADOS de reportes: nuevo, proceso, resuelto, cerrado
PRIORIDADES: baja, normal, alta, urgente

JOINS útiles:
- reporte → capa: reportes_reporte r JOIN reportes_subcategoriaurbana s ON r.subcategoria_id=s.id JOIN reportes_capaurbana c ON s.capa_id=c.id
- reporte → depto: ...JOIN reportes_departamentomunicipal d ON c.departamento_id=d.id
- reporte → inspector: JOIN reportes_usuario u ON r.asignado_a_id=u.id

Fecha actual: {fecha_actual}
"""


def _llamar_ollama_sync(prompt, max_tokens=800):
    """Llamada bloqueante a Ollama — se ejecuta en thread separado"""
    tokens = max(max_tokens, 500)
    prompt_final = prompt + "\n/no_think"
    resp = requests.post(OLLAMA_URL, json={
        "model": OLLAMA_MODEL,
        "prompt": prompt_final,
        "stream": False,
        "options": {"num_predict": tokens, "temperature": 0.1}
    }, timeout=120)
    resp.raise_for_status()
    raw = resp.json().get("response", "")
    if "<think>" in raw:
        parts = raw.split("</think>")
        raw = parts[-1].strip() if len(parts) > 1 else raw
    return raw.strip() or None


def llamar_ollama(prompt, max_tokens=800):
    """Ejecuta Ollama en thread separado para no bloquear Daphne/ASGI"""
    try:
        future = _executor.submit(_llamar_ollama_sync, prompt, max_tokens)
        return future.result(timeout=130)
    except concurrent.futures.TimeoutError:
        logger.error("Ollama timeout después de 130s")
        return None
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        return None


def generar_sql(pregunta, fecha_actual):
    """Genera SQL para responder la pregunta usando un prompt compacto."""
    # Schema minimalista para no desperdiciar tokens
    prompt = f"""PostgreSQL. Tablas:
- reportes_reporte(id, estado, prioridad, fecha_creacion, tiempo_resolucion_horas, subcategoria_id, asignado_a_id)
- reportes_subcategoriaurbana(id, nombre, sla_horas, capa_id)
- reportes_capaurbana(id, nombre, departamento_id)
- reportes_departamentomunicipal(id, nombre)
- reportes_usuario(id, username, tipo)
estados: nuevo,proceso,resuelto,cerrado | prioridades: baja,normal,alta,urgente
Fecha: {fecha_actual}

PREGUNTA: {pregunta}

Escribe solo el SQL SELECT. Sin explicación, sin markdown:"""

    return llamar_ollama(prompt, max_tokens=800)


def ejecutar_sql_seguro(sql):
    """Ejecuta SQL de solo lectura de forma segura"""
    sql_upper = sql.upper().strip()
    # Validar que sea solo SELECT
    if not sql_upper.startswith('SELECT'):
        return None, "Solo se permiten consultas SELECT"
    # Bloquear palabras peligrosas
    for palabra in ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE', 'EXEC', '--']:
        if palabra in sql_upper:
            return None, f"SQL no permitido: contiene {palabra}"
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            columnas = [col[0] for col in cursor.description] if cursor.description else []
            filas = cursor.fetchall()
            return {'columnas': columnas, 'filas': [list(f) for f in filas], 'total': len(filas)}, None
    except Exception as e:
        return None, str(e)


def interpretar_resultados(pregunta, sql, datos, fecha_actual):
    """Paso 2: Pedir a Ollama que interprete los datos y genere KPIs"""
    datos_str = json.dumps(datos, ensure_ascii=False, default=str)

    prompt = f"""Eres un analista municipal experto. Tienes datos reales de la base de datos municipal.

PREGUNTA ORIGINAL: "{pregunta}"
FECHA ACTUAL: {fecha_actual}

SQL EJECUTADO:
{sql}

DATOS OBTENIDOS:
{datos_str}

Analiza estos datos y genera una respuesta completa con:
1. Respuesta directa a la pregunta (1-2 oraciones)
2. KPIs relevantes extraídos de los datos (usa números reales)
3. Observaciones o tendencias destacadas
4. Si aplica, una recomendación concreta

Formato de respuesta:
📊 **RESUMEN**: [respuesta directa]

📈 **KPIs**:
• [kpi 1 con valor real]
• [kpi 2 con valor real]
• [más si aplica]

💡 **OBSERVACIONES**: [análisis]

✅ **RECOMENDACIÓN**: [acción sugerida si aplica]

Usa los números EXACTOS de los datos. Responde en español. Sé conciso pero completo."""

    return llamar_ollama(prompt, max_tokens=1000)


def _buscar_contexto_sql(pregunta: str) -> str:
    """
    Búsqueda de contexto usando SQL ILIKE — sin llamar a Ollama.
    Extrae palabras clave de la pregunta y busca reportes relevantes.
    """
    # Palabras clave ignoradas
    stopwords = {'hay', 'los', 'las', 'cuantos', 'cuántos', 'de', 'en', 'la', 'el',
                 'que', 'con', 'por', 'son', 'del', 'un', 'una', 'y', 'o', 'a',
                 'se', 'al', 'mas', 'más', 'cual', 'cuál', 'como', 'cómo', 'qué'}
    palabras = [
        p.lower().strip('?,.')
        for p in pregunta.split()
        if len(p) > 3 and p.lower() not in stopwords
    ][:5]  # máximo 5 palabras clave

    if not palabras:
        return ""

    # Construir WHERE con ILIKE
    condiciones = " OR ".join([
        f"(r.descripcion ILIKE '%%{p}%%' OR c.nombre ILIKE '%%{p}%%' OR r.direccion ILIKE '%%{p}%%')"
        for p in palabras
    ])

    sql = f"""
        SELECT r.codigo_seguimiento, r.descripcion, r.estado,
               r.prioridad, r.direccion, c.nombre as categoria
        FROM reportes_reporte r
        LEFT JOIN reportes_categoriaresiduo c ON r.categoria_id = c.id
        WHERE {condiciones}
        LIMIT 5
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            filas = cursor.fetchall()

        if not filas:
            return ""

        lineas = [f"REPORTES RELACIONADOS CON LA PREGUNTA ({len(filas)}):"]
        for f in filas:
            lineas.append(
                f"• [{f[0]}] {f[5] or 'Sin cat'} | {f[2]} | {f[3]} | "
                f"{f[4] or 'Sin dir'} | {str(f[1])[:80]}"
            )
        return "\n".join(lineas)
    except Exception as e:
        logger.warning(f"_buscar_contexto_sql error: {e}")
        return ""


def interpretar_resultados_con_rag(pregunta, sql, datos, contexto_rag, fecha_actual):
    """Interpreta datos SQL + contexto RAG semántico juntos."""
    datos_str = json.dumps(datos, ensure_ascii=False, default=str)

    seccion_rag = ""
    if contexto_rag:
        seccion_rag = f"""
CONTEXTO SEMÁNTICO (reportes similares encontrados por RAG):
{contexto_rag}
"""

    prompt = f"""Eres un analista municipal experto. Tienes datos reales de la base de datos.

PREGUNTA: "{pregunta}"
FECHA: {fecha_actual}
{seccion_rag}
DATOS SQL:
{datos_str}

Analiza y responde con:
📊 **RESUMEN**: [respuesta directa]

📈 **KPIs**:
• [kpi con valor real]
• [más si aplica]

💡 **OBSERVACIONES**: [análisis, menciona reportes específicos del contexto RAG si son relevantes]

✅ **RECOMENDACIÓN**: [acción concreta]

Usa números EXACTOS. Español. Conciso."""

    return llamar_ollama(prompt, max_tokens=1000)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ia_chat_admin(request):
    """
    Chat IA para el administrador con RAG.
    POST { "pregunta": "..." }
    Combina SQL sobre BD estructurada + búsqueda semántica RAG.
    """
    pregunta = request.data.get('pregunta', '').strip()
    if not pregunta:
        return Response({'error': 'pregunta requerida'}, status=400)

    fecha_actual = timezone.now().strftime('%Y-%m-%d %H:%M')

    def proceso_completo():
        # Paso 1: RAG ligero — búsqueda por texto en BD (sin Ollama, instantánea)
        # Usamos SQL ILIKE para encontrar reportes relevantes sin consumir Ollama
        try:
            contexto_rag = _buscar_contexto_sql(pregunta)
        except Exception as e:
            logger.warning(f"RAG SQL falló: {e}")
            contexto_rag = ""

        # Paso 2: Generar SQL + Ejecutar + Interpretar (todo con Qwen3)
        sql = generar_sql(pregunta, fecha_actual)
        if not sql:
            return None, None, None, 'IA no disponible', contexto_rag
        sql_limpio = sql.replace('```sql', '').replace('```', '').strip()

        datos, error_sql = ejecutar_sql_seguro(sql_limpio)
        if error_sql:
            return sql_limpio, None, f'No pude ejecutar la consulta: {error_sql}', None, contexto_rag

        respuesta = interpretar_resultados_con_rag(
            pregunta, sql_limpio, datos, contexto_rag, fecha_actual
        )
        if not respuesta:
            respuesta = f"Datos encontrados: {datos['total']} registros."
        return sql_limpio, datos, respuesta, None, contexto_rag

    # Ejecutar TODO directamente — sin thread externo
    # El timeout lo maneja Daphne con -t 300
    try:
        sql, datos, respuesta, error, contexto_rag = proceso_completo()
    except Exception as e:
        logger.error(f"Error en chat admin: {e}")
        return Response({'error': str(e)}, status=503)

    if error:
        return Response({'error': error}, status=503)

    return Response({
        'respuesta': respuesta,
        'sql': sql,
        'rag_usado': bool(contexto_rag),
        'datos': {
            'columnas': datos['columnas'],
            'filas': datos['filas'][:10],
            'total': datos['total']
        } if datos else None
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ia_resumen_departamento(request):
    """
    Genera resumen ejecutivo del día para un departamento.
    POST { "departamento_id": 5 }
    """
    depto_id = request.data.get('departamento_id')

    from .models import DepartamentoMunicipal, Reporte

    try:
        depto = DepartamentoMunicipal.objects.get(id=depto_id)
    except DepartamentoMunicipal.DoesNotExist:
        return Response({'error': 'Departamento no encontrado'}, status=404)

    hoy = timezone.now().date()
    hace_7_dias = timezone.now() - timedelta(days=7)

    # Obtener stats reales del departamento
    reportes_activos = Reporte.objects.filter(
        subcategoria__capa__departamento_id=depto_id
    ).exclude(estado__in=['resuelto', 'cerrado'])

    stats = {
        'departamento': depto.nombre,
        'fecha': hoy.strftime('%d/%m/%Y'),
        'total_activos': reportes_activos.count(),
        'urgentes': reportes_activos.filter(prioridad='urgente').count(),
        'altos': reportes_activos.filter(prioridad='alta').count(),
        'sla_vencidos': reportes_activos.filter(fecha_limite_resolucion__lt=timezone.now()).count(),
        'nuevos_hoy': Reporte.objects.filter(
            subcategoria__capa__departamento_id=depto_id,
            fecha_creacion__date=hoy
        ).count(),
        'resueltos_7dias': Reporte.objects.filter(
            subcategoria__capa__departamento_id=depto_id,
            estado__in=['resuelto', 'cerrado'],
            fecha_actualizacion__gte=hace_7_dias
        ).count(),
    }

    prompt = f"""Eres el asistente del director municipal. Genera un resumen ejecutivo del día para el departamento.

DATOS REALES:
{json.dumps(stats, ensure_ascii=False)}

Genera un resumen ejecutivo breve (4-6 oraciones) en español que:
1. Informe el estado general del departamento hoy
2. Destaque si hay urgencias o SLA vencidos que requieren atención inmediata
3. Mencione el progreso (resueltos esta semana)
4. Incluya una prioridad de acción clara

Tono: profesional, directo, sin relleno. Solo el texto del resumen."""

    respuesta = llamar_ollama(prompt, max_tokens=400)
    if not respuesta:
        respuesta = f"El departamento tiene {stats['total_activos']} reportes activos, {stats['urgentes']} urgentes y {stats['sla_vencidos']} con SLA vencido."

    return Response({'resumen': respuesta, 'stats': stats})
