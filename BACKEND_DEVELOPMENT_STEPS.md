🚀 Guía de Desarrollo Backend: Sistema de Gestión de Tiempos
Este documento detalla la hoja de ruta técnica para la implementación del backend utilizando Django y Django REST Framework.

🏗️ Fase 1: Configuración del Entorno y Base
Entorno Virtual: Crear y activar un venv.

Instalación de Dependencias:

django, djangorestframework, django-cors-headers, djangorestframework-simplejwt.

App de Usuarios (users):

Definir el modelo Usuario(AbstractUser) con el campo rol.

Configurar AUTH_USER_MODEL = 'users.Usuario' en settings.py.

Seguridad y CORS:

Configurar corsheaders para permitir peticiones desde el dominio de React.

Configurar REST_FRAMEWORK para usar JWTAuthentication.

🗂️ Fase 2: Definición del Modelo de Negocio (Core)
App de Proyectos (projects):

Modelo Proyecto: campos para nombre, descripción y estado activo.

Modelo Planificacion: para asignar fechas de trabajo futuras.

App de Tiempos (timetracker):

Modelo RegistroTiempo: Relaciona usuario, proyecto y almacena hora_inicio, hora_fin y cierre_automatico.

Migraciones: Ejecutar makemigrations y migrate para reflejar los cambios en la base de datos.

🔌 Fase 3: Desarrollo de la API (Endpoints)
Serializers: Crear clases que transformen los modelos en JSON.

Endpoints para Operarios:

POST /api/tiempos/iniciar/: Crea un nuevo registro si no hay uno activo.

POST /api/tiempos/finalizar/: Actualiza la hora_fin del registro actual.

Endpoints para Líder/Admin:

CRUD completo de usuarios y proyectos.

Endpoint para asignar operarios a proyectos específicos.

🤖 Fase 4: Lógica de Automatización (Cierre de las 5 PM)
Comando Personalizado: Crear management/commands/close_sessions.py.

Lógica del Script: * Buscar registros donde hora_fin sea null.

Asignar la hora de corte (17:00 o 00:00).

Marcar cierre_automatico = True.

Programación (Cron): Configurar el servidor para ejecutar este comando automáticamente en las horas establecidas.

📊 Fase 5: Módulo de Liquidación y Reportes
Consultas de Agregación: Utilizar el ORM de Django (Sum, Count) para calcular horas totales por usuario y proyecto.

Filtros: Implementar django-filter para permitir búsquedas por rangos de fechas (día, semana, mes, quincena).

Vistas de Reporte: Crear endpoints específicos que devuelvan la "liquidación" lista para ser consumida por el frontend.

🧪 Fase 6: Pruebas y Documentación
Tests Unitarios: Validar que los cálculos de horas sean correctos.

Pruebas de Permisos: Asegurar que un "Operario" no pueda acceder a los endpoints de "Administrador".

Swagger/OpenAPI: Configurar drf-spectacular para generar la documentación interactiva de la API.