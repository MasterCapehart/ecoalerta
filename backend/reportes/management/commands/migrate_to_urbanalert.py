"""
Comando para migrar la BD de EcoAlerta (microbasurales) a UrbanAlert (reportes ciudadanos generales).
Actualiza categorías, borra datos demo de basurales y genera datos demo realistas.
"""
import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.gis.geos import Point
from reportes.models import CategoriaResiduo, Usuario, Reporte, Tag


NUEVAS_CATEGORIAS = [
    {'nombre': 'Baches y Pavimento',    'descripcion': 'Hoyos, grietas o hundimientos en calles y veredas'},
    {'nombre': 'Iluminación',           'descripcion': 'Faroles apagados, cables caídos o postes dañados'},
    {'nombre': 'Residuos y Basurales',  'descripcion': 'Microbasurales, escombros o acumulación de basura'},
    {'nombre': 'Áreas Verdes',          'descripcion': 'Plazas descuidadas, poda pendiente o árboles peligrosos'},
    {'nombre': 'Semáforos y Señalética','descripcion': 'Semáforos sin luz, señales dañadas o faltantes'},
    {'nombre': 'Infraestructura',       'descripcion': 'Veredas rotas, tapas de alcantarilla, bancas dañadas'},
    {'nombre': 'Seguridad Vial',        'descripcion': 'Rayados, daños en mobiliario urbano o riesgo vial'},
    {'nombre': 'Otro',                  'descripcion': 'Otros problemas urbanos no categorizados'},
]

# Descripciones realistas por categoría
DESCRIPCIONES = {
    'Baches y Pavimento': [
        'Bache profundo en la calzada, dificulta el tránsito vehicular',
        'Grieta extensa en la acera impide el paso de sillas de ruedas',
        'Hundimiento en la calzada genera acumulación de agua',
        'Pavimento deteriorado pone en riesgo a motociclistas',
        'Bache en cruce peatonal sin señalización de advertencia',
    ],
    'Iluminación': [
        'Farol apagado desde hace semanas, sector muy oscuro de noche',
        'Cable eléctrico caído sobre la vereda, riesgo eléctrico',
        'Poste de luz inclinado, peligro de caída',
        'Tres postes seguidos sin funcionar, calle completamente oscura',
        'Luminaria parpadeando, puede causar accidentes',
    ],
    'Residuos y Basurales': [
        'Acumulación de escombros y basura en sitio eriazo',
        'Microbasural formado en esquina, genera malos olores',
        'Bolsas de basura abandonadas obstruyen la cuneta',
        'Muebles y electrodomésticos abandonados en la vía pública',
        'Contenedor de basura desbordado hace varios días',
    ],
    'Áreas Verdes': [
        'Árbol con ramas peligrosas sobre línea eléctrica',
        'Plaza sin mantención, pasto alto y sin barrer',
        'Juegos infantiles con partes rotas, peligro para niños',
        'Árbol caído bloquea paso peatonal',
        'Regadores de plaza rotos, desperdicio de agua',
    ],
    'Semáforos y Señalética': [
        'Semáforo peatonal sin funcionar en cruce escolar',
        'Señal de tránsito "Ceda el paso" caída',
        'Semáforo con luz verde permanente, riesgo de accidente',
        'Señalización de velocidad borrada, imperceptible',
        'Semáforo desincronizado genera congestión innecesaria',
    ],
    'Infraestructura': [
        'Tapa de alcantarilla rota, peligro de caída',
        'Banca de plaza destrozada, no puede usarse',
        'Vereda completamente levantada por raíces',
        'Rampa de acceso discapacitados bloqueada',
        'Escalera pública con peldaños rotos',
    ],
    'Seguridad Vial': [
        'Rayado vandalismo cubre señalización vial',
        'Espejo vial quebrado en curva peligrosa',
        'Delineadores viales robados en curva',
        'Refugio peatonal destruido',
        'Demarcación de paso cebra borrada completamente',
    ],
    'Otro': [
        'Ruido excesivo proveniente de obra sin horario permitido',
        'Inundación en calle por tapón en alcantarilla',
        'Perros callejeros agresivos en el sector',
        'Cámara de seguridad municipal sin funcionar',
        'Buzón postal destruido',
    ],
}

# Coordenadas realistas: La Serena, Chile (-29.9, -71.25)
BASE_LAT = -29.9027
BASE_LNG = -71.2520

# Calles ficticias pero verosímiles
CALLES = [
    'Av. Francisco de Aguirre', 'Calle Los Carrera', 'Av. El Santo',
    'Calle Balmaceda', 'Av. Juan de Dios Pení', 'Calle Cordovez',
    'Av. del Mar', 'Calle O\'Higgins', 'Pasaje Las Palmas',
    'Av. La Paz', 'Calle Cienfuegos', 'Av. Los Aromos',
    'Calle Prat', 'Av. Brasil', 'Calle Aldunate',
]


