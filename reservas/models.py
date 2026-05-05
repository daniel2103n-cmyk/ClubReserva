from django.db import models
from django.contrib.auth.models import User
import datetime

# ─────────────────────────────────────────────
# Reglas de negocio por especialidad
# ─────────────────────────────────────────────
REGLAS_ESPECIALIDAD = {
    'Tenis':    {'tipo_instalacion': 'Deportiva',  'cupo_max': 4,  'compartida': True,  'grupos_max': 1,  'tarifa_default': 25.00},
    'Pádel':    {'tipo_instalacion': 'Deportiva',  'cupo_max': 4,  'compartida': True,  'grupos_max': 1,  'tarifa_default': 25.00},
    'Natación': {'tipo_instalacion': 'Acuática',   'cupo_max': 10, 'compartida': True,  'grupos_max': 5,  'tarifa_default': 30.00},
    'Yoga':     {'tipo_instalacion': 'Relajación', 'cupo_max': 15, 'compartida': True,  'grupos_max': 1,  'tarifa_default': 15.00},
    'Fitness':  {'tipo_instalacion': 'Fitness',    'cupo_max': 1,  'compartida': False, 'grupos_max': 0,  'tarifa_default': 35.00},
    'Otro':     {'tipo_instalacion': None,         'cupo_max': 10, 'compartida': True,  'grupos_max': 1,  'tarifa_default': 20.00},
}

DESCUENTO_COMPARTIDA = 0.25  # 25% de descuento al precio base por ser clase compartida


class PerfilUsuario(models.Model):
    ROL_CHOICES = [
        ('cliente', 'Cliente'),
        ('instructor', 'Instructor'),
        ('admin', 'Admin'),
    ]
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='cliente')

    def __str__(self):
        return f"{self.usuario.get_full_name() or self.usuario.username} ({self.rol})"


class Instalacion(models.Model):
    TIPO_CHOICES = [
        ('Deportiva', 'Deportiva'),
        ('Acuática', 'Acuática'),
        ('Fitness', 'Fitness'),
        ('Relajación', 'Relajación'),
    ]
    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('mantenimiento', 'Mantenimiento'),
        ('inactiva', 'Inactiva'),
    ]
    nombre = models.CharField(max_length=150)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default='Deportiva')
    capacidad = models.PositiveIntegerField(default=4)
    descripcion = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activa')
    precio_hora = models.DecimalField(max_digits=8, decimal_places=2, default=30.00)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class Instructor(models.Model):
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('ocupado', 'Ocupado'),
        ('ausente', 'Ausente'),
    ]
    ESPECIALIDAD_CHOICES = [
        ('Tenis', 'Tenis'),
        ('Natación', 'Natación'),
        ('Yoga', 'Yoga'),
        ('Fitness', 'Fitness'),
        ('Pádel', 'Pádel'),
        ('Otro', 'Otro'),
    ]
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructor')
    especialidad = models.CharField(max_length=50, choices=ESPECIALIDAD_CHOICES, default='Tenis')
    calificacion_promedio = models.DecimalField(max_digits=3, decimal_places=1, default=5.0)
    total_resenas = models.PositiveIntegerField(default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='disponible')
    bio = models.TextField(blank=True)
    foto = models.ImageField(upload_to='instructores/', blank=True, null=True)
    tarifa_hora = models.DecimalField(max_digits=8, decimal_places=2, default=20.00)

    def __str__(self):
        return f"Instructor: {self.usuario.get_full_name() or self.usuario.username}"

    @property
    def tipo_instalacion_compatible(self):
        """Retorna el tipo de instalación compatible con la especialidad del instructor."""
        regla = REGLAS_ESPECIALIDAD.get(self.especialidad, {})
        return regla.get('tipo_instalacion')

    @property
    def permite_clases_compartidas(self):
        regla = REGLAS_ESPECIALIDAD.get(self.especialidad, {})
        return regla.get('compartida', False)


