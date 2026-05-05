"""
Script para crear datos de prueba en ClubReserva.
Ejecutar con: python manage.py shell < seed_data.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from reservas.models import PerfilUsuario, Instalacion, Instructor, Reserva, ClaseHoy, ClaseCompartida
import datetime

print("🌱 Creando datos de prueba...")

# ── Admin ──────────────────────────────────────────
admin_user, _ = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@clubreserva.com',
        'first_name': 'Alex',
        'last_name': 'Thompson',
        'is_staff': True,
        'is_superuser': True,
    }
)
admin_user.set_password('admin123')
admin_user.save()
PerfilUsuario.objects.get_or_create(usuario=admin_user, defaults={'rol': 'admin'})
print("  ✅ Admin: admin / admin123")

# ── Instructores ───────────────────────────────────
instructores_data = [
    {'username': 'marc.thompson', 'first_name': 'Marc', 'last_name': 'Thompson',
     'email': 'marc@clubreserva.com', 'especialidad': 'Tenis'},
    {'username': 'elena.rojas', 'first_name': 'Elena', 'last_name': 'Rojas',
     'email': 'elena@clubreserva.com', 'especialidad': 'Yoga'},
    {'username': 'carlos.mendoza', 'first_name': 'Carlos', 'last_name': 'Mendoza',
     'email': 'carlos.m@clubreserva.com', 'especialidad': 'Natación'},
]

instructores_objs = []
for data in instructores_data:
    esp = data.pop('especialidad')
    user, _ = User.objects.get_or_create(username=data['username'], defaults=data)
    user.set_password('inst123')
    user.save()
    PerfilUsuario.objects.get_or_create(usuario=user, defaults={'rol': 'instructor'})
    inst, _ = Instructor.objects.get_or_create(
        usuario=user,
        defaults={'especialidad': esp, 'calificacion_promedio': 4.9, 'estado': 'disponible'}
    )
    instructores_objs.append(inst)
    print(f"  ✅ Instructor: {data['username']} / inst123")

# ── Clientes ───────────────────────────────────────
clientes_data = [
    {'username': 'carlos.perez', 'first_name': 'Carlos', 'last_name': 'Pérez',
     'email': 'carlos.perez@email.com'},
    {'username': 'ana.silva', 'first_name': 'Ana', 'last_name': 'Silva',
     'email': 'ana.silva@email.com'},
    {'username': 'luis.ocampo', 'first_name': 'Luis', 'last_name': 'Ocampo',
     'email': 'l.ocampo@email.com'},
]

clientes_objs = []
for data in clientes_data:
    user, _ = User.objects.get_or_create(username=data['username'], defaults=data)
    user.set_password('cli123')
    user.save()
    PerfilUsuario.objects.get_or_create(usuario=user, defaults={'rol': 'cliente'})
    clientes_objs.append(user)
    print(f"  ✅ Cliente: {data['username']} / cli123")

# ── Instalaciones ──────────────────────────────────
instalaciones_data = [
    {'nombre': 'Cancha de Tenis #1', 'tipo': 'Deportiva', 'capacidad': 4,
     'descripcion': 'Superficie de arcilla profesional, iluminación LED.', 'precio_hora': 30},
    {'nombre': 'Cancha de Tenis #2', 'tipo': 'Deportiva', 'capacidad': 4,
     'descripcion': 'Superficie rápida, ideal para partidos de alta velocidad.', 'precio_hora': 30},
    {'nombre': 'Piscina Olímpica', 'tipo': 'Acuática', 'capacidad': 50,
     'descripcion': 'Piscina climatizada 50m, 8 carriles.', 'precio_hora': 25,
     'estado': 'mantenimiento'},
    {'nombre': 'Gimnasio Central', 'tipo': 'Fitness', 'capacidad': 30,
     'descripcion': 'Equipos de última generación, zona cardio y pesas.', 'precio_hora': 20},
    {'nombre': 'Sala de Yoga', 'tipo': 'Relajación', 'capacidad': 15,
     'descripcion': 'Ambiente zen, piso de bambú y espejos.', 'precio_hora': 18},
    {'nombre': 'Cancha Fútbol 5', 'tipo': 'Deportiva', 'capacidad': 10,
     'descripcion': 'Césped sintético de alta calidad.', 'precio_hora': 40},
]

inst_objs = []
for data in instalaciones_data:
    estado = data.pop('estado', 'activa')
    inst, _ = Instalacion.objects.get_or_create(nombre=data['nombre'], defaults={**data, 'estado': estado})
    inst_objs.append(inst)
    print(f"  ✅ Instalación: {inst.nombre}")

# ── Reservas ───────────────────────────────────────
hoy = datetime.date.today()
manana = hoy + datetime.timedelta(days=1)
ayer = hoy - datetime.timedelta(days=2)

reservas_data = [
    {'cliente': clientes_objs[0], 'instalacion': inst_objs[0],
     'instructor': instructores_objs[0], 'fecha': manana,
     'hora_inicio': '10:00', 'hora_fin': '11:30', 'estado': 'confirmada', 'precio_total': 45},
    {'cliente': clientes_objs[0], 'instalacion': inst_objs[2],
     'instructor': None, 'fecha': manana + datetime.timedelta(days=2),
     'hora_inicio': '08:00', 'hora_fin': '09:00', 'estado': 'confirmada', 'precio_total': 25},
    {'cliente': clientes_objs[0], 'instalacion': inst_objs[1],
     'instructor': instructores_objs[0], 'fecha': ayer,
     'hora_inicio': '09:00', 'hora_fin': '10:30', 'estado': 'completada', 'precio_total': 45},
    {'cliente': clientes_objs[1], 'instalacion': inst_objs[3],
     'instructor': None, 'fecha': hoy,
     'hora_inicio': '17:00', 'hora_fin': '18:00', 'estado': 'confirmada', 'precio_total': 20},
]

for data in reservas_data:
    Reserva.objects.get_or_create(
        cliente=data['cliente'], instalacion=data['instalacion'],
        fecha=data['fecha'], hora_inicio=data['hora_inicio'],
        defaults=data
    )
print(f"  ✅ Reservas de prueba creadas")

# ── Clases del día ─────────────────────────────────
clases_data = [
    {'instructor': instructores_objs[0], 'instalacion': inst_objs[0],
     'nombre_clase': 'Entrenamiento de Tenis Pro', 'fecha': hoy,
     'hora_inicio': '09:00', 'hora_fin': '10:30', 'cupo_maximo': 15,
     'inscritos': 12, 'nivel': 'Avanzado', 'estado': 'en_curso'},
    {'instructor': instructores_objs[0], 'instalacion': inst_objs[1],
     'nombre_clase': 'Tenis Iniciación', 'fecha': hoy,
     'hora_inicio': '11:00', 'hora_fin': '12:00', 'cupo_maximo': 10,
     'inscritos': 8, 'nivel': 'Básico', 'estado': 'pendiente'},
    {'instructor': instructores_objs[1], 'instalacion': inst_objs[4],
     'nombre_clase': 'Yoga Matinal', 'fecha': hoy,
     'hora_inicio': '07:30', 'hora_fin': '08:30', 'cupo_maximo': 12,
     'inscritos': 10, 'nivel': 'Todos', 'estado': 'completada'},
]

for data in clases_data:
    ClaseHoy.objects.get_or_create(
        instructor=data['instructor'], fecha=data['fecha'],
        hora_inicio=data['hora_inicio'],
        defaults=data
    )
print(f"  ✅ Clases del día creadas")

# ── Clases Compartidas ─────────────────────────────
clases_comp_data = [
    {
        'nombre': 'Tenis Masterclass',
        'instructor': instructores_objs[0], # Marc (Tenis)
        'instalacion': inst_objs[0], # Cancha de Tenis #1
        'dia_semana': 1, # Martes
        'hora_inicio': datetime.time(16, 0),
        'hora_fin': datetime.time(17, 30),
        'cupo_maximo': 4,
        'nivel': 'Avanzado',
        'descripcion': 'Clase grupal para perfeccionar técnica y estrategia en cancha de arcilla.'
    },
    {
        'nombre': 'Yoga Relax',
        'instructor': instructores_objs[1], # Elena (Yoga)
        'instalacion': inst_objs[4], # Sala de Yoga
        'dia_semana': 3, # Jueves
        'hora_inicio': datetime.time(8, 0),
        'hora_fin': datetime.time(9, 0),
        'cupo_maximo': 15,
        'nivel': 'Todos',
        'descripcion': 'Sesión para conectar cuerpo y mente, enfocada en respiración y estiramiento.'
    },
    {
        'nombre': 'Natación Infantil (Grupo A)',
        'instructor': instructores_objs[2], # Carlos (Natación)
        'instalacion': inst_objs[2], # Piscina Olímpica
        'dia_semana': 5, # Sábado
        'hora_inicio': datetime.time(10, 0),
        'hora_fin': datetime.time(11, 0),
        'cupo_maximo': 10,
        'nivel': 'Básico',
        'descripcion': 'Iniciación a la natación para niños.'
    },
    {
        'nombre': 'Natación Infantil (Grupo B)', # Prueba de multi-grupo simultáneo
        'instructor': instructores_objs[2], # Carlos (Natación)
        'instalacion': inst_objs[2], # Piscina Olímpica
        'dia_semana': 5, # Sábado
        'hora_inicio': datetime.time(10, 0),
        'hora_fin': datetime.time(11, 0),
        'cupo_maximo': 10,
        'nivel': 'Intermedio',
        'descripcion': 'Perfeccionamiento de estilos para niños más avanzados.'
    }
]

for data in clases_comp_data:
    clase, created = ClaseCompartida.objects.get_or_create(
        nombre=data['nombre'],
        instructor=data['instructor'],
        dia_semana=data['dia_semana'],
        hora_inicio=data['hora_inicio'],
        defaults=data
    )
    if created:
        clase.precio_persona = clase.calcular_precio()
        clase.save()
print("  ✅ Clases Compartidas predefinidas creadas")

print("\n🎉 ¡Datos de prueba creados exitosamente!")
print("\n📋 Credenciales:")
print("   Admin:      admin / admin123         → /admin-panel/dashboard/")
print("   Instructor: marc.thompson / inst123  → /instructor/dashboard/")
print("   Cliente:    carlos.perez / cli123    → /cliente/dashboard/")
