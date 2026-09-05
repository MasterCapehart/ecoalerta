"""
Servicio RAG (Retrieval-Augmented Generation) para EcoAlerta.

Flujo:
1. Texto → nomic-embed-text → vector de 768 dimensiones
2. Vector guardado en PostgreSQL con pgvector
3. Búsqueda semántica por similitud coseno
4. Contexto relevante → Qwen3 genera respuesta mejorada
"""
import json
import requests
import logging
import concurrent.futures
from django.db import connection

logger = logging.getLogger('reportes')

OLLAMA_URL = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"
EMBED_DIM = 768

_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)


# ── 1. EMBEDDINGS ─────────────────────────────────────────────────────────────

def _generar_embedding_sync(texto: str) -> list[float] | None:
    """Convierte texto a vector usando nomic-embed-text (bloqueante)."""
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": texto},
            timeout=30
        )
        resp.raise_for_status()
        return resp.json().get("embedding")
    except Exception as e:
        logger.error(f"Error generando embedding: {e}")
        return None


def generar_embedding(texto: str) -> list[float] | None:
    """Genera embedding en thread separado para no bloquear Daphne."""
    try:
        future = _executor.submit(_generar_embedding_sync, texto)
        return future.result(timeout=35)
    except Exception as e:
        logger.error(f"Embedding timeout/error: {e}")
        return None


# ── 2. INDEXACIÓN ─────────────────────────────────────────────────────────────

def _texto_para_indexar(reporte) -> str:
    """
    Construye el texto que se vectorizará para cada reporte.
    Combina los campos más relevantes semánticamente.
    """
    partes = []
    if reporte.descripcion:
        partes.append(reporte.descripcion)
    if reporte.direccion:
        partes.append(f"Dirección: {reporte.direccion}")
    if hasattr(reporte, 'categoria') and reporte.categoria:
        partes.append(f"Categoría: {reporte.categoria.nombre}")
    if hasattr(reporte, 'subcategoria') and reporte.subcategoria:
        partes.append(f"Tipo: {reporte.subcategoria.nombre}")
        if reporte.subcategoria.capa:
            partes.append(f"Área: {reporte.subcategoria.capa.nombre}")
    partes.append(f"Estado: {reporte.estado}")
    partes.append(f"Prioridad: {reporte.prioridad}")
    return ". ".join(partes)


def indexar_reporte(reporte_id: int) -> bool:
    """
    Genera y guarda el embedding de un reporte específico.
    Llamar cuando se crea o actualiza un reporte.
    """
    from .models import Reporte
    try:
        reporte = Reporte.objects.select_related(
            'categoria', 'subcategoria__capa'
        ).get(id=reporte_id)

        texto = _texto_para_indexar(reporte)
        embedding = generar_embedding(texto)

        if embedding is None:
            logger.warning(f"No se pudo generar embedding para reporte {reporte_id}")
            return False

        # Guardar vector en BD usando SQL directo (pgvector)
        vector_str = "[" + ",".join(str(v) for v in embedding) + "]"
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE reportes_reporte SET embedding = %s::vector WHERE id = %s",
                [vector_str, reporte_id]
            )

        logger.info(f"Reporte {reporte_id} indexado correctamente")
        return True

    except Exception as e:
        logger.error(f"Error indexando reporte {reporte_id}: {e}")
        return False


def indexar_todos_los_reportes() -> dict:
    """
    Indexa todos los reportes sin embedding.
    Para ejecutar manualmente o como tarea programada.
    """
    from .models import Reporte

    sin_embedding = list(
        Reporte.objects.select_related('categoria', 'subcategoria__capa')
        .extra(where=["embedding IS NULL"])
        .values_list('id', flat=True)
    )

    total = len(sin_embedding)
    exitosos = 0
    fallidos = 0

    logger.info(f"Iniciando indexación de {total} reportes...")

    for reporte_id in sin_embedding:
        if indexar_reporte(reporte_id):
            exitosos += 1
        else:
            fallidos += 1

    resultado = {
        'total': total,
        'exitosos': exitosos,
        'fallidos': fallidos
    }
    logger.info(f"Indexación completada: {resultado}")
    return resultado


