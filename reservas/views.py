from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q, Sum
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework import viewsets
from .models import (
    PerfilUsuario, Instalacion, Instructor, Reserva, ClaseHoy,
    ClaseCompartida, InscripcionClase, REGLAS_ESPECIALIDAD, AlertaAdmin
)
from .serializers import (
    InstalacionSerializer, InstructorSerializer,
    ReservaSerializer, ClaseHoySerializer,
    ClaseCompartidaSerializer, InscripcionClaseSerializer
)
import datetime
import json
from django.http import JsonResponse

# ─────────────────────────────────────────────
# Mixin para control de roles
# ─────────────────────────────────────────────
class RolRequeridoMixin:
    rol_requerido = None  # 'cliente' | 'instructor' | 'admin'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        perfil = getattr(request.user, 'perfil', None)
        if not perfil or (self.rol_requerido and perfil.rol != self.rol_requerido):
            messages.error(request, 'No tienes permiso para acceder a esta sección.')
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)


# ─────────────────────────────────────────────
# Autenticación
# ─────────────────────────────────────────────
class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return _redirigir_por_rol(request.user)
        return render(request, 'auth/login.html')

    def post(self, request):
        input_val = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        user = None
        user_obj_found = None

        # Intentar autenticar directamente con lo que ingresó
        user = authenticate(request, username=input_val, password=password)
        if not user:
            try:
                user_obj_found = User.objects.get(username=input_val)
            except User.DoesNotExist:
                pass

        # Si falla, intentar buscar si es un correo electrónico
        if not user and '@' in input_val:
            try:
                user_obj_found = User.objects.get(email=input_val)
                user = authenticate(request, username=user_obj_found.username, password=password)
            except User.DoesNotExist:
                pass
            except User.MultipleObjectsReturned:
                user_obj_found = User.objects.filter(email=input_val).first()
                user = authenticate(request, username=user_obj_found.username, password=password)

        if user:
            login(request, user)
            return _redirigir_por_rol(user)
            
        if user_obj_found and not user_obj_found.is_active:
            messages.error(request, 'Tu cuenta ha sido inhabilitada. Contacta al administrador.')
        else:
            messages.error(request, 'Usuario/Correo o contraseña incorrectos.')
            
        return render(request, 'auth/login.html', {'error': True})


class RegistroView(View):
    def get(self, request):
        return render(request, 'auth/registro.html')

    def post(self, request):
        nombre = request.POST.get('nombre', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        confirm = request.POST.get('confirm', '').strip()

        if password != confirm:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'auth/registro.html', {'error': True})

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Ya existe una cuenta con ese correo.')
            return render(request, 'auth/registro.html', {'error': True})

        username = email.split('@')[0]
        # Asegurar username único
        base = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{counter}"
            counter += 1

        partes = nombre.split(' ', 1)
        first = partes[0]
        last = partes[1] if len(partes) > 1 else ''

        user = User.objects.create_user(
            username=username, email=email, password=password,
            first_name=first, last_name=last
        )
        PerfilUsuario.objects.create(usuario=user, rol='cliente')
        login(request, user)
        return redirect('cliente_dashboard')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


def _redirigir_por_rol(user):
    perfil = getattr(user, 'perfil', None)
    if perfil:
        if perfil.rol == 'admin':
            return redirect('admin_dashboard')
        elif perfil.rol == 'instructor':
            return redirect('instructor_dashboard')
    return redirect('cliente_dashboard')


# ─────────────────────────────────────────────
# Vistas de Cliente
# ─────────────────────────────────────────────
@method_decorator(login_required, name='dispatch')
class ClienteDashboardView(RolRequeridoMixin, View):
    rol_requerido = 'cliente'

    def get(self, request):
        hoy = timezone.now().date()
        proximas = Reserva.objects.filter(
            cliente=request.user,
            fecha__gte=hoy,
            estado='confirmada'
        ).select_related('instalacion', 'instructor__usuario')[:5]

        recientes = Reserva.objects.filter(
            cliente=request.user,
            fecha__lt=hoy
        ).select_related('instalacion', 'instructor__usuario').order_by('-fecha')[:5]

        mes_actual = hoy.month
        reservas_mes = Reserva.objects.filter(
            cliente=request.user,
            fecha__month=mes_actual
        ).count()

        proxima = proximas.first()

        hoy = timezone.now().date()
        dia_semana_hoy = hoy.weekday()  # 0=Lunes
        mis_clases = InscripcionClase.objects.filter(
            cliente=request.user,
            clase__activa=True
        ).select_related('clase__instructor__usuario', 'clase__instalacion').order_by('clase__dia_semana', 'clase__hora_inicio')

        context = {
            'proximas': proximas,
            'recientes': recientes,
            'reservas_mes': reservas_mes,
            'proxima': proxima,
            'mis_clases': mis_clases,
            'usuario': request.user,
        }
        return render(request, 'cliente/dashboard.html', context)


