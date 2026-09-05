"""
Migración para agregar columna de embeddings RAG a reportes.
Usa pgvector para búsqueda semántica.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reportes', '0015_seed_capas_urbanas_iniciales'),
    ]

    operations = [
        # Habilitar extensión pgvector (si no existe)
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS vector;",
            reverse_sql="SELECT 1;",
        ),
        # Agregar columna embedding (vector de 768 dimensiones - nomic-embed-text)
        migrations.RunSQL(
            sql="""
                ALTER TABLE reportes_reporte
                ADD COLUMN IF NOT EXISTS embedding vector(768);
            """,
            reverse_sql="""
                ALTER TABLE reportes_reporte
                DROP COLUMN IF EXISTS embedding;
            """,
        ),
        # Índice HNSW para búsqueda rápida por similitud coseno
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS reporte_embedding_hnsw_idx
                ON reportes_reporte
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64);
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS reporte_embedding_hnsw_idx;
            """,
        ),
    ]
