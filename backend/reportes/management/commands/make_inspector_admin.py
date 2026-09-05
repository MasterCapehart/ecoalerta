from django.core.management.base import BaseCommand
from reportes.models import Usuario


class Command(BaseCommand):
    help = 'Actualiza el usuario inspector a administrador'

    def handle(self, *args, **options):
        try:
            inspector = Usuario.objects.get(username='inspector')
            
            if inspector.tipo == 'admin':
                self.stdout.write(
                    self.style.WARNING('El usuario inspector ya es administrador')
                )
            else:
                inspector.tipo = 'admin'
                inspector.save()
                self.stdout.write(
                    self.style.SUCCESS('Usuario inspector actualizado a administrador exitosamente')
                )
        except Usuario.DoesNotExist:
            # Si no existe, crearlo como admin
            inspector = Usuario.objects.create_user(
                username='inspector',
                password='1234',
                tipo='admin',
                email='inspector@urbanalert.cl'
            )
            self.stdout.write(
                self.style.SUCCESS('Usuario inspector creado como administrador (usuario: inspector, password: 1234)')
            )