class Command(BaseCommand):
    help = 'Migra BD de EcoAlerta (basurales) a UrbanAlert (reportes ciudadanos generales)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--borrar-reportes-demo',
            action='store_true',
            help='Elimina los reportes demo anteriores de basurales',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Migración a UrbanAlert ===\n'))

        # 1. Actualizar/crear categorías nuevas
        self._migrar_categorias()

        # 2. Borrar reportes demo antiguos si se pide
        if options['borrar_reportes_demo']:
            self._borrar_reportes_demo()

        # 3. Crear tags útiles
        self._crear_tags()

        # 4. Generar reportes demo realistas
        self._generar_reportes_demo()

        self.stdout.write(self.style.SUCCESS('\n¡Migración completada exitosamente!\n'))

    def _migrar_categorias(self):
        self.stdout.write('→ Actualizando categorías...')

        # Nombres viejos de residuos que ya no aplican
        categorias_viejas = [
            'Residuos Domésticos', 'Escombros de Construcción',
            'Residuos Electrónicos', 'Residuos Orgánicos',
            'Residuos Peligrosos', 'Mixtos',
        ]

        # Obtener o crear categoría "Residuos y Basurales" primero (para reasignar reportes viejos)
        cat_residuos, _ = CategoriaResiduo.objects.get_or_create(
            nombre='Residuos y Basurales',
            defaults={'descripcion': 'Microbasurales, escombros o acumulación de basura'}
        )

        # Reasignar reportes de categorías viejas a "Residuos y Basurales"
        for nombre_viejo in categorias_viejas:
            try:
                cat_vieja = CategoriaResiduo.objects.get(nombre=nombre_viejo)
                n = Reporte.objects.filter(categoria=cat_vieja).update(categoria=cat_residuos)
                if n > 0:
                    self.stdout.write(f'  Reasignados {n} reportes de "{nombre_viejo}" → "Residuos y Basurales"')
                cat_vieja.delete()
                self.stdout.write(f'  Eliminada categoría: {nombre_viejo}')
            except CategoriaResiduo.DoesNotExist:
                pass

        # Crear todas las categorías nuevas
        for cat_data in NUEVAS_CATEGORIAS:
            _, created = CategoriaResiduo.objects.get_or_create(
                nombre=cat_data['nombre'],
                defaults={'descripcion': cat_data['descripcion']}
            )
            estado = self.style.SUCCESS('creada') if created else self.style.WARNING('ya existe')
            self.stdout.write(f'  Categoría "{cat_data["nombre"]}": {estado}')

    def _borrar_reportes_demo(self):
        self.stdout.write('→ Eliminando reportes demo anteriores...')
        n = Reporte.objects.filter(
            notas_internas__icontains='cargado automáticamente'
        ).delete()[0]
        n2 = Reporte.objects.filter(
            notas_internas__icontains='demo'
        ).delete()[0]
        self.stdout.write(f'  Eliminados {n + n2} reportes demo')

    def _crear_tags(self):
        self.stdout.write('→ Creando tags...')
        tags = [
            {'nombre': 'Urgente',        'color': '#ef4444'},
            {'nombre': 'Zona Escolar',   'color': '#f59e0b'},
            {'nombre': 'Zona Hospital',  'color': '#3b82f6'},
            {'nombre': 'Accesibilidad',  'color': '#8b5cf6'},
            {'nombre': 'Reincidente',    'color': '#ec4899'},
            {'nombre': 'Alto Tráfico',   'color': '#f97316'},
        ]
        for t in tags:
            _, created = Tag.objects.get_or_create(nombre=t['nombre'], defaults={'color': t['color']})
            if created:
                self.stdout.write(f'  Tag creado: {t["nombre"]}')

    def _generar_reportes_demo(self):
        self.stdout.write('→ Generando reportes demo realistas...')

        if Reporte.objects.filter(notas_internas__icontains='urbanalert-demo').exists():
            self.stdout.write(self.style.WARNING('  Ya existen reportes demo de UrbanAlert, se omite generación'))
            return

        inspector = Usuario.objects.filter(username='inspector').first()
        if not inspector:
            self.stdout.write(self.style.WARNING('  No se encontró usuario inspector, usando primer admin'))
            inspector = Usuario.objects.filter(tipo='admin').first()

        categorias = list(CategoriaResiduo.objects.all())
        if not categorias:
            self.stdout.write(self.style.ERROR('  Sin categorías, no se pueden crear reportes'))
            return

        estados_pesos = [
            ('nuevo',    0.35),
            ('proceso',  0.25),
            ('resuelto', 0.25),
            ('cerrado',  0.15),
        ]
        prioridades = ['baja', 'normal', 'alta', 'urgente']

        creados = 0
        for i in range(1, 41):
            categoria = random.choice(categorias)
            estado, _ = zip(*estados_pesos)
            pesos = [p for _, p in estados_pesos]
            estado_elegido = random.choices(list(estado), weights=pesos, k=1)[0]
            days_ago = random.randint(0, 60)
            created_at = timezone.now() - timedelta(days=days_ago)
            calle = random.choice(CALLES)
            numero = random.randint(100, 2500)

            descripciones_cat = DESCRIPCIONES.get(categoria.nombre, DESCRIPCIONES['Otro'])
            descripcion = random.choice(descripciones_cat)

            lat = BASE_LAT + random.uniform(-0.08, 0.08)
            lng = BASE_LNG + random.uniform(-0.08, 0.08)

            Reporte.objects.create(
                categoria=categoria,
                descripcion=descripcion,
                email=f'ciudadano{i}@demo.cl',
                ubicacion=Point(lng, lat, srid=4326),
                direccion=f'{calle} #{numero}',
                estado=estado_elegido,
                prioridad=random.choice(prioridades),
                notas_internas='urbanalert-demo',
                creado_por=inspector,
                asignado_a=inspector if estado_elegido in ('proceso', 'resuelto', 'cerrado') else None,
                fecha_creacion=created_at,
                fecha_actualizacion=created_at + timedelta(hours=random.randint(1, 72)),
            )
            creados += 1

        self.stdout.write(self.style.SUCCESS(f'  Creados {creados} reportes demo realistas'))
