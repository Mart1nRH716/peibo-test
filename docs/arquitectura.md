# Arquitectura

## Resumen

Peibo separa la exposición HTTP, la lógica de negocio, el acceso a datos y los esquemas de validación. FastAPI registra los routers bajo `/api/v1`; PostgreSQL almacena usuarios y roles, y el servicio de Ghibli consulta una API externa.

## Componentes

- `app/main.py`: crea la aplicación FastAPI, registra los routers y expone `/health`.
- `app/routers/`: define los endpoints de usuarios y de Studio Ghibli, valida dependencias y traduce errores de servicio a respuestas HTTP.
- `app/services/`: contiene autenticación y reglas de negocio de usuarios, además de la integración HTTP con Studio Ghibli.
- `app/repositories/`: concentra las consultas y escrituras de SQLAlchemy.
- `app/models/`: declara los modelos ORM `Usuario` y `Rol`.
- `app/schemas/`: define los cuerpos de entrada y las respuestas mediante Pydantic.
- `app/security.py` y `app/utils/security_utils.py`: implementan validación de JWT, usuarios activos y permisos por rol.
- `alembic/`: conserva el historial de migraciones del esquema de PostgreSQL.

## Datos y persistencia

La base contiene el catálogo `cat_rol` y la tabla `tb_usuario`. Cada usuario tiene un username y email únicos, una contraseña almacenada como hash, un rol y un indicador de actividad. Las contraseñas no se exponen en las respuestas de la API.

La aplicación utiliza SQLAlchemy asíncrono con `asyncpg`. La configuración se carga desde variables de entorno y el archivo `.env`. En Compose, el servicio `migrate-seed` espera a que PostgreSQL esté listo, ejecuta `alembic upgrade head` y después carga los datos demostrativos con `seed.py`; la API inicia una vez termina ese servicio.

## Autenticación y autorización

El endpoint de token autentica username y password y entrega un JWT firmado con el algoritmo configurado. Las rutas protegidas esperan el token en la cabecera `Authorization: Bearer ...` y validan que el usuario siga activo.

El rol `admin` puede crear, modificar y eliminar usuarios y consultar todos los recursos de Ghibli. Cada rol de recurso (`films`, `people`, `locations`, `species` y `vehicles`) puede acceder únicamente al recurso homónimo. Los roles y sus IDs se definen en `app/schemas/enum.py`.

## Integración con Studio Ghibli

El servicio `GhibliService` realiza peticiones HTTP asíncronas a `https://ghibliapi.vercel.app`, con un timeout de 10 segundos. Valida el nombre del recurso antes de llamar al proveedor y limita las consultas de colección a 100 elementos. Los errores del proveedor se traducen a `404` para elemento inexistente o `502` para errores HTTP o de conexión.

## Configuración y ejecución

La plantilla `.env.example` y `docs/docker.md` describen la configuración local. Compose publica la API y PostgreSQL, conserva los datos en el volumen `postgres_data` y crea una base separada `peibo_test` para las pruebas. La suite de tests elimina y crea de nuevo las tablas de esa base; no debe apuntarse a datos que se quieran conservar.

El entorno documentado es para desarrollo local. El seed contiene contraseñas demostrativas fijas y no debe utilizarse como mecanismo de inicialización de producción.
