"""
Data migration: Puebla las 6 capas urbanas iniciales con sus subcategorías.
Incluye departamentos municipales genéricos configurables desde el admin.
"""
from django.db import migrations


CAPAS_DATA = [
    {
        "nombre": "Medio Ambiente",
        "slug": "medio-ambiente",
        "descripcion": "Microbasurales, residuos y contaminación ambiental",
        "icono": "leaf.fill",
        "color_hex": "#2ECC71",
        "orden": 1,
        "departamento": "Dirección de Medio Ambiente",
        "subcategorias": [
            {"nombre": "Microbasural en vía pública", "icono": "trash.fill", "sla_horas": 48, "prioridad_base": "alta", "orden": 1},
            {"nombre": "Residuos domésticos", "icono": "bag.fill", "sla_horas": 72, "prioridad_base": "normal", "orden": 2},
            {"nombre": "Escombros y construcción", "icono": "hammer.fill", "sla_horas": 96, "prioridad_base": "normal", "orden": 3},
            {"nombre": "Residuos voluminosos (muebles/electro)", "icono": "sofa.fill", "sla_horas": 72, "prioridad_base": "normal", "orden": 4},
            {"nombre": "Residuos peligrosos", "icono": "exclamationmark.triangle.fill", "sla_horas": 24, "prioridad_base": "urgente", "orden": 5},
            {"nombre": "Contaminación de agua o suelo", "icono": "drop.fill", "sla_horas": 24, "prioridad_base": "urgente", "orden": 6},
        ]
    },
    {
        "nombre": "Vialidad",
        "slug": "vialidad",
        "descripcion": "Calles, veredas y pavimento en mal estado",
        "icono": "road.lanes",
        "color_hex": "#E67E22",
        "orden": 2,
        "departamento": "Dirección de Obras",
        "subcategorias": [
            {"nombre": "Bache en calzada", "icono": "car.fill", "sla_horas": 72, "prioridad_base": "alta", "orden": 1},
            {"nombre": "Vereda dañada o levantada", "icono": "figure.walk", "sla_horas": 96, "prioridad_base": "normal", "orden": 2},
            {"nombre": "Cuneta tapada o rota", "icono": "water.waves", "sla_horas": 72, "prioridad_base": "normal", "orden": 3},
            {"nombre": "Derrumbe o erosión", "icono": "mountain.2.fill", "sla_horas": 24, "prioridad_base": "urgente", "orden": 4},
            {"nombre": "Barrera o señal caída", "icono": "xmark.seal.fill", "sla_horas": 48, "prioridad_base": "alta", "orden": 5},
        ]
    },
    {
        "nombre": "Señalización y Tránsito",
        "slug": "senalizacion",
        "descripcion": "Semáforos, señales de tránsito y demarcaciones",
        "icono": "light.traffic",
        "color_hex": "#E74C3C",
        "orden": 3,
        "departamento": "Dirección de Tránsito",
        "subcategorias": [
            {"nombre": "Semáforo dañado o apagado", "icono": "light.traffic", "sla_horas": 24, "prioridad_base": "urgente", "orden": 1},
            {"nombre": "Señal de tránsito faltante o dañada", "icono": "exclamationmark.triangle", "sla_horas": 48, "prioridad_base": "alta", "orden": 2},
            {"nombre": "Demarcación borrada (paso peatonal, etc.)", "icono": "line.diagonal", "sla_horas": 96, "prioridad_base": "normal", "orden": 3},
            {"nombre": "Semáforo peatonal sin funcionar", "icono": "figure.walk.motion", "sla_horas": 24, "prioridad_base": "urgente", "orden": 4},
        ]
    },
    {
        "nombre": "Alumbrado Público",
        "slug": "alumbrado",
        "descripcion": "Postes de luz, luminarias y cables en mal estado",
        "icono": "lightbulb.fill",
        "color_hex": "#F1C40F",
        "orden": 4,
        "departamento": "Dirección de Obras",
        "subcategorias": [
            {"nombre": "Luminaria apagada o intermitente", "icono": "lightbulb.slash.fill", "sla_horas": 48, "prioridad_base": "normal", "orden": 1},
            {"nombre": "Poste caído o inclinado", "icono": "bolt.fill", "sla_horas": 24, "prioridad_base": "urgente", "orden": 2},
            {"nombre": "Cables eléctricos colgando", "icono": "cable.connector", "sla_horas": 12, "prioridad_base": "urgente", "orden": 3},
            {"nombre": "Zona oscura sin alumbrado", "icono": "moon.fill", "sla_horas": 72, "prioridad_base": "alta", "orden": 4},
        ]
    },
    {
        "nombre": "Áreas Verdes y Plazas",
        "slug": "areas-verdes",
        "descripcion": "Parques, plazas, árboles y juegos infantiles",
        "icono": "tree.fill",
        "color_hex": "#27AE60",
        "orden": 5,
        "departamento": "Dirección de Parques y Jardines",
        "subcategorias": [
            {"nombre": "Árbol caído o peligroso", "icono": "tree.fill", "sla_horas": 24, "prioridad_base": "urgente", "orden": 1},
            {"nombre": "Juego infantil roto o peligroso", "icono": "figure.play", "sla_horas": 48, "prioridad_base": "alta", "orden": 2},
            {"nombre": "Plaza o parque en mal estado", "icono": "mappin.and.ellipse", "sla_horas": 96, "prioridad_base": "normal", "orden": 3},
            {"nombre": "Bancas o mobiliario urbano dañado", "icono": "chair.fill", "sla_horas": 72, "prioridad_base": "normal", "orden": 4},
            {"nombre": "Ramas sobre cables o vía pública", "icono": "scissors", "sla_horas": 48, "prioridad_base": "alta", "orden": 5},
        ]
    },
    {
        "nombre": "Infraestructura",
        "slug": "infraestructura",
        "descripcion": "Alcantarillado, agua potable y estructuras urbanas",
        "icono": "wrench.and.screwdriver.fill",
        "color_hex": "#8E44AD",
        "orden": 6,
        "departamento": "Dirección de Obras",
        "subcategorias": [
            {"nombre": "Alcantarilla rota o tapada", "icono": "arrow.down.to.line", "sla_horas": 48, "prioridad_base": "alta", "orden": 1},
            {"nombre": "Pérdida de agua potable en vía pública", "icono": "drop.fill", "sla_horas": 24, "prioridad_base": "urgente", "orden": 2},
            {"nombre": "Muro o estructura en riesgo de derrumbe", "icono": "building.2.fill", "sla_horas": 24, "prioridad_base": "urgente", "orden": 3},
            {"nombre": "Tapa de cámara inexistente o dañada", "icono": "circle.grid.cross.fill", "sla_horas": 48, "prioridad_base": "alta", "orden": 4},
            {"nombre": "Daño en canal o acequia", "icono": "water.waves.and.arrow.trianglehead.up", "sla_horas": 72, "prioridad_base": "normal", "orden": 5},
        ]
    },
]


