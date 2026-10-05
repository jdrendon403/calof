import shutil
import tempfile
from datetime import timedelta
from io import BytesIO
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from cuadrillas.models import Cuadrilla
from projects.models import Assignment, Project
from timetracker.models import TimeEntry
from users.models import Usuario

from .models import EstadoInforme, Foto, InformeServicio, Notificacion, Novedad, SolicitudInsumo

MEDIA = Path(tempfile.mkdtemp(prefix="campo-tests-"))


def imagen(nombre="foto.jpg", formato="JPEG", tam=(800, 600)):
    buf = BytesIO()
    Image.new("RGB", tam, "steelblue").save(buf, formato)
    return SimpleUploadedFile(nombre, buf.getvalue(), content_type=f"image/{formato.lower()}")


@override_settings(MEDIA_ROOT=MEDIA, MEDIA_X_ACCEL=False)
class CampoBase(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.api = APIClient()
        self.admin = Usuario.objects.create_user(username="admin", password="x1234", rol="ADMIN")
        self.lider = Usuario.objects.create_user(username="lider", password="x1234", rol="LIDER")
        self.lider_otro = Usuario.objects.create_user(username="lider2", password="x1234", rol="LIDER")
        self.op = Usuario.objects.create_user(username="op", password="x1234", rol="OPERARIO",
                                              first_name="Juan", last_name="Pérez")
        self.op_otro = Usuario.objects.create_user(username="op2", password="x1234", rol="OPERARIO")
        self.p1 = Project.objects.create(nombre="Subestación", cliente="Energía S.A.")
        self.p2 = Project.objects.create(nombre="Planta")
        for u in (self.lider, self.op):
            Assignment.objects.create(usuario=u, proyecto=self.p1)
        for u in (self.lider_otro, self.op_otro):
            Assignment.objects.create(usuario=u, proyecto=self.p2)

    def como(self, user):
        self.api.force_authenticate(user=user)
        return self.api


class NovedadTest(CampoBase):
    def crear(self, user=None, **extra):
        data = {"proyecto": self.p1.id, "categoria": "SEGURIDAD", "titulo": "Cable expuesto", **extra}
        return self.como(user or self.op).post("/api/novedades/", data)

    def test_operario_crea_y_notifica_a_lideres_del_proyecto_y_admins(self):
        r = self.crear()
        self.assertEqual(r.status_code, status.HTTP_201_CREATED, r.data)
        destinatarios = set(Notificacion.objects.values_list("destinatario__username", flat=True))
        self.assertEqual(destinatarios, {"lider", "admin"})

    def test_lider_de_cuadrilla_tambien_recibe_aviso(self):
        lider_cuadrilla = Usuario.objects.create_user(username="lc", password="x1234", rol="LIDER")
        Cuadrilla.objects.create(nombre="A", proyecto=self.p1, lider=lider_cuadrilla)
        self.crear()
        self.assertTrue(Notificacion.objects.filter(destinatario=lider_cuadrilla).exists())

    def test_operario_no_reporta_en_proyecto_no_asignado(self):
        r = self.crear(proyecto=self.p2.id)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_novedad_sin_proyecto_solo_avisa_a_admins(self):
        r = self.crear(proyecto="", categoria="PERSONAL")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED, r.data)
        self.assertEqual(list(Notificacion.objects.values_list("destinatario__username", flat=True)), ["admin"])

    def test_visibilidad_por_rol(self):
        self.crear()
        self.crear(user=self.op_otro, proyecto=self.p2.id)
        self.assertEqual(len(self.como(self.op).get("/api/novedades/").data), 1)
        self.assertEqual(len(self.como(self.lider).get("/api/novedades/").data), 1)
        self.assertEqual(len(self.como(self.lider_otro).get("/api/novedades/").data), 1)
        self.assertEqual(len(self.como(self.admin).get("/api/novedades/").data), 2)

    def test_lider_atiende_y_autor_recibe_aviso(self):
        nov_id = self.crear().data["id"]
        Notificacion.objects.all().delete()
        r = self.como(self.lider).post(f"/api/novedades/{nov_id}/atender/", {"respuesta": "Se aisló el área"})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["estado"], "ATENDIDA")
        self.assertEqual(Notificacion.objects.get().destinatario, self.op)
        # No se puede atender dos veces ni editar después de atendida
        self.assertEqual(self.como(self.lider).post(f"/api/novedades/{nov_id}/atender/").status_code, 400)
        self.assertEqual(self.como(self.op).patch(f"/api/novedades/{nov_id}/", {"titulo": "x"}).status_code, 403)

    def test_operario_y_lider_de_otro_proyecto_no_atienden(self):
        nov_id = self.crear().data["id"]
        self.assertEqual(self.como(self.op).post(f"/api/novedades/{nov_id}/atender/").status_code, 403)
        self.assertEqual(self.como(self.lider_otro).post(f"/api/novedades/{nov_id}/atender/").status_code, 404)

    def test_lider_no_atiende_lo_propio(self):
        nov_id = self.crear(user=self.lider).data["id"]
        self.assertEqual(self.como(self.lider).post(f"/api/novedades/{nov_id}/atender/").status_code, 403)
        self.assertEqual(self.como(self.admin).post(f"/api/novedades/{nov_id}/atender/").status_code, 200)


