from django.core.management.base import BaseCommand
from reportes.models import CategoriaResiduo, Usuario


class Command(BaseCommand):
    help = 'Carga datos iniciales: categorías de residuos y usuario inspector'

    def handle(self, *args, **options):
        # Crear categorías de residuos
        categorias = [
            {'nombre': 'Residuos Domésticos', 'descripcion': 'Basura doméstica común'},
            {'nombre': 'Escombros de Construcción', 'descripcion': 'Materiales de construcción'},
            {'nombre': 'Residuos Electrónicos', 'descripcion': 'Equipos electrónicos desechados'},
            {'nombre': 'Residuos Orgánicos', 'descripcion': 'Desechos orgánicos biodegradables'},
            {'nombre': 'Residuos Peligrosos', 'descripcion': 'Materiales tóxicos o peligrosos'},
            {'nombre': 'Mixtos', 'descripcion': 'Mezcla de diferentes tipos de residuos'},
        ]

        for cat_data in categorias:
            categoria, created = CategoriaResiduo.objects.get_or_create(
                nombre=cat_data['nombre'],
                defaults={'descripcion': cat_data['descripcion']}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Categoría creada: {categoria.nombre}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Categoría ya existe: {categoria.nombre}')
                )

        # Crear usuario inspector por defecto
        if not Usuario.objects.filter(username='inspector').exists():
            inspector = Usuario.objects.create_user(
                username='inspector',
                password='1234',
                tipo='inspector',
                email='inspector@ecoalerta.cl'
            )
            self.stdout.write(
                self.style.SUCCESS('Usuario inspector creado (usuario: inspector, password: 1234)')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Usuario inspector ya existe')
            )

        self.stdout.write(
            self.style.SUCCESS('\n¡Datos iniciales cargados exitosamente!')
        )