@method_decorator(login_required, name='dispatch')
class HacerReservaView(RolRequeridoMixin, View):
    rol_requerido = 'cliente'

    def get(self, request):
        instalaciones = Instalacion.objects.filter(estado='activa')
        instructores = Instructor.objects.filter(
            estado='disponible'
        ).select_related('usuario')
        context = {
            'instalaciones': instalaciones,
            'instructores': instructores,
            'usuario': request.user,
        }
        return render(request, 'cliente/reserva.html', context)

    def post(self, request):
        instalacion_id = request.POST.get('instalacion')
        instructor_id = request.POST.get('instructor')
        fecha = request.POST.get('fecha')
        hora_inicio = request.POST.get('hora_inicio')
        hora_fin = request.POST.get('hora_fin')

        try:
            import datetime
            from django.utils import timezone
            
            fecha_obj = datetime.datetime.strptime(fecha, '%Y-%m-%d').date()
            hi_obj = datetime.datetime.strptime(hora_inicio, '%H:%M').time()
            hf_obj = datetime.datetime.strptime(hora_fin, '%H:%M').time()
            hoy = timezone.now().date()
            
            if fecha_obj < hoy:
                messages.error(request, 'No puedes hacer reservas en días pasados.')
                return redirect('hacer_reserva')
            
            if fecha_obj > hoy + datetime.timedelta(days=30):
                messages.error(request, 'Solo puedes reservar con un máximo de 1 mes (30 días) de anticipación.')
                return redirect('hacer_reserva')
                
            if hi_obj < datetime.time(8, 0) or hf_obj > datetime.time(19, 0):
                messages.error(request, 'El horario operativo es de 08:00 a 19:00.')
                return redirect('hacer_reserva')
                
            if hi_obj >= hf_obj:
                messages.error(request, 'La hora de inicio debe ser anterior a la hora de fin.')
                return redirect('hacer_reserva')
                
            duracion_hrs = (hf_obj.hour + hf_obj.minute / 60.0) - (hi_obj.hour + hi_obj.minute / 60.0)
            if duracion_hrs < 1.0:
                messages.error(request, 'La reserva debe durar al menos 1 hora.')
                return redirect('hacer_reserva')
            if duracion_hrs > 2.0:
                messages.error(request, 'La reserva no puede durar más de 2 horas.')
                return redirect('hacer_reserva')

            instalacion = Instalacion.objects.get(id=instalacion_id, estado='activa')
            instructor = None
            if instructor_id:
                instructor = Instructor.objects.get(id=instructor_id, estado='disponible')

            # Solapamientos con otras Reservas Privadas
            solapamientos_reserva = Reserva.objects.filter(
                fecha=fecha_obj,
                hora_inicio__lt=hf_obj,
                hora_fin__gt=hi_obj,
                estado__in=['confirmada', 'completada', 'en_curso']
            )
            if solapamientos_reserva.filter(instalacion=instalacion).exists():
                messages.error(request, 'La instalación ya está ocupada en ese horario por otra reserva.')
                return redirect('hacer_reserva')
            if instructor and solapamientos_reserva.filter(instructor=instructor).exists():
                messages.error(request, 'El instructor seleccionado ya tiene una clase privada en ese horario.')
                return redirect('hacer_reserva')

            # Solapamientos con Clases Compartidas
            from reservas.models import ClaseCompartida
            solapamientos_clases = ClaseCompartida.objects.filter(
                dia_semana=fecha_obj.weekday(),
                hora_inicio__lt=hf_obj,
                hora_fin__gt=hi_obj,
                activa=True
            )
            if solapamientos_clases.filter(instalacion=instalacion).exists():
                messages.error(request, 'La instalación está reservada para una Clase Compartida fundamental en ese horario.')
                return redirect('hacer_reserva')
            if instructor and solapamientos_clases.filter(instructor=instructor).exists():
                messages.error(request, 'El instructor se encuentra impartiendo una Clase Compartida fundamental en ese horario.')
                return redirect('hacer_reserva')

            precio_final = float(instalacion.precio_hora) * duracion_hrs
            if instructor:
                precio_final += float(instructor.tarifa_hora) * duracion_hrs

            reserva = Reserva.objects.create(
                cliente=request.user,
                instalacion=instalacion,
                instructor=instructor,
                fecha=fecha_obj,
                hora_inicio=hi_obj,
                hora_fin=hf_obj,
                estado='confirmada',
                precio_total=precio_final
            )
            messages.success(request, '¡Reserva confirmada exitosamente!')
            return redirect('cliente_dashboard')
        except ValueError:
            messages.error(request, 'Error en el formato de la fecha o las horas proporcionadas.')
            return redirect('hacer_reserva')
        except Exception as e:
            messages.error(request, f'Error al crear la reserva: {str(e)}')
            return redirect('hacer_reserva')


# ─────────────────────────────────────────────
# Vistas de Instructor
# ─────────────────────────────────────────────
@method_decorator(login_required, name='dispatch')
class InstructorDashboardView(RolRequeridoMixin, View):
    rol_requerido = 'instructor'

    def get(self, request):
        instructor = getattr(request.user, 'instructor', None)
        if not instructor:
            messages.error(request, 'Perfil de instructor no encontrado.')
            return redirect('login')

        hoy = timezone.now().date()
        clases_hoy = list(ClaseHoy.objects.filter(
            instructor=instructor, fecha=hoy
        ).select_related('instalacion'))

        reservas_hoy = list(Reserva.objects.filter(
            instructor=instructor, fecha=hoy
        ).select_related('instalacion', 'cliente'))

        sesiones = []
        for c in clases_hoy:
            sesiones.append({
                'id': c.id,
                'tipo': 'Grupal',
                'nombre': c.nombre_clase,
                'hora_inicio': c.hora_inicio,
                'hora_fin': c.hora_fin,
                'instalacion': c.instalacion.nombre,
                'alumnos': f"{c.inscritos}/{c.cupo_maximo}",
                'nivel': c.nivel,
                'estado': c.estado,
            })
        for r in reservas_hoy:
            sesiones.append({
                'id': r.id,
                'tipo': 'Privada',
                'nombre': f"Clase Privada ({r.cliente.get_full_name() or r.cliente.username})",
                'hora_inicio': r.hora_inicio,
                'hora_fin': r.hora_fin,
                'instalacion': r.instalacion.nombre,
                'alumnos': "1/1",
                'nivel': "Personalizado",
                'estado': 'pendiente' if r.estado == 'confirmada' else r.estado,
            })
            
        sesiones.sort(key=lambda x: x['hora_inicio'])

        proxima_sesion = next((s for s in sesiones if s['estado'] in ['pendiente', 'confirmada']), None)

        mes_actual = hoy.month
        clases_mes = ClaseHoy.objects.filter(instructor=instructor, fecha__month=mes_actual, estado='completada').count()
        reservas_mes = Reserva.objects.filter(instructor=instructor, fecha__month=mes_actual, estado='completada').count()
        total_sesiones_mes = clases_mes + reservas_mes
        horas_mes = total_sesiones_mes * 1.5

        context = {
            'instructor': instructor,
            'sesiones': sesiones,
            'proxima_sesion': proxima_sesion,
            'horas_mes': int(horas_mes),
            'usuario': request.user,
        }
        return render(request, 'profesor/dashboard.html', context)


