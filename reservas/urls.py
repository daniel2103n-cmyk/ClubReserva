from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LoginView, RegistroView, logout_view,
    ClienteDashboardView, HacerReservaView,
    InstructorDashboardView, InstructorCalendarioView,
    AdminDashboardView, GestionClientesView,
    GestionInstalacionesView, GestionInstructoresView,
    InstalacionViewSet, InstructorViewSet,
    ReservaViewSet, ClaseHoyViewSet,
    IniciarClaseView, FinalizarClaseView, InstructorFotoView,
    ReportarFalloFacialView,
    GestionClasesCompartidasView, ClaseCompartidaInscritosView,
    CatalogoClasesView, ClaseCompartidaViewSet,
)

router = DefaultRouter()
router.register(r'instalaciones', InstalacionViewSet)
router.register(r'instructores', InstructorViewSet)
router.register(r'reservas', ReservaViewSet)
router.register(r'clases', ClaseHoyViewSet)
router.register(r'clases-compartidas', ClaseCompartidaViewSet)

urlpatterns = [
    # Autenticación
    path('', LoginView.as_view(), name='login'),
    path('login/', LoginView.as_view(), name='login'),
    path('registro/', RegistroView.as_view(), name='registro'),
    path('logout/', logout_view, name='logout'),

    # Cliente
    path('cliente/dashboard/', ClienteDashboardView.as_view(), name='cliente_dashboard'),
    path('cliente/reservar/', HacerReservaView.as_view(), name='hacer_reserva'),
    path('cliente/clases/', CatalogoClasesView.as_view(), name='catalogo_clases'),

    # Instructor
    path('instructor/dashboard/', InstructorDashboardView.as_view(), name='instructor_dashboard'),
    path('instructor/calendario/', InstructorCalendarioView.as_view(), name='instructor_calendario'),
    path('instructor/iniciar-clase/', IniciarClaseView.as_view(), name='iniciar_clase'),
    path('instructor/reportar-fallo-facial/', ReportarFalloFacialView.as_view(), name='reportar_fallo_facial'),
    path('instructor/finalizar-clase/', FinalizarClaseView.as_view(), name='finalizar_clase'),
    path('instructor/mi-foto/', InstructorFotoView.as_view(), name='instructor_foto'),

    # Admin
    path('admin-panel/dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin-panel/clientes/', GestionClientesView.as_view(), name='admin_clientes'),
    path('admin-panel/instalaciones/', GestionInstalacionesView.as_view(), name='admin_instalaciones'),
    path('admin-panel/instructores/', GestionInstructoresView.as_view(), name='admin_instructores'),
    path('admin-panel/clases/', GestionClasesCompartidasView.as_view(), name='admin_clases'),
    path('admin-panel/clases/<int:clase_id>/inscritos/', ClaseCompartidaInscritosView.as_view(), name='admin_clase_inscritos'),

    # API REST
    path('api/', include(router.urls)),
]
