# Peibo

Peibo es una API REST construida con FastAPI para administrar usuarios y roles, emitir tokens JWT y consultar recursos de Studio Ghibli con permisos basados en el rol del usuario.

## Funcionalidades

- Autenticación de usuarios mediante OAuth2 y tokens Bearer JWT.
- Alta, consulta, búsqueda, actualización parcial y eliminación de usuarios.
- Control de acceso por roles: las operaciones administrativas requieren el rol `admin`.
- Integración con la API pública de Studio Ghibli. Cada rol no administrador puede consultar el recurso asignado; `admin` puede consultar todos.
- Persistencia asíncrona con PostgreSQL y SQLAlchemy, con migraciones administradas por Alembic.

## Requisitos

- Docker con Docker Compose.
- Git, para clonar el repositorio.

## Inicio rápido con Docker

Desde la raíz del repositorio:

```bash
cp .env.example .env
```

Antes de iniciar, genera una clave JWT para el entorno local y asígnala a `SECRET_KEY` en `.env`:

```bash
openssl rand -hex 32
```

Levanta los servicios:

```bash
docker compose up --build
```

Compose inicia PostgreSQL, aplica las migraciones y carga los datos de demostración antes de iniciar la API. Cuando el contenedor esté listo:

- API: <http://localhost:8000>
- Swagger UI: <http://localhost:8000/docs>
- OpenAPI: <http://localhost:8000/openapi.json>
- Health check: <http://localhost:8000/health>

El puerto de la API se puede cambiar con `API_PORT`; PostgreSQL usa `POSTGRES_PORT`. Para detener los servicios sin borrar los datos, ejecuta `docker compose down`. Consulta [docs/docker.md](docs/docker.md) para las variables, pruebas en contenedores y administración del volumen.

## Detener y datos

```bash
docker compose down
```

Este comando conserva el volumen `postgres_data`. Para borrar también las bases y todos sus datos, ejecuta `docker compose down -v`.

## Usuarios de demostración

En una base nueva, el seed crea estos usuarios para desarrollo:

| Usuario          | Contraseña      | Rol           |
| ---------------- | --------------- | ------------- |
| `admin_user`     | `admin1234`     | Administrador |
| `films_user`     | `films1234`     | Films         |
| `people_user`    | `people1234`    | People        |
| `locations_user` | `locations1234` | Locations     |
| `species_user`   | `species1234`   | Species       |
| `vehicles_user`  | `vehicles1234`  | Vehicles      |

Son credenciales públicas de demostración: no reutilizarlas fuera del entorno local ni en producción. El seed no cambia la contraseña de un usuario que ya exista.

## Ejemplo de autenticación

El endpoint de token recibe campos de formulario, no JSON:

```bash
curl -X POST http://localhost:8000/api/v1/usuarios/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin_user&password=admin1234'
```

Usa el `access_token` de la respuesta en las rutas protegidas:

```bash
curl http://localhost:8000/api/v1/usuarios/me \
  -H 'Authorization: Bearer <access_token>'
```

Consulta [docs/endpoints.md](docs/endpoints.md) para todos los endpoints, permisos, cuerpos y respuestas. La descripción funcional y técnica está en [docs/arquitectura.md](docs/arquitectura.md).

## Pruebas

Las pruebas requieren PostgreSQL y usan exclusivamente una base llamada `peibo_test`, que se limpia y reconstruye durante la suite. No configures esa URL con una base que contenga datos que deban conservarse. Consulta la [guía de pruebas](docs/testing-usuarios.md)
