"""
Fotos y archivos privados.

- Las fotos se normalizan al subirlas: se corrige la orientación, se reducen a 1600 px y se
  guardan como JPEG nuevo, lo que descarta los metadatos EXIF (incluida la ubicación GPS).
- Ningún archivo se publica en una URL fija. La API entrega enlaces firmados que vencen
  (`url_firmada`), porque las etiquetas <img> no pueden enviar el token JWT.
"""
import mimetypes
from io import BytesIO

from django.conf import settings
from django.core import signing
from django.core.files.base import ContentFile
from django.http import FileResponse, Http404, HttpResponse
from PIL import Image, ImageOps, UnidentifiedImageError
from rest_framework import serializers

MAX_BYTES = 10 * 1024 * 1024
LADO_MAX = 1600
LADO_MINIATURA = 400
SALT = "campo.archivos"
VIGENCIA_SEGUNDOS = 12 * 3600


def _a_jpeg(img, lado):
    copia = img.copy()
    copia.thumbnail((lado, lado))
    buf = BytesIO()
    copia.save(buf, "JPEG", quality=82, optimize=True)
    return ContentFile(buf.getvalue())


def procesar_foto(archivo):
    """Valida la imagen y devuelve (foto, miniatura) como ContentFile JPEG sin metadatos."""
    if archivo.size > MAX_BYTES:
        raise serializers.ValidationError("La foto supera el tamaño máximo de 10 MB.")
    try:
        img = Image.open(archivo)
        img.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise serializers.ValidationError("El archivo no es una imagen válida.")
    img = ImageOps.exif_transpose(img)
    if img.mode != "RGB":
        fondo = Image.new("RGB", img.size, "white")
        fondo.paste(img.convert("RGBA"), mask=img.convert("RGBA").split()[-1])
        img = fondo
    return _a_jpeg(img, LADO_MAX), _a_jpeg(img, LADO_MINIATURA)


def procesar_firma(archivo):
    """La firma llega como PNG desde el canvas; se valida y se vuelve a guardar."""
    if archivo.size > 2 * 1024 * 1024:
        raise serializers.ValidationError("La imagen de la firma es demasiado grande.")
    try:
        img = Image.open(archivo)
        img.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise serializers.ValidationError("La firma no es una imagen válida.")
    img.thumbnail((1200, 600))
    buf = BytesIO()
    img.convert("RGBA").save(buf, "PNG", optimize=True)
    return ContentFile(buf.getvalue())


def url_firmada(campo_archivo):
    """Enlace temporal a un archivo guardado (FieldFile) o None si no hay archivo."""
    if not campo_archivo:
        return None
    token = signing.dumps(campo_archivo.name, salt=SALT, compress=True)
    # Ruta relativa: el navegador la resuelve contra el mismo dominio (evita mezclar http/https tras el túnel).
    return f"/api/archivos/{token}/"


def servir(request, token):
    try:
        nombre = signing.loads(token, salt=SALT, max_age=VIGENCIA_SEGUNDOS)
    except signing.BadSignature:
        raise Http404
    ruta = (settings.MEDIA_ROOT / nombre).resolve()
    if settings.MEDIA_ROOT.resolve() not in ruta.parents or not ruta.is_file():
        raise Http404
    tipo = mimetypes.guess_type(ruta.name)[0] or "application/octet-stream"
    if settings.MEDIA_X_ACCEL:
        resp = HttpResponse(content_type=tipo)
        resp["X-Accel-Redirect"] = f"/protected/{nombre}"
    else:
        resp = FileResponse(open(ruta, "rb"), content_type=tipo)
    resp["Cache-Control"] = "private, max-age=3600"
    if tipo == "application/pdf":
        descarga = request.GET.get("nombre", "informe.pdf").replace('"', "")
        resp["Content-Disposition"] = f'inline; filename="{descarga}"'
    return resp
