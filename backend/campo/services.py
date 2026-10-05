"""
Reglas compartidas de novedades, insumos e informes: alcance por rol,
quién recibe los avisos y quién puede gestionar cada elemento.
"""
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from cuadrillas.models import Cuadrilla
from projects.models import Assignment, Project
from timetracker.models import TimeEntry
from users.models import Rol

from .models import Notificacion

User = get_user_model()


def proyectos_liderados(user):
    """Proyectos que un líder tiene asignados o en los que lidera una cuadrilla."""
    return Project.objects.filter(
        Q(id__in=Assignment.objects.filter(usuario=user).values("proyecto_id"))
        | Q(id__in=Cuadrilla.objects.filter(lider=user).values("proyecto_id"))
    )


def proyectos_permitidos(user):
    """Proyectos sobre los que el usuario puede crear novedades, solicitudes o informes."""
    if user.rol == Rol.ADMIN:
        return Project.objects.all()
    if user.rol == Rol.LIDER:
        return proyectos_liderados(user)
    return Project.objects.filter(asignaciones__usuario=user)


def filtrar_visibles(qs, user, extra=None):
    """
    Admin: todo. Líder: lo de sus proyectos y lo propio. Operario: lo propio.
    `extra` agrega condiciones de visibilidad (p. ej. participantes de un informe).
    """
    if user.rol == Rol.ADMIN:
        return qs
    cond = Q(autor=user)
    if extra is not None:
        cond |= extra
    if user.rol == Rol.LIDER:
        cond |= Q(proyecto__in=proyectos_liderados(user))
    return qs.filter(cond).distinct()


def puede_gestionar(user, obj):
    """Atender, aprobar, rechazar o devolver: el admin siempre; el líder en sus proyectos, salvo lo propio."""
    if user.rol == Rol.ADMIN:
        return True
    if user.rol != Rol.LIDER or obj.autor_id == user.id or obj.proyecto_id is None:
        return False
    return proyectos_liderados(user).filter(pk=obj.proyecto_id).exists()


def destinatarios(proyecto, excluir=None):
    """Líderes del proyecto (asignados o de sus cuadrillas) y todos los administradores."""
    cond = Q(rol=Rol.ADMIN)
    if proyecto is not None:
        cond |= Q(rol=Rol.LIDER, asignaciones__proyecto=proyecto)
        cond |= Q(rol=Rol.LIDER, cuadrillas_lideradas__proyecto=proyecto)
    qs = User.objects.filter(cond, is_active=True).distinct()
    if excluir is not None:
        qs = qs.exclude(pk=excluir.pk)
    return qs


def notificar(usuarios, tipo, texto, enlace=""):
    Notificacion.objects.bulk_create(
        [Notificacion(destinatario=u, tipo=tipo, texto=texto[:300], enlace=enlace) for u in usuarios]
    )


def notificar_autor(obj, actor, tipo, texto, enlace=""):
    if obj.autor_id and obj.autor_id != actor.id:
        notificar([obj.autor], tipo, texto, enlace)


def nombre(user):
    if user is None:
        return "Usuario eliminado"
    return user.get_full_name() or user.username


def resumen_personal(proyecto_id, fecha):
    """[{usuario_id, nombre, minutos}] de los registros de tiempo del proyecto ese día."""
    ahora = timezone.now()
    totales = {}
    entradas = TimeEntry.objects.filter(proyecto_id=proyecto_id, hora_inicio__date=fecha).select_related("usuario")
    for e in entradas:
        fila = totales.setdefault(e.usuario_id, {"usuario_id": e.usuario_id, "nombre": nombre(e.usuario), "minutos": 0})
        fila["minutos"] += int(((e.hora_fin or ahora) - e.hora_inicio).total_seconds() // 60)
    return sorted(totales.values(), key=lambda f: f["nombre"])