@method_decorator(login_required, name='dispatch')
class InstructorCalendarioView(RolRequeridoMixin, View):
    rol_requerido = 'instructor'

    def get(self, request):
        instructor = getattr(request.user, 'instructor', None)
        if not instructor:
            messages.error(request, 'Perfil de instructor no encontrado.')
            return redirect('login')

        hoy = timezone.now().date()
        fecha_str = request.GET.get('fecha')
        if fecha_str:
            try:
                fecha_base = datetime.datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                fecha_base = hoy
        else:
            fecha_base = hoy

        # Semana actual (Lunes a Domingo)
        lunes = fecha_base - datetime.timedelta(days=fecha_base.weekday())
        semana = [lunes + datetime.timedelta(days=i) for i in range(7)]
        
        semana_anterior = (lunes - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        semana_siguiente = (lunes + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        hoy_str = hoy.strftime('%Y-%m-%d')

        clases_semana = ClaseHoy.objects.filter(
            instructor=instructor,
            fecha__gte=lunes,
            fecha__lt=lunes + datetime.timedelta(days=7)
        ).select_related('instalacion')

        reservas_semana = Reserva.objects.filter(
            instructor=instructor,
            fecha__gte=lunes,
            fecha__lt=lunes + datetime.timedelta(days=7)
        ).select_related('instalacion', 'cliente')

        sesiones = []
        for c in clases_semana:
            sesiones.append({
                'tipo': 'Grupal',
                'nombre': c.nombre_clase,
                'fecha': c.fecha,
                'hora_inicio': c.hora_inicio,
                'hora_fin': c.hora_fin,
                'instalacion': c.instalacion.nombre,
                'estado': c.estado,
            })
        for r in reservas_semana:
            sesiones.append({
                'tipo': 'Privada',
                'nombre': f"Clase Privada ({r.cliente.get_full_name() or r.cliente.username})",
                'fecha': r.fecha,
                'hora_inicio': r.hora_inicio,
                'hora_fin': r.hora_fin,
                'instalacion': r.instalacion.nombre,
                'estado': 'pendiente' if r.estado == 'confirmada' else r.estado,
            })

        # Organizar por día
        sesiones_por_dia = {}
        for dia in semana:
            dia_sesiones = [s for s in sesiones if s['fecha'] == dia]
            dia_sesiones.sort(key=lambda x: x['hora_inicio'])
            sesiones_por_dia[dia] = dia_sesiones

        context = {
            'instructor': instructor,
            'semana': semana,
            'sesiones_por_dia': sesiones_por_dia,
            'usuario': request.user,
            'hoy': hoy,
            'fecha_base': fecha_base,
            'semana_anterior': semana_anterior,
            'semana_siguiente': semana_siguiente,
            'hoy_str': hoy_str,
        }
        return render(request, 'profesor/calendario.html', context)


# ─────────────────────────────────────────────
# Vistas de Admin
# ─────────────────────────────────────────────
@method_decorator(login_required, name='dispatch')
class AdminDashboardView(RolRequeridoMixin, View):
    rol_requerido = 'admin'

    def get(self, request):
        hoy = timezone.now().date()

        # Permitir filtrar por fecha desde ?fecha=YYYY-MM-DD
        fecha_param = request.GET.get('fecha')
        if fecha_param:
            try:
                fecha_vista = datetime.date.fromisoformat(fecha_param)
            except ValueError:
                fecha_vista = hoy
        else:
            fecha_vista = hoy

        # ── KPI Cards ──────────────────────────────
        reservas_hoy = Reserva.objects.filter(fecha=fecha_vista).count()

        instalaciones_activas = Instalacion.objects.filter(estado='activa')
        total_instalaciones = instalaciones_activas.count()
        reservas_confirmadas = Reserva.objects.filter(
            fecha=fecha_vista, estado='confirmada'
        ).count()
        ocupacion = round((reservas_confirmadas / max(total_instalaciones * 12, 1)) * 100)

        instructores_activos = Instructor.objects.filter(
            Q(estado='disponible') | Q(estado='ocupado')
        ).count()
        instructores_en_sesion = Instructor.objects.filter(estado='ocupado').count()

        total_clientes = PerfilUsuario.objects.filter(rol='cliente').count()

        # ── Calendario de reservas ──────────────────
        horas = list(range(8, 20))

        reservas_dia = list(Reserva.objects.filter(
            fecha=fecha_vista
        ).select_related('cliente', 'instalacion', 'instructor__usuario'))
        
        # Obtener clases compartidas para este día de la semana
        from reservas.models import ClaseCompartida
        clases_dia = list(ClaseCompartida.objects.filter(
            dia_semana=fecha_vista.weekday(), activa=True
        ).select_related('instructor__usuario', 'instalacion'))

        ESTADO_COLORES = {
            'confirmada': 'bg-emerald-600',
            'completada': 'bg-blue-600',
            'cancelada':  'bg-red-500',
            'pendiente':  'bg-amber-500',
        }

        calendario_rows = []
        for inst in Instalacion.objects.all().order_by('id'):
            slots = []
            for hora in horas:
                hora_time = datetime.time(hora, 0)
                reserva = None
                clases_en_hora = []
                for r in reservas_dia:
                    if r.instalacion_id == inst.id and r.hora_inicio <= hora_time < r.hora_fin:
                        reserva = r
                        break
                for c in clases_dia:
                    if c.instalacion_id == inst.id and c.hora_inicio <= hora_time < c.hora_fin:
                        clases_en_hora.append(c)

                slots.append({
                    'hora': hora,
                    'reserva': reserva,
                    'clases_compartidas': clases_en_hora,
                    'color': ESTADO_COLORES.get(reserva.estado, 'bg-slate-400') if reserva else None,
                })
            calendario_rows.append({'instalacion': inst, 'slots': slots})

        # ── Historial de reservas ───────────────────
        historial = Reserva.objects.select_related(
            'cliente', 'instalacion', 'instructor__usuario'
        ).order_by('-creado_en')[:15]

        ESTADO_BADGE = {
            'confirmada': ('bg-emerald-100 text-emerald-700', 'Confirmada'),
            'completada': ('bg-blue-100 text-blue-700', 'Completada'),
            'cancelada':  ('bg-red-100 text-red-700', 'Cancelada'),
            'pendiente':  ('bg-amber-100 text-amber-700', 'Pendiente'),
        }
        historial_data = []
        for r in historial:
            badge_cls, badge_label = ESTADO_BADGE.get(r.estado, ('bg-slate-100 text-slate-600', r.estado))
            historial_data.append({
                'reserva': r,
                'badge_cls': badge_cls,
                'badge_label': badge_label,
            })

        alertas_admin = AlertaAdmin.objects.select_related('instructor__usuario').order_by('-fecha_hora')[:10]

        context = {
            'reservas_hoy': reservas_hoy,
            'ocupacion': min(ocupacion, 100),
            'instructores_activos': instructores_activos,
            'instructores_en_sesion': instructores_en_sesion,
            'total_clientes': total_clientes,
            'horas': horas,
            'calendario_rows': calendario_rows,
            'historial': historial_data,
            'alertas_admin': alertas_admin,
            'fecha_vista': fecha_vista,
            'hoy': hoy,
            'usuario': request.user,
        }
        return render(request, 'admin/dashboard_admin.html', context)


@method_decorator(login_required, name='dispatch')
class GestionClientesView(RolRequeridoMixin, View):
    rol_requerido = 'admin'

    def get(self, request):
        buscar = request.GET.get('q', '')
        estado_filtro = request.GET.get('estado', '')

        perfiles = PerfilUsuario.objects.filter(rol='cliente').select_related('usuario')

        if buscar:
            perfiles = perfiles.filter(
                Q(usuario__first_name__icontains=buscar) |
                Q(usuario__last_name__icontains=buscar) |
                Q(usuario__email__icontains=buscar)
            )
        if estado_filtro == 'activo':
            perfiles = perfiles.filter(usuario__is_active=True)
        elif estado_filtro == 'inactivo':
            perfiles = perfiles.filter(usuario__is_active=False)

        context = {
            'perfiles': perfiles,
            'buscar': buscar,
            'estado_filtro': estado_filtro,
            'total': perfiles.count(),
            'usuario': request.user,
        }
        return render(request, 'admin/gestion_cli.html', context)

    def post(self, request):
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')

        if action == 'crear':
            nombre = request.POST.get('nombre', '').strip()
            email = request.POST.get('email', '').strip()
            
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Ya existe un usuario con este correo.')
                return redirect('admin_clientes')
                
            username = email.split('@')[0]
            base = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base}{counter}"
                counter += 1
                
            partes = nombre.split(' ', 1)
            first = partes[0]
            last = partes[1] if len(partes) > 1 else ''
            
            user = User.objects.create_user(
                username=username, email=email, password='cliente123',
                first_name=first, last_name=last
            )
            PerfilUsuario.objects.create(usuario=user, rol='cliente')
            messages.success(request, 'Cliente creado. Contraseña por defecto: cliente123')
            
        elif action == 'editar' and user_id:
            u = get_object_or_404(User, id=user_id)
            nombre = request.POST.get('nombre', '').strip()
            
            partes = nombre.split(' ', 1)
            u.first_name = partes[0]
            u.last_name = partes[1] if len(partes) > 1 else ''
            u.email = request.POST.get('email', u.email)
            u.save()
            messages.success(request, 'Cliente actualizado.')

        elif action == 'toggle_activo' and user_id:
            u = get_object_or_404(User, id=user_id)
            u.is_active = not u.is_active
            u.save()
            messages.success(request, 'Estado del cliente actualizado.')
            
        elif action == 'eliminar' and user_id:
            u = get_object_or_404(User, id=user_id)
            u.delete()
            messages.success(request, 'Cliente eliminado.')
            
        return redirect('admin_clientes')


@method_decorator(login_required, name='dispatch')
class GestionInstalacionesView(RolRequeridoMixin, View):
    rol_requerido = 'admin'

    def get(self, request):
        instalaciones = Instalacion.objects.all()
        context = {
            'instalaciones': instalaciones,
            'usuario': request.user,
        }
        return render(request, 'admin/gestion_inst.html', context)

    def post(self, request):
        action = request.POST.get('action')
        inst_id = request.POST.get('inst_id')

        if action == 'crear':
            Instalacion.objects.create(
                nombre=request.POST.get('nombre', 'Nueva Instalación'),
                tipo=request.POST.get('tipo', 'Deportiva'),
                capacidad=request.POST.get('capacidad', 4),
                descripcion=request.POST.get('descripcion', ''),
                precio_hora=request.POST.get('precio_hora', 30),
            )
            messages.success(request, 'Instalación creada.')
        elif action == 'toggle_estado' and inst_id:
            inst = get_object_or_404(Instalacion, id=inst_id)
            inst.estado = 'mantenimiento' if inst.estado == 'activa' else 'activa'
            inst.save()
            messages.success(request, 'Estado de instalación actualizado.')
        elif action == 'editar' and inst_id:
            inst = get_object_or_404(Instalacion, id=inst_id)
            inst.nombre = request.POST.get('nombre', inst.nombre)
            inst.tipo = request.POST.get('tipo', inst.tipo)
            inst.capacidad = request.POST.get('capacidad', inst.capacidad)
            inst.descripcion = request.POST.get('descripcion', inst.descripcion)
            inst.save()
            messages.success(request, 'Instalación actualizada.')
        elif action == 'eliminar' and inst_id:
            inst = get_object_or_404(Instalacion, id=inst_id)
            inst.delete()
            messages.success(request, 'Instalación eliminada.')
        return redirect('admin_instalaciones')


@method_decorator(login_required, name='dispatch')
class GestionInstructoresView(RolRequeridoMixin, View):
    rol_requerido = 'admin'

    def get(self, request):
        buscar = request.GET.get('q', '')
        especialidad = request.GET.get('especialidad', '')

        instructores = Instructor.objects.select_related('usuario')

        if buscar:
            instructores = instructores.filter(
                Q(usuario__first_name__icontains=buscar) |
                Q(usuario__last_name__icontains=buscar) |
                Q(usuario__email__icontains=buscar)
            )
        if especialidad:
            instructores = instructores.filter(especialidad=especialidad)

        hoy = timezone.now().date()
        for inst in instructores:
            inst.clases_hoy_count = ClaseHoy.objects.filter(
                instructor=inst, fecha=hoy
            ).count()

        context = {
            'instructores': instructores,
            'buscar': buscar,
            'especialidad': especialidad,
            'total': instructores.count(),
            'usuario': request.user,
        }
        return render(request, 'admin/gestion_prof.html', context)

    def post(self, request):
        action = request.POST.get('action')
        inst_id = request.POST.get('inst_id')

        if action == 'crear':
            nombre = request.POST.get('nombre', '').strip()
            email = request.POST.get('email', '').strip()
            especialidad = request.POST.get('especialidad', 'General')
            
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Ya existe un usuario con este correo.')
                return redirect('admin_instructores')
                
            username = email.split('@')[0]
            base = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base}{counter}"
                counter += 1
                
            partes = nombre.split(' ', 1)
            first = partes[0]
            last = partes[1] if len(partes) > 1 else ''
            
            user = User.objects.create_user(
                username=username, email=email, password='instructor123',
                first_name=first, last_name=last
            )
            PerfilUsuario.objects.create(usuario=user, rol='instructor')
            instructor = Instructor.objects.create(
                usuario=user,
                especialidad=especialidad,
                estado='disponible',
                calificacion_promedio=5.0,
                tarifa_hora=request.POST.get('tarifa_hora', 20.00)
            )
            if 'foto' in request.FILES:
                instructor.foto = request.FILES['foto']
                instructor.save()
            messages.success(request, 'Instructor creado. Contraseña por defecto: instructor123')
            
        elif action == 'editar' and inst_id:
            inst = get_object_or_404(Instructor, id=inst_id)
            user = inst.usuario
            nombre = request.POST.get('nombre', '').strip()
            
            partes = nombre.split(' ', 1)
            user.first_name = partes[0]
            user.last_name = partes[1] if len(partes) > 1 else ''
            user.email = request.POST.get('email', user.email)
            user.save()
            
            inst.especialidad = request.POST.get('especialidad', inst.especialidad)
            if request.POST.get('tarifa_hora'):
                try:
                    inst.tarifa_hora = float(request.POST.get('tarifa_hora'))
                except ValueError:
                    pass
            if 'foto' in request.FILES:
                inst.foto = request.FILES['foto']
            inst.save()
            messages.success(request, 'Instructor actualizado.')
            
        elif action == 'eliminar' and inst_id:
            inst = get_object_or_404(Instructor, id=inst_id)
            user = inst.usuario
            user.delete() # Esto borra PerfilUsuario e Instructor en cascada
            messages.success(request, 'Instructor eliminado.')
            
        elif action == 'cambiar_estado' and inst_id:
            inst = get_object_or_404(Instructor, id=inst_id)
            nuevo_estado = request.POST.get('estado', 'disponible')
            inst.estado = nuevo_estado
            inst.save()
            messages.success(request, 'Estado del instructor actualizado.')
            
        return redirect('admin_instructores')