# ── 3. BÚSQUEDA SEMÁNTICA ─────────────────────────────────────────────────────

def buscar_reportes_similares(
    texto_consulta: str,
    top_k: int = 5,
    umbral_similitud: float = 0.3,
    filtros: dict = None
) -> list[dict]:
    """
    Busca reportes semánticamente similares a una consulta.

    Args:
        texto_consulta: Pregunta o descripción a buscar
        top_k: Número máximo de resultados
        umbral_similitud: Similitud coseno mínima (0-1, más alto = más estricto)
        filtros: Dict con filtros adicionales (estado, prioridad, etc.)

    Returns:
        Lista de reportes con su similitud
    """
    embedding = generar_embedding(texto_consulta)
    if embedding is None:
        return []

    vector_str = "[" + ",".join(str(v) for v in embedding) + "]"

    # Construir cláusulas WHERE adicionales
    where_extra = "AND r.embedding IS NOT NULL"
    params = [vector_str, vector_str, umbral_similitud, top_k]

    if filtros:
        if filtros.get('estado'):
            where_extra += f" AND r.estado = '{filtros['estado']}'"
        if filtros.get('prioridad'):
            where_extra += f" AND r.prioridad = '{filtros['prioridad']}'"
        if filtros.get('solo_activos'):
            where_extra += " AND r.estado NOT IN ('resuelto', 'cerrado')"

    sql = f"""
        SELECT
            r.id,
            r.codigo_seguimiento,
            r.descripcion,
            r.direccion,
            r.estado,
            r.prioridad,
            r.fecha_creacion,
            cat.nombre AS categoria_nombre,
            sub.nombre AS subcategoria_nombre,
            capa.nombre AS capa_nombre,
            1 - (r.embedding <=> %s::vector) AS similitud
        FROM reportes_reporte r
        LEFT JOIN reportes_categoriaresiduo cat ON r.categoria_id = cat.id
        LEFT JOIN reportes_subcategoriaurbana sub ON r.subcategoria_id = sub.id
        LEFT JOIN reportes_capaurbana capa ON sub.capa_id = capa.id
        WHERE 1 - (r.embedding <=> %s::vector) >= %s
        {where_extra}
        ORDER BY similitud DESC
        LIMIT %s
    """

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            columnas = [col[0] for col in cursor.description]
            filas = cursor.fetchall()

        resultados = []
        for fila in filas:
            r = dict(zip(columnas, fila))
            r['fecha_creacion'] = r['fecha_creacion'].strftime('%d/%m/%Y %H:%M') if r['fecha_creacion'] else None
            r['similitud'] = round(float(r['similitud']), 3)
            resultados.append(r)

        return resultados

    except Exception as e:
        logger.error(f"Error en búsqueda semántica: {e}")
        return []


# ── 4. CONTEXTO RAG PARA EL CHAT ──────────────────────────────────────────────

def obtener_contexto_rag(pregunta: str, max_reportes: int = 5) -> str:
    """
    Busca reportes relevantes y los formatea como contexto para Qwen3.
    """
    reportes = buscar_reportes_similares(
        texto_consulta=pregunta,
        top_k=max_reportes,
        umbral_similitud=0.25
    )

    if not reportes:
        return ""

    lineas = [f"REPORTES RELEVANTES ENCONTRADOS ({len(reportes)}):"]
    for i, r in enumerate(reportes, 1):
        categoria = r.get('subcategoria_nombre') or r.get('categoria_nombre') or 'Sin categoría'
        lineas.append(
            f"{i}. [{r['codigo_seguimiento']}] {categoria} | "
            f"Estado: {r['estado']} | Prioridad: {r['prioridad']} | "
            f"Dirección: {r.get('direccion','N/D')} | "
            f"Fecha: {r.get('fecha_creacion','N/D')} | "
            f"Similitud: {r['similitud']:.0%}\n"
            f"   Descripción: {r['descripcion'][:150] if r['descripcion'] else 'Sin descripción'}"
        )

    return "\n".join(lineas)
