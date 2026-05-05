from rest_framework import serializers
from django.contrib.auth.models import User
from .models import PerfilUsuario, Instalacion, Instructor, Reserva, ClaseHoy, ClaseCompartida, InscripcionClase


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilUsuario
        fields = '__all__'


class InstalacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instalacion
        fields = '__all__'


class InstructorSerializer(serializers.ModelSerializer):
    nombre = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    class Meta:
        model = Instructor
        fields = '__all__'

    def get_nombre(self, obj):
        return obj.usuario.get_full_name() or obj.usuario.username

    def get_email(self, obj):
        return obj.usuario.email


class ReservaSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.SerializerMethodField()
    instalacion_nombre = serializers.SerializerMethodField()
    instructor_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Reserva
        fields = '__all__'

    def get_cliente_nombre(self, obj):
        return obj.cliente.get_full_name() or obj.cliente.username

    def get_instalacion_nombre(self, obj):
        return obj.instalacion.nombre

    def get_instructor_nombre(self, obj):
        if obj.instructor:
            return obj.instructor.usuario.get_full_name() or obj.instructor.usuario.username
        return None


class ClaseHoySerializer(serializers.ModelSerializer):
    instructor_nombre = serializers.SerializerMethodField()
    instalacion_nombre = serializers.SerializerMethodField()

    class Meta:
        model = ClaseHoy
        fields = '__all__'

    def get_instructor_nombre(self, obj):
        return obj.instructor.usuario.get_full_name() or obj.instructor.usuario.username

    def get_instalacion_nombre(self, obj):
        return obj.instalacion.nombre


class ClaseCompartidaSerializer(serializers.ModelSerializer):
    instructor_nombre = serializers.SerializerMethodField()
    instalacion_nombre = serializers.SerializerMethodField()
    dia_nombre = serializers.SerializerMethodField()
    inscritos_count = serializers.SerializerMethodField()
    cupo_disponible = serializers.SerializerMethodField()

    class Meta:
        model = ClaseCompartida
        fields = '__all__'

    def get_instructor_nombre(self, obj):
        return obj.instructor.usuario.get_full_name() or obj.instructor.usuario.username

    def get_instalacion_nombre(self, obj):
        return obj.instalacion.nombre

    def get_dia_nombre(self, obj):
        return obj.get_dia_semana_display()

    def get_inscritos_count(self, obj):
        return obj.inscritos_count

    def get_cupo_disponible(self, obj):
        return obj.cupo_disponible


class InscripcionClaseSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.SerializerMethodField()
    clase_nombre = serializers.SerializerMethodField()

    class Meta:
        model = InscripcionClase
        fields = '__all__'

    def get_cliente_nombre(self, obj):
        return obj.cliente.get_full_name() or obj.cliente.username

    def get_clase_nombre(self, obj):
        return obj.clase.nombre