# ─────────────────────────────────────────────
# Vistas de Reconocimiento Facial
# ─────────────────────────────────────────────

@method_decorator(login_required, name='dispatch')
class InstructorFotoView(RolRequeridoMixin, View):
    """Devuelve la URL de la foto del instructor autenticado como JSON."""
    rol_requerido = 'instructor'

    def get(self, request):
        instructor = getattr(request.user, 'instructor', None)
        if not instructor:
            return JsonResponse({'error': 'Perfil de instructor no encontrado'}, status=404)
        if instructor.foto:
            foto_url = request.build_absolute_uri(instructor.foto.url)
        else:
            foto_url = None
        return JsonResponse({'foto_url': foto_url, 'nombre': request.user.get_full_name() or request.user.username})


@method_decorator(login_required, name='dispatch')
class IniciarClaseView(RolRequeridoMixin, View):
    """Cambia el estado de una clase/reserva a 'en_curso'."""
    rol_requerido = 'instructor'

    def post(self, request):
        instructor = getattr(request.user, 'instructor', None)
        if not instructor:
            return JsonResponse({'error': 'Perfil de instructor no encontrado'}, status=404)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Datos inválidos'}, status=400)

        clase_id = data.get('clase_id')
        tipo = data.get('tipo', 'grupal')  # 'grupal' o 'privada'

        ahora = timezone.now()
        hora_actual = ahora.time()
        hoy = ahora.date()

        def _procesar_inicio(obj, hora_inicio, nombre_sesion):
            if hora_actual < hora_inicio:
                return JsonResponse({'error': f'No puedes iniciar la clase antes de las {hora_inicio.strftime("%H:%M")}'}, status=400)
            
            inicio_dt = datetime.datetime.combine(hoy, hora_inicio)
            limite_tarde = (inicio_dt + datetime.timedelta(minutes=20)).time()
            if hora_actual > limite_tarde:
                AlertaAdmin.objects.create(
                    tipo='llegada_tarde',
                    mensaje=f"Inició tarde: {nombre_sesion} a las {hora_actual.strftime('%H:%M')} (programada {hora_inicio.strftime('%H:%M')})",
                    instructor=instructor
                )
            obj.estado = 'en_curso'
            obj.save()
            return JsonResponse({'ok': True, 'mensaje': f'{nombre_sesion} iniciada correctamente'})

        if tipo == 'grupal' and clase_id:
            clase = get_object_or_404(ClaseHoy, id=clase_id, instructor=instructor)
            if clase.estado != 'pendiente':
                return JsonResponse({'error': f'La clase ya está en estado: {clase.estado}'}, status=400)
            return _procesar_inicio(clase, clase.hora_inicio, clase.nombre_clase)

        elif tipo == 'privada' and clase_id:
            reserva = get_object_or_404(Reserva, id=clase_id, instructor=instructor)
            if reserva.estado != 'confirmada':
                return JsonResponse({'error': f'La reserva ya está en estado: {reserva.estado}'}, status=400)
            return _procesar_inicio(reserva, reserva.hora_inicio, f"Clase privada con {reserva.cliente.username}")

        # Sin ID específico: intentar la próxima
        clase = ClaseHoy.objects.filter(instructor=instructor, fecha=hoy, estado='pendiente').order_by('hora_inicio').first()
        if clase:
            return _procesar_inicio(clase, clase.hora_inicio, clase.nombre_clase)

        reserva = Reserva.objects.filter(instructor=instructor, fecha=hoy, estado='confirmada').order_by('hora_inicio').first()
        if reserva:
            return _procesar_inicio(reserva, reserva.hora_inicio, f"Clase privada con {reserva.cliente.username}")

        return JsonResponse({'error': 'No se encontró ninguna sesión pendiente para iniciar'}, status=404)
        
