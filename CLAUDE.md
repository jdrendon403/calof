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
│   ├── cuadrillas/   # App: modelo Cuadrilla, servicios de trabajo colectivo
│   ├── manage.py
│   └── requirements.txt
├── frontend/         # React SPA
│   ├── src/
│   │   ├── api/        # client.js (axios + interceptors)
│   │   ├── context/    # AuthContext, TimeContext
│   │   ├── pages/      # LoginView, DashboardOperario, DashboardLider, AdminPanel
│   │   ├── components/ # Layout, CuadrillaManager
│   │   └── utils/      # time.js (minutesToHHMM)
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
| Build tool | Vite | 5.0 (usePolling=true para Docker en Windows) |
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

Assignment  [tabla intermedia Project ↔ Usuario]
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
  - cuadrilla_id → Cuadrilla (FK, null=True)  ← null = entrada individual
  - property: duracion_minutos (calculada si hora_fin existe)

Cuadrilla
  - id, nombre
  - proyecto_id → Project (FK)
  - lider_id → Usuario (FK, rol LIDER o ADMIN)
  - miembros (M2M → Usuario)
  - activa (BooleanField, default=True)
  - fecha_creacion (DateTimeField, auto)
```

---

## API Endpoints

```
# Autenticación
POST   /api/auth/login/          → { access, refresh, user, rol }  ← máx. 5/min por usuario y 20/min por IP
POST   /api/auth/refresh/
GET    /api/auth/me/
POST   /api/auth/change-password/ → { current_password, new_password } (usuario autenticado)

# Usuarios
GET|POST         /api/users/              ← GET: Lider/Admin | POST: Admin only
GET|PATCH|DELETE /api/users/{id}/         ← Admin only

# Proyectos
GET|POST        /api/projects/
GET|PATCH|DELETE /api/projects/{id}/
POST   /api/projects/{id}/assign-users/
POST   /api/projects/{id}/unassign-user/
GET    /api/projects/assignments/         ← Lider/Admin only

# Tiempos (individuales)
POST   /api/time/start/          → crea TimeEntry con hora_fin=null
PATCH  /api/time/stop/           → cierra entrada activa del usuario
GET    /api/time/current/        → entrada activa del usuario
GET    /api/time/                → lista (Operario: propia; Lider/Admin: todas)

# Cuadrillas
GET|POST        /api/cuadrillas/
GET|PATCH       /api/cuadrillas/{id}/
POST   /api/cuadrillas/{id}/add-members/
POST   /api/cuadrillas/{id}/remove-member/
POST   /api/cuadrillas/{id}/start/    → crea TimeEntry para todos los miembros
POST   /api/cuadrillas/{id}/stop/     → cierra entradas activas de la cuadrilla
GET    /api/cuadrillas/{id}/current/  → estado activo de la cuadrilla

# Reportes
GET    /api/reports/settlement/?period=week|month
       → incluye entradas activas (hora_fin=null) usando now() como cierre temporal
       → responde: { por_usuario: [{nombre_completo, total_minutos}], por_proyecto: [...] }

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
| Listar usuarios | — | ✓ | ✓ |
| CRUD proyectos | — | ✓ | ✓ |
| Asignar/desasignar usuarios a proyectos | — | ✓ | ✓ |
| Ver reportes de liquidación | — | ✓ | ✓ |
| Crear/gestionar cuadrillas | — | ✓ | ✓ |
| Iniciar/detener cuadrilla | miembro | lider | ✓ |
| CRUD usuarios | — | — | ✓ |

**Permission classes del backend:** `IsAdminUser`, `IsProjectLeader`, `IsProjectLeaderOrReadOnly`

**Operario** solo ve proyectos a los que está asignado (filtrado en queryset).

---

## Módulo de Cuadrillas

- Un **Líder** crea una cuadrilla, asigna un proyecto y matricula operarios.
- Cualquier **miembro o el líder** puede iniciar/detener el trabajo de toda la cuadrilla.
- Al iniciar: se crea un `TimeEntry` para cada miembro con el **mismo** `hora_inicio` (transacción atómica).
- Miembros con sesión individual activa se **omiten** (no fallan); la API reporta `skipped_user_ids`.
- Al detener: cierra todos los `TimeEntry` activos con `cuadrilla_id` de esa cuadrilla.
- El cierre automático de Celery (17:00 y 00:00) aplica igual a entradas de cuadrilla.
- Lógica de negocio aislada en `cuadrillas/services.py` (`cuadrilla_start`, `cuadrilla_stop`, `cuadrilla_current_status`).

---

## Autenticación JWT

- **Access token lifetime:** 60 minutos
- **Refresh token lifetime:** 1 día
- Tokens guardados en `localStorage` (keys: `access`, `refresh`)
- **Interceptor de request:** agrega `Authorization: Bearer {access}` automáticamente
- **Interceptor de response:** en 401 → intenta refresh → si falla, logout + redirect `/login`

---

## Tareas programadas (Celery Beat)

Timezone: `America/Bogota`. Los crontabs se definen en **hora local** (Celery respeta `CELERY_TIMEZONE`).

