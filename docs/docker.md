# Entorno local con Docker

Este Compose es para desarrollo local. Levanta PostgreSQL y la API; antes de iniciar la API aplica las migraciones de Alembic y carga los datos de ejemplo de `seed.py`. Ese seed contiene contraseñas demostrativas fijas, por lo que no debe usarse en producción.

## Iniciar

Si todavía no tienes un `.env`, copia `.env.example` como `.env` y cambia `SECRET_KEY` y `POSTGRES_PASSWORD`. El archivo `.env` contiene secretos y no se versiona.

```bash
docker compose up --build
```

La API queda disponible en `http://localhost:8000`; su health check está en `http://localhost:8000/health` y la documentación OpenAPI en `http://localhost:8000/docs`. PostgreSQL se publica en el puerto `5432` por defecto. Puedes cambiar esos puertos con `API_PORT` y `POSTGRES_PORT`.

## Pruebas

Compose crea la base `peibo_test` al inicializar el volumen. La suite elimina y reconstruye las tablas de esa base antes de cada prueba; nunca la uses para datos que quieras conservar.

```bash
docker compose run --rm -v ./tests:/app/tests --entrypoint pytest api -q tests/test_usuarios_router.py
```

El servicio de pruebas recibe una URL interna a `db` y apunta a `peibo_test`, separada de la base de desarrollo `peibo_db`.

## Detener y datos

```bash
docker compose down
```

Este comando conserva el volumen `postgres_data`. Para borrar también las bases y todos sus datos, ejecuta `docker compose down -v`; esa operación es destructiva.

El SQL que crea `peibo_test` se ejecuta solo cuando PostgreSQL inicializa un volumen vacío. Si ya tenías un volumen anterior sin esa base, créala manualmente o elimina el volumen únicamente si puedes descartar sus datos.