@method_decorator(login_required, name='dispatch')
class ReportarFalloFacialView(RolRequeridoMixin, View):
    """Registra un fallo persistente de reconocimiento facial."""
    rol_requerido = 'instructor'

    def post(self, request):
        instructor = getattr(request.user, 'instructor', None)
        if not instructor:
            return JsonResponse({'error': 'Perfil no encontrado'}, status=404)
        
        try:
            data = json.loads(request.body)
            clase_id = data.get('clase_id')
            tipo = data.get('tipo', 'grupal')
            
            nombre_sesion = "Sesión desconocida"
            if tipo == 'grupal' and clase_id:
                clase = ClaseHoy.objects.filter(id=clase_id).first()
                if clase: nombre_sesion = clase.nombre_clase
            elif tipo == 'privada' and clase_id:
                reserva = Reserva.objects.filter(id=clase_id).first()
                if reserva: nombre_sesion = f"Privada con {reserva.cliente.username}"

            AlertaAdmin.objects.create(
                tipo='fallo_reconocimiento',
                mensaje=f"Fallo crítico de reconocimiento facial (3 intentos) en: {nombre_sesion}",
                instructor=instructor
            )
            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(login_required, name='dispatch')
class FinalizarClaseView(RolRequeridoMixin, View):
    """Cambia el estado de una clase/reserva a 'completada'."""
    rol_requerido = 'instructor'

    def post(self, request):
        instructor = getattr(request.user, 'instructor', None)
        if not instructor:
            return JsonResponse({'error': 'Perfil de instructor no encontrado'}, status=404)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Datos inválidos'}, status=400)

        clase_id = data.get('clase_id')
        tipo = data.get('tipo', 'grupal')

        ahora = timezone.now()
        hora_actual = ahora.time()
        hoy = ahora.date()

        def _procesar_fin(obj, hora_inicio, hora_fin, nombre_sesion):
            inicio_dt = datetime.datetime.combine(hoy, hora_inicio)
            fin_dt = datetime.datetime.combine(hoy, hora_fin)
            duracion_total = (fin_dt - inicio_dt).total_seconds()
            
            # Tiempo desde el inicio programado hasta ahora (aprox el tiempo que duró)
            tiempo_transcurrido = (ahora - timezone.make_aware(inicio_dt)).total_seconds()
            
            if tiempo_transcurrido < (duracion_total * 0.70):
                AlertaAdmin.objects.create(
                    tipo='salida_temprana',
                    mensaje=f"Finalizó temprano: {nombre_sesion} a las {hora_actual.strftime('%H:%M')} (programada hasta {hora_fin.strftime('%H:%M')})",
                    instructor=instructor
                )
            
            obj.estado = 'completada'
            obj.save()
            return JsonResponse({'ok': True, 'mensaje': f'{nombre_sesion} finalizada correctamente'})

        if tipo == 'grupal' and clase_id:
            clase = get_object_or_404(ClaseHoy, id=clase_id, instructor=instructor)
            if clase.estado != 'en_curso':
                return JsonResponse({'error': 'La clase no está en curso.'}, status=400)
            return _procesar_fin(clase, clase.hora_inicio, clase.hora_fin, clase.nombre_clase)

        elif tipo == 'privada' and clase_id:
            reserva = get_object_or_404(Reserva, id=clase_id, instructor=instructor)
            if reserva.estado != 'en_curso':
                return JsonResponse({'error': 'La reserva no está en curso.'}, status=400)
            return _procesar_fin(reserva, reserva.hora_inicio, reserva.hora_fin, f"Clase privada con {reserva.cliente.username}")

        # Sin ID: la primera en curso
        clase = ClaseHoy.objects.filter(instructor=instructor, fecha=hoy, estado='en_curso').order_by('hora_inicio').first()
        if clase:
            return _procesar_fin(clase, clase.hora_inicio, clase.hora_fin, clase.nombre_clase)

        reserva = Reserva.objects.filter(instructor=instructor, fecha=hoy, estado='en_curso').order_by('hora_inicio').first()
        if reserva:
            return _procesar_fin(reserva, reserva.hora_inicio, reserva.hora_fin, f"Clase privada con {reserva.cliente.username}")

        return JsonResponse({'error': 'No se encontró ninguna sesión en curso para finalizar'}, status=404)


