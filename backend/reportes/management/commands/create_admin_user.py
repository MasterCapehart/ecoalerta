from django.core.management.base import BaseCommand
from reportes.models import Usuario


class Command(BaseCommand):
    help = 'Crea o actualiza el usuario administrador con todos los permisos'

    def handle(self, *args, **options):
        try:
            administrador = Usuario.objects.get(username='administrador')
            
            # Verificar si ya tiene todos los permisos
            if administrador.tipo == 'admin' and administrador.is_staff and administrador.is_superuser:
                self.stdout.write(
                    self.style.WARNING('El usuario administrador ya existe con todos los permisos')
                )
            else:
                # Actualizar permisos
                administrador.tipo = 'admin'
                administrador.is_staff = True
                administrador.is_superuser = True
                administrador.set_password('1234')
                administrador.save()
                self.stdout.write(
                    self.style.SUCCESS('Usuario administrador actualizado con todos los permisos exitosamente')
                )
        except Usuario.DoesNotExist:
            # Si no existe, crearlo con todos los permisos
            administrador = Usuario.objects.create_user(
                username='administrador',
                password='1234',
                tipo='admin',
                email='administrador@ecoalerta.cl',
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(
                self.style.SUCCESS('Usuario administrador creado con todos los permisos (usuario: administrador, password: 1234)')
            )