def seed_capas(apps, schema_editor):
    DepartamentoMunicipal = apps.get_model('reportes', 'DepartamentoMunicipal')
    CapaUrbana = apps.get_model('reportes', 'CapaUrbana')
    SubcategoriaUrbana = apps.get_model('reportes', 'SubcategoriaUrbana')

    departamentos_cache = {}

    for capa_data in CAPAS_DATA:
        # Crear o recuperar departamento
        depto_nombre = capa_data["departamento"]
        if depto_nombre not in departamentos_cache:
            depto, _ = DepartamentoMunicipal.objects.get_or_create(
                nombre=depto_nombre,
                defaults={"activo": True}
            )
            departamentos_cache[depto_nombre] = depto
        departamento = departamentos_cache[depto_nombre]

        # Crear capa
        capa, _ = CapaUrbana.objects.get_or_create(
            slug=capa_data["slug"],
            defaults={
                "nombre": capa_data["nombre"],
                "descripcion": capa_data["descripcion"],
                "icono": capa_data["icono"],
                "color_hex": capa_data["color_hex"],
                "departamento": departamento,
                "activa": True,
                "orden": capa_data["orden"],
            }
        )

        # Crear subcategorías
        for sub_data in capa_data["subcategorias"]:
            SubcategoriaUrbana.objects.get_or_create(
                capa=capa,
                nombre=sub_data["nombre"],
                defaults={
                    "icono": sub_data["icono"],
                    "sla_horas": sub_data["sla_horas"],
                    "prioridad_base": sub_data["prioridad_base"],
                    "activa": True,
                    "orden": sub_data["orden"],
                }
            )


def unseed_capas(apps, schema_editor):
    CapaUrbana = apps.get_model('reportes', 'CapaUrbana')
    DepartamentoMunicipal = apps.get_model('reportes', 'DepartamentoMunicipal')
    CapaUrbana.objects.all().delete()
    DepartamentoMunicipal.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('reportes', '0014_add_capas_urbanas_311'),
    ]

    operations = [
        migrations.RunPython(seed_capas, unseed_capas),
    ]
