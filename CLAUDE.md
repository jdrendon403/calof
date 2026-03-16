# CLAUDE.md — Contexto del Proyecto SGTP

Sistema de Gestión de Tiempos y Proyectos para una empresa de servicios de ingeniería.
Arquitectura desacoplada: REST API (Django) + SPA (React).

---

## Estructura de directorios

```
calof/
├── backend/          # Django REST API
│   ├── config/       # Settings, URLs raíz, config Celery
│   ├── users/        # App: modelo Usuario, auth, permisos
│   ├── projects/     # App: modelos Project, Assignment
│   ├── timetracker/  # App: modelo TimeEntry, tareas Celery
│   ├── reports/      # App: endpoint de liquidación
│   ├── manage.py
│   └── requirements.txt
├── frontend/         # React SPA
│   ├── src/
│   │   ├── api/      # client.js (axios + interceptors)
│   │   ├── context/  # AuthContext, TimeContext
│   │   ├── pages/    # LoginView, DashboardOperario, DashboardLider, AdminPanel
│   │   └── components/ # Layout (nav + header)
│   ├── package.json
│   └── vite.config.js
└── docker-compose.yml
```

---

## Stack tecnológico

| Capa | Tecnología | Versión |
|------|-----------|---------|
| Backend framework | Django + DRF | 4.2 / 3.14+ |
| Autenticación | djangorestframework-simplejwt | 5.3 |
| Base de datos | PostgreSQL | 15 |
| Cache / Broker | Redis | 7 |
| Tareas async | Celery + django-celery-beat | 5.3 / 2.5 |
| Docs API | drf-spectacular (Redoc) | 0.27 |
| Frontend framework | React | 18.2 |
| Build tool | Vite | 5.0 |
| Routing | React Router DOM | 6.21 |
| HTTP client | Axios | 1.6 |
| Estilos | Tailwind CSS | 3.4 |
| Gráficos | Recharts | 2.10 |
| State management | React Context API | — |

---

## Modelos de datos

```
Usuario (CustomUser extends AbstractUser)
  - id, username, email, password, first_name, last_name
  - rol: ADMIN | LIDER | OPERARIO
  - telefono
  - property: is_project_leader → True si ADMIN o LIDER

Project
  - id, nombre, descripcion, cliente
  - estado: ABIERTO | CERRADO
  - fecha_inicio, fecha_fin
  - usuarios_asignados (M2M → Usuario via Assignment)

Assignment  [tabla intermedia]
  - usuario_id → Usuario
  - proyecto_id → Project
  - fecha_programada
  - unique_together: [usuario, proyecto]

TimeEntry
  - usuario_id → Usuario
  - proyecto_id → Project
  - hora_inicio (DateTimeField)
  - hora_fin (DateTimeField, null=True)  ← null = entrada activa
  - cierre_automatico (BooleanField)
  - property: duracion_minutos (calculada si hora_fin existe)
```

---

## API Endpoints

```
# Autenticación
POST   /api/auth/login/          → { access, refresh, user, rol }
POST   /api/auth/refresh/
GET    /api/auth/me/

# Usuarios (Admin only)
GET|POST        /api/users/
GET|PATCH|DELETE /api/users/{id}/

# Proyectos
GET|POST        /api/projects/
GET|PATCH|DELETE /api/projects/{id}/
POST   /api/projects/{id}/assign-users/
POST   /api/projects/{id}/unassign-user/
GET    /api/projects/assignments/         ← Lider/Admin only

# Tiempos
POST   /api/time/start/          → crea TimeEntry con hora_fin=null
PATCH  /api/time/stop/           → cierra entrada activa
GET    /api/time/current/        → entrada activa del usuario
GET    /api/time/                → lista (Operario: propia; Lider/Admin: todas)

# Reportes
GET    /api/reports/settlement/?period=week|month

# Docs
GET    /api/docs/                → Redoc
GET    /api/schema/              → OpenAPI
GET    /admin/                   → Django Admin
```

---

## Roles y permisos (RBAC)

| Acción | OPERARIO | LIDER | ADMIN |
|--------|:--------:|:-----:|:-----:|
| Ver/registrar sus propios tiempos | ✓ | ✓ | ✓ |
| Ver tiempos de todos los usuarios | — | ✓ | ✓ |
| CRUD proyectos | — | ✓ | ✓ |
| Asignar/desasignar usuarios | — | ✓ | ✓ |
| Ver reportes de liquidación | — | ✓ | ✓ |
| CRUD usuarios | — | — | ✓ |