class FotoTest(CampoBase):
    def setUp(self):
        super().setUp()
        self.nov = Novedad.objects.create(autor=self.op, proyecto=self.p1, titulo="Falla")

    def subir(self, user=None, archivo=None, **extra):
        data = {"novedad": self.nov.id, "archivo": archivo or imagen(), "descripcion": "Tablero", **extra}
        return self.como(user or self.op).post("/api/fotos/", data, format="multipart")

    def test_sube_normaliza_y_sirve_con_enlace_firmado(self):
        r = self.subir(archivo=imagen("grande.png", "PNG", (4000, 3000)))
        self.assertEqual(r.status_code, status.HTTP_201_CREATED, r.data)
        foto = Foto.objects.get()
        with Image.open(foto.archivo.path) as img:
            self.assertEqual(img.format, "JPEG")
            self.assertEqual(max(img.size), 1600)
        with Image.open(foto.miniatura.path) as img:
            self.assertEqual(max(img.size), 400)
        self.api.force_authenticate(user=None)
        resp = self.api.get(r.data["url"])
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "image/jpeg")

    def test_enlace_alterado_da_404(self):
        url = self.subir().data["url"]
        self.assertEqual(self.api.get(url.rstrip("/") + "x/").status_code, 404)

    def test_rechaza_archivo_que_no_es_imagen(self):
        falso = SimpleUploadedFile("virus.jpg", b"no soy una imagen", content_type="image/jpeg")
        self.assertEqual(self.subir(archivo=falso).status_code, status.HTTP_400_BAD_REQUEST)

    def test_operario_de_otro_proyecto_no_sube_ni_ve(self):
        self.subir()
        self.assertEqual(self.subir(user=self.op_otro).status_code, status.HTTP_400_BAD_REQUEST)
        foto = Foto.objects.get()
        self.assertEqual(self.como(self.op_otro).delete(f"/api/fotos/{foto.id}/").status_code, 404)

    def test_no_se_agregan_fotos_a_novedad_atendida(self):
        self.nov.estado = "ATENDIDA"
        self.nov.save()
        self.assertEqual(self.subir().status_code, status.HTTP_403_FORBIDDEN)

    def test_limite_de_fotos(self):
        for _ in range(10):
            self.assertEqual(self.subir(archivo=imagen(tam=(50, 50))).status_code, 201)
        self.assertEqual(self.subir(archivo=imagen(tam=(50, 50))).status_code, 400)

    def test_borrar_foto_elimina_archivos(self):
        self.subir()
        foto = Foto.objects.get()
        rutas = [Path(foto.archivo.path), Path(foto.miniatura.path)]
        self.assertEqual(self.como(self.op).delete(f"/api/fotos/{foto.id}/").status_code, 204)
        self.assertFalse(any(r.exists() for r in rutas))


