# Sistema de Gestión de Tiempos y Proyectos (SGTP) - Ingeniería

## 📌 Propósito del Proyecto
Aplicación integral para la gestión de personal y seguimiento de tiempos en proyectos de servicios de ingeniería. Permite controlar la disponibilidad de mano de obra, liquidar tiempos trabajados y programar asignaciones futuras.

## 🏗️ Arquitectura General
El sistema utiliza una arquitectura desacoplada:
- **Backend:** API REST construida con Django & Django REST Framework (DRF).
- **Frontend Web:** Aplicación SPA (Single Page Application) con React.
- **Base de Datos:** PostgreSQL (Recomendado para producción).
- **Tareas Programadas:** Script de cierre automático de jornadas (5:00 PM / Media noche).

## 👥 Roles y Permisos
- **Administrador:** Gestión total de usuarios (CRUD) y acceso a toda la información.
- **Líder:** Creación de proyectos, asignación de personal, planeación y liquidación de reportes. Gestión de cuadrillas.
- **Operario:** Marcación de inicio/fin de actividades (individual o como parte de una cuadrilla) y consulta de historial personal.

## 👷 Módulo de Cuadrillas
Las cuadrillas permiten agrupar operarios en equipos de trabajo coordinados:
- Un **Líder** crea una cuadrilla, le asigna un proyecto y matricula operarios como miembros.
- Cualquier miembro de la cuadrilla puede **iniciar o detener** el trabajo de toda la cuadrilla con una sola acción.
- Al iniciar, se crea automáticamente un `TimeEntry` para **cada miembro** con el mismo `hora_inicio`.
- Al detener, se cierran todos los registros activos de la cuadrilla simultáneamente.
- El cierre automático de jornada (5 PM / medianoche) aplica igual a entradas individuales y de cuadrilla.
- Un operario puede pertenecer a múltiples cuadrillas pero solo puede tener **una sesión activa** a la vez.

### Endpoints de Cuadrillas
| Método | URL | Descripción | Roles |
|--------|-----|-------------|-------|
| GET/POST | `/api/cuadrillas/` | Listar / Crear | LIDER, ADMIN |
| GET/PATCH | `/api/cuadrillas/{id}/` | Detalle / Actualizar | LIDER (propia), ADMIN |
| POST | `/api/cuadrillas/{id}/add-members/` | Agregar miembros | LIDER (propia), ADMIN |
| POST | `/api/cuadrillas/{id}/remove-member/` | Quitar miembro | LIDER (propia), ADMIN |
| POST | `/api/cuadrillas/{id}/start/` | Iniciar trabajo de cuadrilla | Miembro o Líder |
| POST | `/api/cuadrillas/{id}/stop/` | Detener trabajo de cuadrilla | Miembro o Líder |
| GET | `/api/cuadrillas/{id}/current/` | Estado activo actual | Miembro o Líder |

## 🚀 Hoja de Ruta (Roadmap)
1. MVP: Aplicación Web con gestión de tiempos básica. ✅
2. Módulo de Cuadrillas: trabajo colectivo coordinado. ✅
3. Fase 2: Módulo de liquidación avanzada y reportes PDF/Excel.
4. Fase 3: Aplicación móvil nativa (Android/iOS).

## Cómo ejecutar

### Con Docker (recomendado)
1. Copiar `.env.example` a `.env` y ajustar variables si es necesario.
2. `docker-compose up --build`
3. Backend: http://localhost:8000
4. Crear superusuario: `docker-compose exec web python manage.py createsuperuser`

### Frontend (desarrollo)
1. `cd frontend && npm install && npm run dev`
2. Frontend: http://localhost:3000 (proxy a API en 8000)

### Tests
- Backend: `cd backend && python manage.py test`
- Cobertura de: cálculos de tiempo, permisos (Operario vs Admin), comando close_sessions, reportes de liquidación.

## Despliegue (producción)
- Configurar `ALLOWED_HOSTS`, `SECRET_KEY`, `DEBUG=0`, `DATABASE_URL` y `CORS_ALLOWED_ORIGINS` en el entorno.
- Servir estáticos: `python manage.py collectstatic`.
- Usar un servidor ASGI/WSGI (gunicorn/uvicorn) y proxy inverso (nginx).
- Celery worker y beat deben estar en ejecución para el cierre automático de sesiones (17:00 y 00:00).
- Documentación API: `/api/docs/` (Redoc) y `/api/schema/` (OpenAPI).