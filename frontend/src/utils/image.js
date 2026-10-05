/**
 * Reduce una foto en el navegador antes de subirla (ahorra datos móviles en campo).
 * Lado mayor máximo 1600 px, JPEG al 80 %. Respeta la orientación EXIF del celular.
 * @param {File} file
 * @returns {Promise<Blob>}
 */
export async function compressImage(file, maxSide = 1600, quality = 0.8) {
  const bitmap = await createImageBitmap(file, { imageOrientation: "from-image" }).catch(() => null);
  const source = bitmap || (await loadImage(file));
  const scale = Math.min(1, maxSide / Math.max(source.width, source.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(source.width * scale);
  canvas.height = Math.round(source.height * scale);
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#fff";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(source, 0, 0, canvas.width, canvas.height);
  bitmap?.close?.();
  return new Promise((resolve, reject) =>
    canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("No se pudo procesar la foto."))), "image/jpeg", quality)
  );
}

function loadImage(file) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error("El archivo no es una imagen."));
    img.src = URL.createObjectURL(file);
  });
}