class InsumoTest(CampoBase):
    def crear(self):
        return self.como(self.op).post("/api/insumos/", {"proyecto": self.p1.id, "detalle": "20 m cable 12 AWG"})

    def test_flujo_aprobar_y_entregar(self):
        sol_id = self.crear().data["id"]
        self.assertEqual(Notificacion.objects.filter(destinatario=self.lider).count(), 1)
        # No se entrega sin aprobar
        self.assertEqual(self.como(self.lider).post(f"/api/insumos/{sol_id}/entregar/").status_code, 400)
        r = self.como(self.lider).post(f"/api/insumos/{sol_id}/aprobar/")
        self.assertEqual(r.data["estado"], "APROBADA")
        r = self.como(self.lider).post(f"/api/insumos/{sol_id}/entregar/")
        self.assertEqual(r.data["estado"], "ENTREGADA")
        self.assertIsNotNone(SolicitudInsumo.objects.get().entregada_en)
        self.assertEqual(Notificacion.objects.filter(destinatario=self.op).count(), 2)

    def test_rechazar_exige_motivo(self):
        sol_id = self.crear().data["id"]
        self.assertEqual(self.como(self.lider).post(f"/api/insumos/{sol_id}/rechazar/").status_code, 400)
        r = self.como(self.lider).post(f"/api/insumos/{sol_id}/rechazar/", {"comentario": "Hay en bodega"})
        self.assertEqual(r.data["estado"], "RECHAZADA")

    def test_filtro_por_estado(self):
        self.crear()
        self.assertEqual(len(self.como(self.lider).get("/api/insumos/?estado=PENDIENTE").data), 1)
        self.assertEqual(len(self.como(self.lider).get("/api/insumos/?estado=APROBADA,ENTREGADA").data), 0)