class Reserva(models.Model):
    ESTADO_CHOICES = [
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada'),
        ('pendiente', 'Pendiente'),
    ]
    cliente = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reservas_cliente'
    )
    instalacion = models.ForeignKey(
        Instalacion, on_delete=models.CASCADE, related_name='reservas'
    )
    instructor = models.ForeignKey(
        Instructor, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservas'
    )
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='confirmada')
    precio_total = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha', 'hora_inicio']

    def __str__(self):
        return f"{self.cliente.get_full_name()} - {self.instalacion.nombre} {self.fecha} {self.hora_inicio}"


class ClaseHoy(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_curso', 'En curso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]
    instructor = models.ForeignKey(
        Instructor, on_delete=models.CASCADE, related_name='clases'
    )
    instalacion = models.ForeignKey(
        Instalacion, on_delete=models.CASCADE, related_name='clases'
    )
    nombre_clase = models.CharField(max_length=150, default='Clase')
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    cupo_maximo = models.PositiveIntegerField(default=10)
    inscritos = models.PositiveIntegerField(default=0)
    nivel = models.CharField(max_length=50, default='Todos')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')

    class Meta:
        ordering = ['fecha', 'hora_inicio']

    def __str__(self):
        return f"{self.nombre_clase} - {self.instructor} - {self.fecha} {self.hora_inicio}"


# ─────────────────────────────────────────────
# Clases Compartidas Recurrentes
# ─────────────────────────────────────────────

class ClaseCompartida(models.Model):
    DIA_CHOICES = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    NIVEL_CHOICES = [
        ('Todos', 'Todos los niveles'),
        ('Básico', 'Básico'),
        ('Intermedio', 'Intermedio'),
        ('Avanzado', 'Avanzado'),
    ]

    nombre = models.CharField(max_length=150)
    instructor = models.ForeignKey(
        Instructor, on_delete=models.CASCADE, related_name='clases_compartidas'
    )
    instalacion = models.ForeignKey(
        Instalacion, on_delete=models.CASCADE, related_name='clases_compartidas'
    )
    dia_semana = models.IntegerField(choices=DIA_CHOICES)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    cupo_maximo = models.PositiveIntegerField(default=10)
    nivel = models.CharField(max_length=50, choices=NIVEL_CHOICES, default='Todos')
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)
    precio_persona = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['dia_semana', 'hora_inicio']
        verbose_name = 'Clase Compartida'
        verbose_name_plural = 'Clases Compartidas'

    def __str__(self):
        dia = dict(self.DIA_CHOICES).get(self.dia_semana, '')
        return f"{self.nombre} — {dia} {self.hora_inicio.strftime('%H:%M')}"

    @property
    def inscritos_count(self):
        return self.inscripciones.count()

    @property
    def cupo_disponible(self):
        return max(0, self.cupo_maximo - self.inscritos_count)

    @property
    def lleno(self):
        return self.cupo_disponible <= 0

    def calcular_precio(self):
        """Calcula el precio por persona con descuento de clase compartida."""
        hi = self.hora_inicio
        hf = self.hora_fin
        duracion_hrs = (hf.hour + hf.minute / 60) - (hi.hour + hi.minute / 60)
        if duracion_hrs <= 0:
            duracion_hrs = 1.0
        precio_base = float(self.instalacion.precio_hora + self.instructor.tarifa_hora) * duracion_hrs
        return round(precio_base * (1 - DESCUENTO_COMPARTIDA), 2)


class InscripcionClase(models.Model):
    cliente = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='inscripciones'
    )
    clase = models.ForeignKey(
        ClaseCompartida, on_delete=models.CASCADE, related_name='inscripciones'
    )
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cliente', 'clase')
        ordering = ['fecha_inscripcion']
        verbose_name = 'Inscripción'
        verbose_name_plural = 'Inscripciones'

    def __str__(self):
        return f"{self.cliente.get_full_name() or self.cliente.username} → {self.clase.nombre}"

class AlertaAdmin(models.Model):
    TIPO_CHOICES = [
        ('llegada_tarde', 'Llegada Tarde'),
        ('salida_temprana', 'Salida Temprana'),
        ('fallo_reconocimiento', 'Fallo de Reconocimiento Facial'),
    ]
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    mensaje = models.CharField(max_length=255)
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name='alertas')
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_hora']
        verbose_name = 'Alerta Administrativa'
        verbose_name_plural = 'Alertas Administrativas'

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.instructor.usuario.username}"
