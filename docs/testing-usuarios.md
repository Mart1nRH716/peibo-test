# Pruebas de endpoints de usuarios

Las pruebas de API usan `TestClient` de forma síncrona y sobreescriben `get_db` con una sesión `AsyncSession`. Requieren PostgreSQL y usan exclusivamente una base llamada `peibo_test`; la fixture rechaza cualquier otro nombre antes de importar la aplicación.

## Preparar la base local

Instala las dependencias de prueba en el entorno virtual del proyecto:

```bash
pip install pytest httpx
```

Crea la base de pruebas con el usuario PostgreSQL local:

```sql
CREATE DATABASE peibo_test;
```

Define la URL de conexión antes de ejecutar pytest. Usa el mismo formato `postgresql+asyncpg` que usa la aplicación, pero apunta a `peibo_test`:

```bash
export TEST_DATABASE_URL="postgresql+asyncpg://usuario:contraseña@localhost:5432/peibo_test"
```

Luego ejecuta:

```bash
pytest -q tests/test_usuarios_router.py
```

La fixture crea el esquema y los roles necesarios al inicio de cada prueba. No ejecutes `seed.py` para esta base. La suite elimina y vuelve a crear sus tablas; no apuntes `TEST_DATABASE_URL` a una base con datos que quieras conservar.

La integración de estas pruebas en GitHub Actions queda pendiente para una fase posterior.