**Permission classes del backend:** `IsAdminUser`, `IsProjectLeader`, `IsProjectLeaderOrReadOnly`

**Operario** solo ve proyectos a los que está asignado (filtrado en queryset).

---

## Autenticación JWT

- **Access token lifetime:** 60 minutos
- **Refresh token lifetime:** 1 día
- Tokens guardados en `localStorage` (keys: `access`, `refresh`)
- **Interceptor de request:** agrega `Authorization: Bearer {access}` automáticamente
- **Interceptor de response:** en 401 → intenta refresh → si falla, logout + redirect `/login`

---

## Tareas programadas (Celery Beat)

Timezone configurado en `America/Bogota`.

| Tarea | Hora | Descripción |
|-------|------|-------------|
| `close-sessions-5pm` | 17:00 | Cierra todas las entradas activas |
| `close-sessions-midnight` | 00:00 | Cierre de seguridad nocturno |

Lógica: busca `TimeEntry` donde `hora_fin=null` → asigna `hora_fin=at_time` + `cierre_automatico=True`.

---

## Frontend: páginas y rutas

| Ruta | Componente | Roles permitidos |
|------|-----------|-----------------|
| `/login` | LoginView | público |
| `/operario` | DashboardOperario | OPERARIO, LIDER, ADMIN |
| `/lider` | DashboardLider | LIDER, ADMIN |
| `/admin` | AdminPanel | ADMIN |
| `/` | RoleRedirect | redirige según rol |

**PrivateRoute:** bloquea acceso sin token; valida rol antes de renderizar.

---

## Frontend: state management

**AuthContext**
- Estado: `user` (objeto con id, username, rol, etc.), `loading`
- Funciones: `login(data)`, `logout()`, `refreshUser()`

**TimeContext**
- Estado: `activeEntry`, `elapsedSeconds` (incrementa cada 1s con `setInterval`)
- Funciones: `start(projectId)`, `stop()`, `fetchCurrent()`, `formatElapsed(seconds)`

---

## Comunicación frontend → backend

En desarrollo: Vite proxea `/api` → `http://localhost:8000` (configurado en `vite.config.js`).
En producción: requiere nginx o reverse proxy que enrute `/api` al contenedor Django.

---

## Servicios Docker Compose

| Servicio | Imagen | Puerto | Depende de |
|----------|--------|--------|------------|
| `db` | postgres:15-alpine | 5432 | — |
| `redis` | redis:7-alpine | 6379 | — |
| `web` | Dockerfile backend | 8000 | db, redis |
| `celery_worker` | Dockerfile backend | — | web, redis |
| `celery_beat` | Dockerfile backend | — | celery_worker, redis |

### Variables de entorno relevantes

```
DATABASE_URL=postgres://sgtp:sgtp_secret@db:5432/sgtp
SECRET_KEY=change-me-in-production
REDIS_URL=redis://redis:6379/0
DEBUG=1
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

---

## Cómo levantar el proyecto

```bash
# Con Docker (recomendado)
docker-compose up --build
# Crear superusuario
docker-compose exec web python manage.py createsuperuser

# Frontend en modo desarrollo (sin Docker)
cd frontend && npm install && npm run dev   # puerto 3000

# Tests backend
cd backend && python manage.py test
```

---

## Roadmap del producto

| Fase | Estado | Descripción |
|------|--------|-------------|
| MVP | ✅ Implementado | Web con gestión de tiempos básica |
| Fase 2 | Pendiente | Liquidación avanzada + exportar PDF/Excel |
| Fase 3 | Pendiente | App móvil nativa (Android/iOS) |

---

## Convenciones del proyecto

- **Idioma del código:** español para nombres de modelos y campos del dominio de negocio (`hora_inicio`, `cierre_automatico`, `usuarios_asignados`). Inglés para código de infraestructura.
- **Idioma de la UI:** español (Colombia), `LANGUAGE_CODE = 'es-co'`
- **Zona horaria:** `America/Bogota` en backend y Celery
- **Colores de UI:** paleta `slate` de Tailwind CSS
- El campo `hora_fin = null` en `TimeEntry` indica que la sesión está **activa/corriendo**
- El flag `cierre_automatico = True` identifica entradas cerradas por el sistema (no por el usuario)