| Tarea | Hora Bogotá | Hora UTC | Descripción |
|-------|------------|----------|-------------|
| `close-sessions-5pm` | 17:00 | 22:00 | Cierra todas las entradas activas |
| `close-sessions-midnight` | 00:00 | 05:00 | Cierre de seguridad nocturno |

Lógica: busca `TimeEntry` donde `hora_fin=null` → asigna `hora_fin=timezone.now()` + `cierre_automatico=True`.

**Importante:** los crontabs usan la hora local Bogotá directamente (`hour=17`, `hour=0`). No convertir a UTC manualmente.

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
- Estado: `user` (objeto con id, username, rol, first_name, last_name, etc.), `loading`
- Funciones: `login(data)`, `logout()`, `refreshUser()`

**TimeContext**
- Estado: `activeEntry`, `elapsedSeconds` (incrementa cada 1s con `setInterval`)
- Funciones: `start(projectId)`, `stop()`, `fetchCurrent()`, `formatElapsed(seconds)`
- Re-ejecuta `fetchCurrent()` cuando `user` cambia (detecta sesión activa al login)

**Utilidades**
- `src/utils/time.js` → `minutesToHHMM(minutes)`: convierte minutos a formato `HH:MM`

---

## Frontend: componentes clave

| Componente | Descripción |
|-----------|-------------|
| `Layout.jsx` | Header con logo InControl, nav por rol, nombre del usuario, logout |
| `DashboardOperario.jsx` | Timer individual + sección modo cuadrilla (visible si pertenece a alguna) |
| `DashboardLider.jsx` | Liquidación, gráfica (polling 30s), proyectos, cuadrillas, registros |
| `CuadrillaManager.jsx` | CRUD cuadrillas, gestión de miembros (usado dentro de DashboardLider) |
| `AdminPanel.jsx` | CRUD usuarios |

---

## Reportes: comportamiento

- Incluye entradas **activas** (`hora_fin=null`) usando `now()` como cierre temporal → no se excluyen.
- Campo `nombre_completo` = `first_name + last_name` con fallback a `username`.
- La gráfica de barras calcula duración de entradas activas en el frontend: `(Date.now() - hora_inicio) / 60000`.
- El dashboard del líder hace **polling cada 30 segundos** para refrescar tiempos y liquidación.

---

## Comunicación frontend → backend

En desarrollo: Vite proxea `/api` → `http://web:8000` (nombre del servicio Docker).
`vite.config.js` lee `VITE_API_URL` del entorno; fallback a `http://localhost:8000`.
`usePolling: true` en Vite para detectar cambios de archivos en Docker sobre Windows/WSL2.

En producción: requiere nginx o reverse proxy que enrute `/api` al contenedor Django.

**ALLOWED_HOSTS del backend** debe incluir `web` para que el proxy de Vite funcione:
```
ALLOWED_HOSTS=localhost,127.0.0.1,web
```

---

## Servicios Docker Compose

| Servicio | Imagen | Puerto | Depende de |
|----------|--------|--------|------------|
| `db` | postgres:15-alpine | 5432 | — |
| `redis` | redis:7-alpine | 6379 | — |
| `web` | Dockerfile backend | 8000 | db, redis |
| `celery_worker` | Dockerfile backend | — | web, redis |
| `celery_beat` | Dockerfile backend | — | celery_worker, redis |
| `frontend` | Dockerfile frontend | 3000 | web |

El backend corre con usuario no-root (`appuser`) para evitar el warning de Celery.
`celery_beat` usa `--schedule=/tmp/celerybeat-schedule` para evitar conflictos de permisos con el volumen montado.

### Variables de entorno relevantes

```
DATABASE_URL=postgres://sgtp:sgtp_secret@db:5432/sgtp
SECRET_KEY=change-me-in-production
REDIS_URL=redis://redis:6379/0
DEBUG=1
CORS_ALLOWED_ORIGINS=http://localhost:3000
ALLOWED_HOSTS=localhost,127.0.0.1,web
VITE_API_URL=http://web:8000
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
| MVP | ✅ | Web con gestión de tiempos básica |
| Cuadrillas | ✅ | Trabajo colectivo coordinado por cuadrillas |
| Fase 2 | Pendiente | Liquidación avanzada + exportar PDF/Excel |
| Fase 3 | Pendiente | App móvil nativa (Android/iOS) |

---

## Convenciones del proyecto

- **Idioma del código:** español para modelos y campos del dominio (`hora_inicio`, `cierre_automatico`, `usuarios_asignados`, `nombre_completo`). Inglés para infraestructura.
- **Idioma de la UI:** español (Colombia), `LANGUAGE_CODE = 'es-co'`
- **Zona horaria:** `America/Bogota` en backend y Celery. Todos los `DateTimeField` se almacenan en UTC.
- **Colores de UI:** paleta `slate` de Tailwind CSS
- **Formato de tiempos en UI:** `HH:MM` via `minutesToHHMM()` — nunca mostrar minutos crudos
- `hora_fin = null` en `TimeEntry` → sesión **activa**
- `cierre_automatico = True` → entrada cerrada por el sistema
- `cuadrilla = null` en `TimeEntry` → entrada **individual** (no de cuadrilla)
- **Git:** repositorio privado `calof` en GitHub. Usuario: Juan David Rendon (jdrendon@gmail.com)
