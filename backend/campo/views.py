from datetime import date

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from projects.serializers import ProjectSerializer
from users.models import Rol

from . import archivos
from .models import (
    EstadoInforme, EstadoNovedad, EstadoSolicitud, Foto, InformeServicio, Notificacion, Novedad,
    SolicitudInsumo, TipoNotificacion,
)
from .pdf import generar_pdf_informe
from .serializers import (
    FotoSerializer, InformeServicioSerializer, NotificacionSerializer, NovedadSerializer,
    SolicitudInsumoSerializer,
)
from .services import (
    destinatarios, filtrar_visibles, nombre, notificar, notificar_autor, proyectos_permitidos,
    puede_gestionar, resumen_personal,
)

MAX_FOTOS = {"novedad": 10, "solicitud": 10, "informe": 30}


class CampoViewSet(viewsets.ModelViewSet):
    """
    Base de novedades, solicitudes e informes.
    El autor edita o elimina solo mientras el elemento está en un estado editable;
    el admin puede eliminar siempre.
    """
    permission_classes = [IsAuthenticated]
    model = None
    estados_editables = ()
    visibilidad_extra = None

    def get_queryset(self):
        qs = self.model.objects.select_related("autor", "proyecto").prefetch_related("fotos")
        qs = filtrar_visibles(qs, self.request.user, self.visibilidad_extra(self.request.user)
                              if self.visibilidad_extra else None)
        params = self.request.query_params
        if params.get("estado"):
            qs = qs.filter(estado__in=params["estado"].split(","))
        if params.get("proyecto"):
            qs = qs.filter(proyecto_id=params["proyecto"])
        if params.get("mias") == "1":
            qs = qs.filter(autor=self.request.user)
        return qs

    def _gestionar(self, obj):
        if not puede_gestionar(self.request.user, obj):
            raise PermissionDenied("No puede gestionar este elemento.")

    def _editable(self, obj):
        user = self.request.user
        if user.rol == Rol.ADMIN:
            return
        if obj.autor_id != user.id or obj.estado not in self.estados_editables:
            raise PermissionDenied("Ya no se puede modificar.")

    def perform_update(self, serializer):
        self._editable(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._editable(instance)
        for foto in instance.fotos.all():
            foto.archivo.delete(save=False)
            foto.miniatura.delete(save=False)
        instance.delete()

    def _respuesta(self, obj):
        return Response(self.get_serializer(obj).data)


class NovedadViewSet(CampoViewSet):
    model = Novedad
    serializer_class = NovedadSerializer
    estados_editables = (EstadoNovedad.ABIERTA,)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("categoria"):
            qs = qs.filter(categoria=self.request.query_params["categoria"])
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        nov = serializer.save(autor=user)
        lugar = f" en {nov.proyecto.nombre}" if nov.proyecto else ""
        notificar(destinatarios(nov.proyecto, excluir=user), TipoNotificacion.NOVEDAD,
                  f"{nombre(user)} reportó una novedad{lugar}: {nov.titulo}", f"/campo/novedades?id={nov.id}")

    @action(detail=True, methods=["post"])
    def atender(self, request, pk=None):
        nov = self.get_object()
        self._gestionar(nov)
        if nov.estado != EstadoNovedad.ABIERTA:
            raise ValidationError("La novedad ya fue atendida.")
        nov.estado = EstadoNovedad.ATENDIDA
        nov.respuesta = request.data.get("respuesta", "").strip()
        nov.atendida_por = request.user
        nov.atendida_en = timezone.now()
        nov.save()
        notificar_autor(nov, request.user, TipoNotificacion.NOVEDAD,
                        f"{nombre(request.user)} atendió su novedad: {nov.titulo}", f"/campo/novedades?id={nov.id}")
        return self._respuesta(nov)


class SolicitudInsumoViewSet(CampoViewSet):
    model = SolicitudInsumo
    serializer_class = SolicitudInsumoSerializer
    estados_editables = (EstadoSolicitud.PENDIENTE,)

    def perform_create(self, serializer):
        user = self.request.user
        sol = serializer.save(autor=user)
        notificar(destinatarios(sol.proyecto, excluir=user), TipoNotificacion.INSUMO,
                  f"{nombre(user)} pidió insumos para {sol.proyecto.nombre}", f"/campo/insumos?id={sol.id}")

    def _cambiar(self, request, desde, hacia, verbo, comentario_obligatorio=False):
        sol = self.get_object()
        self._gestionar(sol)
        if sol.estado != desde:
            raise ValidationError(f"La solicitud está {sol.get_estado_display().lower()}.")
        comentario = request.data.get("comentario", "").strip()
        if comentario_obligatorio and not comentario:
            raise ValidationError({"comentario": "Indique el motivo."})
        sol.estado = hacia
        if comentario:
            sol.comentario = comentario
        if hacia == EstadoSolicitud.ENTREGADA:
            sol.entregada_en = timezone.now()
        else:
            sol.gestionada_por = request.user
            sol.gestionada_en = timezone.now()
        sol.save()
        notificar_autor(sol, request.user, TipoNotificacion.INSUMO,
                        f"{nombre(request.user)} {verbo} su solicitud de insumos para {sol.proyecto.nombre}",
                        f"/campo/insumos?id={sol.id}")
        return self._respuesta(sol)

    @action(detail=True, methods=["post"])
    def aprobar(self, request, pk=None):
        return self._cambiar(request, EstadoSolicitud.PENDIENTE, EstadoSolicitud.APROBADA, "aprobó")

    @action(detail=True, methods=["post"])
    def rechazar(self, request, pk=None):
        return self._cambiar(request, EstadoSolicitud.PENDIENTE, EstadoSolicitud.RECHAZADA, "rechazó",
                             comentario_obligatorio=True)

    @action(detail=True, methods=["post"])
    def entregar(self, request, pk=None):
        return self._cambiar(request, EstadoSolicitud.APROBADA, EstadoSolicitud.ENTREGADA, "marcó como entregada")


class InformeServicioViewSet(CampoViewSet):
    model = InformeServicio
    serializer_class = InformeServicioSerializer
    estados_editables = (EstadoInforme.BORRADOR, EstadoInforme.DEVUELTO)

    @staticmethod
    def visibilidad_extra(user):
        return Q(participantes=user)

    def get_queryset(self):
        return super().get_queryset().prefetch_related("participantes")

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)

    def perform_update(self, serializer):
        self._editable(serializer.instance)
        if serializer.instance.estado == EstadoInforme.APROBADO:
            raise PermissionDenied("Un informe aprobado no se puede modificar.")
        serializer.save()

    @action(detail=True, methods=["post", "delete"], parser_classes=[MultiPartParser, FormParser])
    def firma(self, request, pk=None):
        """Guarda (POST, campo `imagen`) o borra (DELETE) la firma del cliente."""
        inf = self.get_object()
        self._editable(inf)
        if inf.firma_imagen:
            inf.firma_imagen.delete(save=False)
        if request.method == "POST":
            if "imagen" not in request.FILES:
                raise ValidationError({"imagen": "Falta la imagen de la firma."})
            inf.firma_imagen.save("firma.png", archivos.procesar_firma(request.FILES["imagen"]), save=False)
        inf.save()
        return self._respuesta(inf)

    @action(detail=True, methods=["post"])
    def enviar(self, request, pk=None):
        inf = self.get_object()
        if inf.autor_id != request.user.id and request.user.rol != Rol.ADMIN:
            raise PermissionDenied("Solo el autor puede enviar el informe.")
        if inf.estado not in self.estados_editables:
            raise ValidationError("El informe ya fue enviado.")
        if not inf.actividades.strip():
            raise ValidationError({"actividades": "Describa las actividades realizadas antes de enviar."})
        inf.estado = EstadoInforme.ENVIADO
        inf.enviado_en = timezone.now()
        inf.save()
        notificar(destinatarios(inf.proyecto, excluir=request.user), TipoNotificacion.INFORME,
                  f"{nombre(request.user)} envió un informe de servicio de {inf.proyecto.nombre} para revisión",
                  f"/campo/informes?id={inf.id}")
        return self._respuesta(inf)

    @action(detail=True, methods=["post"])
    def aprobar(self, request, pk=None):
        inf = self.get_object()
        self._gestionar(inf)
        if inf.estado != EstadoInforme.ENVIADO:
            raise ValidationError("Solo se aprueban informes enviados.")
        with transaction.atomic():
            anio = timezone.localdate().year
            ultimo = (InformeServicio.objects.select_for_update()
                      .filter(consecutivo__startswith=f"INF-{anio}-").order_by("-consecutivo").first())
            numero = int(ultimo.consecutivo.rsplit("-", 1)[1]) + 1 if ultimo else 1
            inf.consecutivo = f"INF-{anio}-{numero:04d}"
            inf.estado = EstadoInforme.APROBADO
            inf.revisado_por = request.user
            inf.revisado_en = timezone.now()
            inf.comentario_revision = request.data.get("comentario", "").strip()
            inf.save()
            inf.pdf.save(f"{inf.consecutivo}.pdf", generar_pdf_informe(inf), save=True)
        notificar_autor(inf, request.user, TipoNotificacion.INFORME,
                        f"{nombre(request.user)} aprobó su informe {inf.consecutivo}", f"/campo/informes?id={inf.id}")
        return self._respuesta(inf)

    @action(detail=True, methods=["post"])
    def devolver(self, request, pk=None):
        inf = self.get_object()
        self._gestionar(inf)
        if inf.estado != EstadoInforme.ENVIADO:
            raise ValidationError("Solo se devuelven informes enviados.")
        comentario = request.data.get("comentario", "").strip()
        if not comentario:
            raise ValidationError({"comentario": "Indique qué debe corregirse."})
        inf.estado = EstadoInforme.DEVUELTO
        inf.comentario_revision = comentario
        inf.revisado_por = request.user
        inf.revisado_en = timezone.now()
        inf.save()
        notificar_autor(inf, request.user, TipoNotificacion.INFORME,
                        f"{nombre(request.user)} devolvió su informe de {inf.proyecto.nombre} para corrección",
                        f"/campo/informes?id={inf.id}")
        return self._respuesta(inf)

    @action(detail=False, methods=["get"], url_path="sugerir-personal")
    def sugerir_personal(self, request):
        """Personal y minutos registrados en el proyecto en la fecha dada (desde Tiempos)."""
        try:
            proyecto_id = int(request.query_params["proyecto"])
            fecha = date.fromisoformat(request.query_params["fecha"])
        except (KeyError, ValueError):
            raise ValidationError("Indique proyecto y fecha (AAAA-MM-DD).")
        return Response(resumen_personal(proyecto_id, fecha))


class FotoViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    """Subir (multipart: archivo, descripcion y novedad|solicitud|informe), describir o borrar fotos."""
    permission_classes = [IsAuthenticated]
    serializer_class = FotoSerializer
    parser_classes = [MultiPartParser, FormParser]

    vistas = {"novedad": NovedadViewSet, "solicitud": SolicitudInsumoViewSet, "informe": InformeServicioViewSet}

    def get_queryset(self):
        user = self.request.user
        return Foto.objects.filter(
            Q(novedad__in=filtrar_visibles(Novedad.objects.all(), user))
            | Q(solicitud__in=filtrar_visibles(SolicitudInsumo.objects.all(), user))
            | Q(informe__in=filtrar_visibles(InformeServicio.objects.all(), user, Q(participantes=user)))
        )

    def _validar_edicion(self, tipo, padre):
        vista = self.vistas[tipo]()
        vista.request = self.request
        vista._editable(padre)

    def create(self, request, *args, **kwargs):
        tipo = next((t for t in self.vistas if request.data.get(t)), None)
        if tipo is None:
            raise ValidationError("Indique a qué novedad, solicitud o informe pertenece la foto.")
        modelo = self.vistas[tipo].model
        visibles = filtrar_visibles(modelo.objects.all(), request.user,
                                    Q(participantes=request.user) if tipo == "informe" else None)
        padre = visibles.filter(pk=request.data[tipo]).first()
        if padre is None:
            raise ValidationError("El elemento no existe o no tiene acceso.")
        self._validar_edicion(tipo, padre)
        if padre.fotos.count() >= MAX_FOTOS[tipo]:
            raise ValidationError(f"Se permiten máximo {MAX_FOTOS[tipo]} fotos.")
        if "archivo" not in request.FILES:
            raise ValidationError({"archivo": "Falta la foto."})
        grande, mini = archivos.procesar_foto(request.FILES["archivo"])
        foto = Foto(subido_por=request.user, descripcion=request.data.get("descripcion", "")[:300], **{tipo: padre})
        foto.archivo.save("f.jpg", grande, save=False)
        foto.miniatura.save("m.jpg", mini, save=False)
        foto.save()
        return Response(self.get_serializer(foto).data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        foto = serializer.instance
        self._validar_edicion(next(t for t in self.vistas if getattr(foto, f"{t}_id")), foto.padre)
        serializer.save()

    def perform_destroy(self, foto):
        self._validar_edicion(next(t for t in self.vistas if getattr(foto, f"{t}_id")), foto.padre)
        foto.archivo.delete(save=False)
        foto.miniatura.delete(save=False)
        foto.delete()


class NotificacionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificacionSerializer

    def get_queryset(self):
        return Notificacion.objects.filter(destinatario=self.request.user)

    def list(self, request, *args, **kwargs):
        return Response(self.get_serializer(self.get_queryset()[:50], many=True).data)

    @action(detail=False, methods=["get"], url_path="no-leidas")
    def no_leidas(self, request):
        return Response({"total": self.get_queryset().filter(leida=False).count()})

    @action(detail=False, methods=["post"], url_path="marcar-leidas")
    def marcar_leidas(self, request):
        """Sin `ids` marca todas como leídas."""
        qs = self.get_queryset().filter(leida=False)
        if request.data.get("ids"):
            qs = qs.filter(pk__in=request.data["ids"])
        return Response({"actualizadas": qs.update(leida=True)})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mis_proyectos(request):
    """Proyectos en los que el usuario puede reportar, pedir insumos o hacer informes."""
    return Response(ProjectSerializer(proyectos_permitidos(request.user).order_by("nombre"), many=True).data)


def archivo(request, token):
    """Entrega un archivo privado a partir de un enlace firmado y temporal (vista Django simple:
    las etiquetas <img> no envían el token JWT, la autorización es la firma del enlace)."""
    return archivos.servir(request, token)
