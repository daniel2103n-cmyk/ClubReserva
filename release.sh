#!/bin/bash

# Aplicar migraciones
echo "Ejecutando migraciones..."
python manage.py migrate --noinput

# Recolectar archivos estáticos
echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# Crear superusuario si las variables existen y no existe ya
echo "Creando superusuario..."
python manage.py shell -c "
from django.contrib.auth.models import User
import os

u = os.environ.get('DJANGO_SUPERUSER_USERNAME')
e = os.environ.get('DJANGO_SUPERUSER_EMAIL')
p = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if u and p:
    if not User.objects.filter(username=u).exists():
        user = User.objects.create_superuser(u, e or 'admin@ejemplo.com', p)
        print(f'Superusuario {u} creado exitosamente.')
    else:
        print(f'El superusuario {u} ya existe.')
        
    # Asegurarse de que TODOS los superusuarios tengan el PerfilUsuario de admin
    # (Esto previene el error de 'too many redirects' al iniciar sesión)
    from reservas.models import PerfilUsuario
    for su in User.objects.filter(is_superuser=True):
        PerfilUsuario.objects.get_or_create(usuario=su, defaults={'rol': 'admin'})
    print('Verificación de perfiles de administrador completada.')
else:
    print('Faltan variables DJANGO_SUPERUSER_USERNAME o DJANGO_SUPERUSER_PASSWORD, se omite creación.')
"

# Iniciar el servidor
echo "Iniciando Gunicorn..."
exec gunicorn core.wsgi:application --bind 0.0.0.0:$PORT