# ─────────────────────────────────────────────
# Gestión Clases Compartidas (Admin)
# ─────────────────────────────────────────────

@method_decorator(login_required, name='dispatch')
class GestionClasesCompartidasView(RolRequeridoMixin, View):
    rol_requerido = 'admin'

    def get(self, request):
        dia_filtro = request.GET.get('dia', '')
        especialidad_filtro = request.GET.get('especialidad', '')
        estado_filtro = request.GET.get('estado', '')

        clases = ClaseCompartida.objects.select_related(
            'instructor__usuario', 'instalacion'
        ).prefetch_related('inscripciones')

        if dia_filtro != '':
            try:
                clases = clases.filter(dia_semana=int(dia_filtro))
            except ValueError:
                pass
        if especialidad_filtro:
            clases = clases.filter(instructor__especialidad=especialidad_filtro)
        if estado_filtro == 'activa':
            clases = clases.filter(activa=True)
        elif estado_filtro == 'inactiva':
            clases = clases.filter(activa=False)

        # KPIs
        total_activas = ClaseCompartida.objects.filter(activa=True).count()
        total_inscritos = InscripcionClase.objects.count()
        clases_llenas = sum(1 for c in ClaseCompartida.objects.filter(activa=True) if c.lleno)
        con_cupo = total_activas - clases_llenas

        instructores = Instructor.objects.select_related('usuario').filter(estado__in=['disponible', 'ocupado'])
        instalaciones = Instalacion.objects.filter(estado='activa')

        # Serializar instructores para JS (filtrado dinámico)
        instructores_json = json.dumps([
            {
                'id': i.id,
                'nombre': i.usuario.get_full_name() or i.usuario.username,
                'especialidad': i.especialidad,
                'tipo_instalacion': REGLAS_ESPECIALIDAD.get(i.especialidad, {}).get('tipo_instalacion'),
                'cupo_max': REGLAS_ESPECIALIDAD.get(i.especialidad, {}).get('cupo_max', 10),
                'permite_compartida': REGLAS_ESPECIALIDAD.get(i.especialidad, {}).get('compartida', True),
                'tarifa_hora': float(i.tarifa_hora),
            }
            for i in instructores
        ])
        instalaciones_json = json.dumps([
            {'id': ins.id, 'nombre': ins.nombre, 'tipo': ins.tipo, 'precio_hora': float(ins.precio_hora)}
            for ins in instalaciones
        ])

        context = {
            'clases': clases,
            'instructores': instructores,
            'instalaciones': instalaciones,
            'instructores_json': instructores_json,
            'instalaciones_json': instalaciones_json,
            'dia_filtro': dia_filtro,
            'especialidad_filtro': especialidad_filtro,
            'estado_filtro': estado_filtro,
            'total_activas': total_activas,
            'total_inscritos': total_inscritos,
            'clases_llenas': clases_llenas,
            'con_cupo': con_cupo,
            'usuario': request.user,
            'dias': ClaseCompartida.DIA_CHOICES,
            'niveles': ClaseCompartida.NIVEL_CHOICES,
        }
        return render(request, 'admin/gestion_clases.html', context)

    def post(self, request):
        action = request.POST.get('action')
        clase_id = request.POST.get('clase_id')

        if action == 'crear':
            instructor_id = request.POST.get('instructor')
            instalacion_id = request.POST.get('instalacion')
            instructor = get_object_or_404(Instructor, id=instructor_id, estado__in=['disponible', 'ocupado'])
            instalacion = get_object_or_404(Instalacion, id=instalacion_id, estado='activa')

            dia_semana = int(request.POST.get('dia_semana', 0))
            hora_inicio_str = request.POST.get('hora_inicio')
            hora_fin_str = request.POST.get('hora_fin')

            try:
                import datetime
                hi_obj = datetime.datetime.strptime(hora_inicio_str, '%H:%M').time()
                hf_obj = datetime.datetime.strptime(hora_fin_str, '%H:%M').time()
                
                if hi_obj < datetime.time(8, 0) or hf_obj > datetime.time(19, 0):
                    messages.error(request, 'El horario operativo es de 08:00 a 19:00.')
                    return redirect('admin_clases')
                    
                if hi_obj >= hf_obj:
                    messages.error(request, 'La hora de inicio debe ser anterior a la hora de fin.')
                    return redirect('admin_clases')
            except ValueError:
                messages.error(request, 'Formato de hora incorrecto.')
                return redirect('admin_clases')

            # Validar especialidad vs instalación
            regla = REGLAS_ESPECIALIDAD.get(instructor.especialidad, {})
            if not regla.get('compartida', False):
                messages.error(request, f'Los instructores de {instructor.especialidad} no pueden tener clases compartidas.')
                return redirect('admin_clases')

            tipo_requerido = regla.get('tipo_instalacion')
            if tipo_requerido and instalacion.tipo != tipo_requerido:
                messages.error(request, f'Un instructor de {instructor.especialidad} debe dar clases en instalaciones de tipo "{tipo_requerido}", no en "{instalacion.tipo}".')
                return redirect('admin_clases')

            cupo_max = int(request.POST.get('cupo_maximo', regla.get('cupo_max', 10)))

            # Validar límite de grupos simultáneos y ocupación de Instalación
            grupos_max = regla.get('grupos_max', 1)
            grupos_existentes = ClaseCompartida.objects.filter(
                instalacion=instalacion,
                dia_semana=dia_semana,
                hora_inicio__lt=hf_obj,
                hora_fin__gt=hi_obj,
                activa=True
            ).count()
            
            if grupos_existentes >= grupos_max:
                if grupos_max == 1:
                    messages.error(request, 'La instalación ya está ocupada por otra Clase Compartida en ese horario.')
                else:
                    messages.error(request, f'La instalación ya superó el máximo de {grupos_max} grupos simultáneos permitidos.')
                return redirect('admin_clases')

            # Solapamiento de Instructor en Clases Compartidas
            instructor_ocupado = ClaseCompartida.objects.filter(
                instructor=instructor,
                dia_semana=dia_semana,
                hora_inicio__lt=hf_obj,
                hora_fin__gt=hi_obj,
                activa=True
            ).exists()
            if instructor_ocupado:
                messages.error(request, 'El instructor ya imparte otra Clase Compartida en ese horario.')
                return redirect('admin_clases')

            # Limitar cupo según regla
            cupo_limite = regla.get('cupo_max', cupo_max)
            cupo_maximo = min(cupo_max, cupo_limite)

            clase = ClaseCompartida(
                nombre=request.POST.get('nombre', ''),
                instructor=instructor,
                instalacion=instalacion,
                dia_semana=dia_semana,
                hora_inicio=hi_obj,
                hora_fin=hf_obj,
                cupo_maximo=cupo_maximo,
                nivel=request.POST.get('nivel', 'Todos'),
                descripcion=request.POST.get('descripcion', ''),
                activa=True,
            )
            clase.precio_persona = clase.calcular_precio()
            # El admin puede sobreescribir el precio
            precio_manual = request.POST.get('precio_persona')
            if precio_manual:
                try:
                    clase.precio_persona = float(precio_manual)
                except ValueError:
                    pass
            clase.save()
            messages.success(request, f'Clase "{clase.nombre}" creada exitosamente.')

        elif action == 'editar' and clase_id:
            clase = get_object_or_404(ClaseCompartida, id=clase_id)
            clase.nombre = request.POST.get('nombre', clase.nombre)
            clase.nivel = request.POST.get('nivel', clase.nivel)
            clase.descripcion = request.POST.get('descripcion', clase.descripcion)
            cupo_nuevo = request.POST.get('cupo_maximo')
            if cupo_nuevo:
                regla = REGLAS_ESPECIALIDAD.get(clase.instructor.especialidad, {})
                cupo_limite = regla.get('cupo_max', 999)
                clase.cupo_maximo = min(int(cupo_nuevo), cupo_limite)
            precio_manual = request.POST.get('precio_persona')
            if precio_manual:
                try:
                    clase.precio_persona = float(precio_manual)
                except ValueError:
                    pass
            clase.save()
            messages.success(request, f'Clase "{clase.nombre}" actualizada.')

        elif action == 'toggle_activa' and clase_id:
            clase = get_object_or_404(ClaseCompartida, id=clase_id)
            clase.activa = not clase.activa
            clase.save()
            estado = 'activada' if clase.activa else 'desactivada'
            messages.success(request, f'Clase "{clase.nombre}" {estado}.')

        elif action == 'eliminar' and clase_id:
            clase = get_object_or_404(ClaseCompartida, id=clase_id)
            if clase.inscritos_count > 0:
                messages.error(request, f'No se puede eliminar "{clase.nombre}" porque tiene {clase.inscritos_count} cliente(s) inscrito(s).')
            else:
                nombre = clase.nombre
                clase.delete()
                messages.success(request, f'Clase "{nombre}" eliminada.')

        return redirect('admin_clases')