class InformeTest(CampoBase):
    def setUp(self):
        super().setUp()
        hoy = timezone.localdate()
        inicio = timezone.make_aware(timezone.datetime(hoy.year, hoy.month, hoy.day, 8, 0))
        TimeEntry.objects.create(usuario=self.op, proyecto=self.p1, hora_inicio=inicio,
                                 hora_fin=inicio + timedelta(hours=4, minutes=30))

    def crear(self, **extra):
        data = {"proyecto": self.p1.id, "fecha_servicio": str(timezone.localdate()), "ubicacion": "Planta Norte",
                "actividades": "Mantenimiento preventivo del tablero", "participante_ids": [self.op.id], **extra}
        return self.como(self.op).post("/api/informes/", data, format="json")

    def test_sugerir_personal_desde_tiempos(self):
        r = self.como(self.op).get(f"/api/informes/sugerir-personal/?proyecto={self.p1.id}&fecha={timezone.localdate()}")
        self.assertEqual(r.data, [{"usuario_id": self.op.id, "nombre": "Juan Pérez", "minutos": 270}])

    def test_flujo_completo_con_pdf(self):
        r = self.crear()
        self.assertEqual(r.status_code, status.HTTP_201_CREATED, r.data)
        inf_id = r.data["id"]
        self.como(self.op).post("/api/fotos/", {"informe": inf_id, "archivo": imagen(), "descripcion": "Antes"},
                                format="multipart")
        firma = self.como(self.op).post(f"/api/informes/{inf_id}/firma/", {"imagen": imagen("f.png", "PNG", (600, 200))},
                                        format="multipart")
        self.assertIsNotNone(firma.data["firma_url"])
        self.assertEqual(self.como(self.op).post(f"/api/informes/{inf_id}/enviar/").data["estado"], "ENVIADO")
        # Enviado: el autor ya no edita
        self.assertEqual(self.como(self.op).patch(f"/api/informes/{inf_id}/", {"ubicacion": "x"}).status_code, 403)
        # Devolver y reenviar
        self.assertEqual(self.como(self.lider).post(f"/api/informes/{inf_id}/devolver/").status_code, 400)
        r = self.como(self.lider).post(f"/api/informes/{inf_id}/devolver/", {"comentario": "Agregar foto final"})
        self.assertEqual(r.data["estado"], "DEVUELTO")
        self.assertEqual(self.como(self.op).patch(f"/api/informes/{inf_id}/", {"ubicacion": "Planta Sur"}).status_code, 200)
        self.como(self.op).post(f"/api/informes/{inf_id}/enviar/")
        r = self.como(self.lider).post(f"/api/informes/{inf_id}/aprobar/")
        self.assertEqual(r.status_code, 200, r.data)
        anio = timezone.localdate().year
        self.assertEqual(r.data["consecutivo"], f"INF-{anio}-0001")
        self.api.force_authenticate(user=None)
        pdf = self.api.get(r.data["pdf_url"])
        self.assertEqual(pdf.status_code, 200)
        self.assertTrue(b"".join(pdf.streaming_content).startswith(b"%PDF"))
        # Aprobado: nadie lo edita salvo el admin
        self.assertEqual(self.como(self.lider).patch(f"/api/informes/{inf_id}/", {"ubicacion": "x"}).status_code, 403)

    def test_consecutivo_incrementa(self):
        for _ in range(2):
            inf_id = self.crear().data["id"]
            self.como(self.op).post(f"/api/informes/{inf_id}/enviar/")
            self.como(self.lider).post(f"/api/informes/{inf_id}/aprobar/")
        consecutivos = sorted(InformeServicio.objects.values_list("consecutivo", flat=True))
        self.assertEqual([c[-4:] for c in consecutivos], ["0001", "0002"])

    def test_no_se_envia_sin_actividades(self):
        inf_id = self.crear(actividades="").data["id"]
        self.assertEqual(self.como(self.op).post(f"/api/informes/{inf_id}/enviar/").status_code, 400)

    def test_participante_ve_el_informe(self):
        Assignment.objects.create(usuario=self.op_otro, proyecto=self.p1)
        self.crear(participante_ids=[self.op.id, self.op_otro.id])
        self.assertEqual(len(self.como(self.op_otro).get("/api/informes/").data), 1)
        self.assertEqual(InformeServicio.objects.get().estado, EstadoInforme.BORRADOR)


class NotificacionTest(CampoBase):
    def test_contador_y_marcar_leidas(self):
        Novedad.objects.create(autor=self.op, proyecto=self.p1, titulo="x")
        self.como(self.op).post("/api/novedades/", {"proyecto": self.p1.id, "titulo": "Retraso"})
        self.como(self.op).post("/api/insumos/", {"proyecto": self.p1.id, "detalle": "Guantes"})
        self.assertEqual(self.como(self.lider).get("/api/notificaciones/no-leidas/").data["total"], 2)
        primera = self.como(self.lider).get("/api/notificaciones/").data[0]["id"]
        self.como(self.lider).post("/api/notificaciones/marcar-leidas/", {"ids": [primera]}, format="json")
        self.assertEqual(self.como(self.lider).get("/api/notificaciones/no-leidas/").data["total"], 1)
        self.como(self.lider).post("/api/notificaciones/marcar-leidas/")
        self.assertEqual(self.como(self.lider).get("/api/notificaciones/no-leidas/").data["total"], 0)
        # Cada uno ve solo las suyas
        self.assertEqual(len(self.como(self.op).get("/api/notificaciones/").data), 0)

    def test_mis_proyectos_por_rol(self):
        self.assertEqual([p["nombre"] for p in self.como(self.op).get("/api/campo/proyectos/").data], ["Subestación"])
        self.assertEqual(len(self.como(self.admin).get("/api/campo/proyectos/").data), 2)
