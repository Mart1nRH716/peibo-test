# Pruebas de endpoints de usuarios

Para las pruebas se requiere de PostgreSQL y usan exclusivamente una base llamada `peibo_test`. La fixture rechaza cualquier otro nombre antes de importar la aplicación.

## Ejecutar pruebas desde el contenedor

Compose crea la base `peibo_test` al inicializar el volumen. La suite elimina y reconstruye las tablas de esa base antes de cada prueba; nunca la uses para datos que quieras conservar.

```bash
docker compose run --rm \
  -v ./tests:/app/tests \
  --workdir /app \
  --entrypoint python \
  api -m pytest -q tests/
```

## Pruebas locales

Si se quieren realizar las pruebas en local, se tiene que crear la base de pruebas con el usuario PostgreSQL local:

```sql
CREATE DATABASE peibo_test;
```

Define la URL de conexión antes de ejecutar pytest. Usa el mismo formato `postgresql+asyncpg` que usa la aplicación, pero apunta a `peibo_test`:

```bash
export TEST_DATABASE_URL="postgresql+asyncpg://usuario:contraseña@localhost:5432/peibo_test"
```

Luego ejecuta:

```bash
py -m pytest
```