@method_decorator(login_required, name='dispatch')
class ClaseCompartidaInscritosView(RolRequeridoMixin, View):
    """Devuelve JSON con los inscritos de una clase (para modal en admin)."""
    rol_requerido = 'admin'

    def get(self, request, clase_id):
        clase = get_object_or_404(ClaseCompartida, id=clase_id)
        inscritos = clase.inscripciones.select_related('cliente').order_by('fecha_inscripcion')
        data = [
            {
                'nombre': i.cliente.get_full_name() or i.cliente.username,
                'email': i.cliente.email,
                'fecha': i.fecha_inscripcion.strftime('%d/%m/%Y %H:%M'),
            }
            for i in inscritos
        ]
        return JsonResponse({
            'clase': clase.nombre,
            'inscritos': data,
            'cupo_maximo': clase.cupo_maximo,
            'cupo_disponible': clase.cupo_disponible,
        })


# ─────────────────────────────────────────────
# Catálogo de Clases Compartidas (Cliente)
# ─────────────────────────────────────────────

@method_decorator(login_required, name='dispatch')
class CatalogoClasesView(RolRequeridoMixin, View):
    rol_requerido = 'cliente'

    def get(self, request):
        dia_filtro = request.GET.get('dia', '')
        nivel_filtro = request.GET.get('nivel', '')
        especialidad_filtro = request.GET.get('especialidad', '')

        clases = ClaseCompartida.objects.filter(activa=True).select_related(
            'instructor__usuario', 'instalacion'
        ).prefetch_related('inscripciones').order_by('dia_semana', 'hora_inicio')

        if dia_filtro != '':
            try:
                clases = clases.filter(dia_semana=int(dia_filtro))
            except ValueError:
                pass
        if nivel_filtro:
            clases = clases.filter(nivel=nivel_filtro)
        if especialidad_filtro:
            clases = clases.filter(instructor__especialidad=especialidad_filtro)

        # IDs de clases en las que ya está inscrito
        mis_inscripciones_ids = set(
            InscripcionClase.objects.filter(cliente=request.user).values_list('clase_id', flat=True)
        )

        context = {
            'clases': clases,
            'mis_inscripciones_ids': mis_inscripciones_ids,
            'dia_filtro': dia_filtro,
            'nivel_filtro': nivel_filtro,
            'especialidad_filtro': especialidad_filtro,
            'dias': ClaseCompartida.DIA_CHOICES,
            'niveles': ClaseCompartida.NIVEL_CHOICES,
            'usuario': request.user,
        }
        return render(request, 'cliente/catalogo_clases.html', context)

    def post(self, request):
        action = request.POST.get('action')
        clase_id = request.POST.get('clase_id')
        clase = get_object_or_404(ClaseCompartida, id=clase_id, activa=True)

        if action == 'inscribir':
            if clase.lleno:
                return JsonResponse({'error': 'Esta clase ya no tiene cupo disponible.'}, status=400)
            try:
                InscripcionClase.objects.create(cliente=request.user, clase=clase)
                return JsonResponse({
                    'ok': True,
                    'mensaje': f'¡Te has inscrito en "{clase.nombre}"!',
                    'inscritos': clase.inscritos_count,
                    'cupo_disponible': clase.cupo_disponible,
                })
            except Exception:
                return JsonResponse({'error': 'Ya estás inscrito en esta clase.'}, status=400)

        elif action == 'cancelar':
            deleted, _ = InscripcionClase.objects.filter(cliente=request.user, clase=clase).delete()
            if deleted:
                return JsonResponse({
                    'ok': True,
                    'mensaje': f'Inscripción en "{clase.nombre}" cancelada.',
                    'inscritos': clase.inscritos_count,
                    'cupo_disponible': clase.cupo_disponible,
                })
            return JsonResponse({'error': 'No estás inscrito en esta clase.'}, status=400)

        return JsonResponse({'error': 'Acción no válida.'}, status=400)


# ─────────────────────────────────────────────
# API ViewSets (REST)
# ─────────────────────────────────────────────

class InstalacionViewSet(viewsets.ModelViewSet):
    queryset = Instalacion.objects.all()
    serializer_class = InstalacionSerializer


class InstructorViewSet(viewsets.ModelViewSet):
    queryset = Instructor.objects.select_related('usuario').all()
    serializer_class = InstructorSerializer


class ReservaViewSet(viewsets.ModelViewSet):
    queryset = Reserva.objects.select_related('cliente', 'instalacion', 'instructor').all()
    serializer_class = ReservaSerializer


class ClaseHoyViewSet(viewsets.ModelViewSet):
    queryset = ClaseHoy.objects.select_related('instructor', 'instalacion').all()
    serializer_class = ClaseHoySerializer


class ClaseCompartidaViewSet(viewsets.ModelViewSet):
    queryset = ClaseCompartida.objects.select_related('instructor__usuario', 'instalacion').all()
    serializer_class = ClaseCompartidaSerializer
