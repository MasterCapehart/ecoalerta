import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from reportes.models import CategoriaResiduo, Usuario, Reporte


class Command(BaseCommand):
    help = 'Carga datos iniciales: categorías de residuos y usuario inspector'

    def handle(self, *args, **options):
        # Crear categorías de residuos
        categorias = [
            {'nombre': 'Baches y Pavimento', 'descripcion': 'Hoyos, grietas o hundimientos en calles y veredas'},
            {'nombre': 'Iluminación', 'descripcion': 'Faroles apagados, cables caídos o postes dañados'},
            {'nombre': 'Residuos y Basurales', 'descripcion': 'Microbasurales, escombros o acumulación de basura'},
            {'nombre': 'Áreas Verdes', 'descripcion': 'Plazas descuidadas, poda pendiente o árboles peligrosos'},
            {'nombre': 'Semáforos y Señalética', 'descripcion': 'Semáforos sin luz, señales dañadas o faltantes'},
            {'nombre': 'Infraestructura', 'descripcion': 'Veredas rotas, tapas de alcantarilla, bancas dañadas'},
            {'nombre': 'Seguridad Vial', 'descripcion': 'Rayados, daños en mobiliario urbano o riesgo vial'},
            {'nombre': 'Otro', 'descripcion': 'Otros problemas urbanos no categorizados'},
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

        # Crear o actualizar usuario inspector por defecto como administrador
        inspector, created = Usuario.objects.get_or_create(
            username='inspector',
            defaults={
                'password': '1234',
                'tipo': 'admin',
                'email': 'inspector@urbanalert.cl'
            }
        )
        
        if created:
            inspector.set_password('1234')
            inspector.save()
            self.stdout.write(
                self.style.SUCCESS('Usuario inspector creado como administrador (usuario: inspector, password: 1234)')
            )
        else:
            # Actualizar el usuario existente a administrador si no lo es
            if inspector.tipo != 'admin':
                inspector.tipo = 'admin'
                inspector.save()
                self.stdout.write(
                    self.style.SUCCESS('Usuario inspector actualizado a administrador')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('Usuario inspector ya existe y es administrador')
                )

        # Crear o actualizar usuario administrador con todos los permisos
        administrador, created = Usuario.objects.get_or_create(
            username='administrador',
            defaults={
                'password': '1234',
                'tipo': 'admin',
                'email': 'administrador@urbanalert.cl',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        if created:
            administrador.set_password('1234')
            administrador.is_staff = True
            administrador.is_superuser = True
            administrador.save()
            self.stdout.write(
                self.style.SUCCESS('Usuario administrador creado con todos los permisos (usuario: administrador, password: 1234)')
            )
        else:
            # Actualizar el usuario existente para asegurar que tenga todos los permisos
            if administrador.tipo != 'admin' or not administrador.is_staff or not administrador.is_superuser:
                administrador.tipo = 'admin'
                administrador.is_staff = True
                administrador.is_superuser = True
                administrador.save()
                self.stdout.write(
                    self.style.SUCCESS('Usuario administrador actualizado con todos los permisos')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('Usuario administrador ya existe con todos los permisos')
                )

        # Crear reportes de ejemplo solo si no existen
        if Reporte.objects.exists():
            self.stdout.write(
                self.style.WARNING('Ya existen reportes en la base, no se generaron datos demo.')
            )
        else:
            inspector = Usuario.objects.filter(username='inspector').first()
            categorias = list(CategoriaResiduo.objects.all())
            estados = ['nuevo', 'proceso', 'resuelto', 'cerrado']

            base_lat = -33.45
            base_lng = -70.66

            for idx in range(1, 31):
                categoria = random.choice(categorias)
                estado = random.choices(
                    estados,
                    weights=[0.35, 0.25, 0.25, 0.15],
                    k=1
                )[0]
                days_ago = random.randint(0, 45)
                created_at = timezone.now() - timedelta(days=days_ago)

                Reporte.objects.create(
                    categoria=categoria,
                    descripcion=f"Reporte demo #{idx} para {categoria.nombre.lower()}",
                    email=f"ciudadano{idx}@demo.cl",
                    ubicacion_lat=base_lat + random.uniform(-0.1, 0.1),
                    ubicacion_lng=base_lng + random.uniform(-0.1, 0.1),
                    direccion=f"Calle {idx} con Avenida {idx + 5}",
                    estado=estado,
                    notas_internas="Reporte cargado automáticamente para pruebas locales.",
                    creado_por=inspector,
                    asignado_a=inspector if estado in {'proceso', 'resuelto', 'cerrado'} else None,
                    fecha_creacion=created_at,
                    fecha_actualizacion=created_at + timedelta(hours=random.randint(1, 72)),
                )

            self.stdout.write(
                self.style.SUCCESS('Se generaron 30 reportes de ejemplo para entrenamiento.')
            )

        self.stdout.write(self.style.SUCCESS('\n¡Datos iniciales cargados exitosamente!'))

