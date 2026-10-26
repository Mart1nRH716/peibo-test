# Referencia de endpoints

La API usa el prefijo `/api/v1`. Las respuestas y errores se serializan como JSON, salvo el inicio de sesión, que recibe datos de formulario.

## Autenticación

### Obtener un token

`POST /api/v1/usuarios/token`

Recibe `username` y `password` como `application/x-www-form-urlencoded`. No requiere token. Responde `200` con:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

Credenciales incorrectas responden `401`. Para las rutas protegidas, envía el token así:

```http
Authorization: Bearer <access_token>
```

### Consultar el perfil propio

`GET /api/v1/usuarios/me`

Requiere un usuario autenticado y activo. Responde `200` con el perfil del usuario actual.

## Usuarios

| Método   | Ruta                             | Acceso                                 | Descripción                                  |
| -------- | -------------------------------- | -------------------------------------- | -------------------------------------------- |
| `POST`   | `/api/v1/usuarios/crear-usuario` | Solo `admin`                           | Crea un usuario. Responde `201`.             |
| `GET`    | `/api/v1/usuarios/`              | Cualquier usuario autenticado y activo | Lista usuarios; permite buscar por username. |
| `GET`    | `/api/v1/usuarios/{id_usuario}`  | Cualquier usuario autenticado y activo | Consulta un usuario por ID.                  |
| `PATCH`  | `/api/v1/usuarios/{id_usuario}`  | Solo `admin`                           | Actualiza parcialmente un usuario.           |
| `DELETE` | `/api/v1/usuarios/{id_usuario}`  | Solo `admin`                           | Elimina un usuario.                          |

Las rutas administrativas requieren `Authorization: Bearer <access_token>`. Un usuario autenticado sin el rol necesario recibe `403`; una petición sin autenticación recibe `401`.

### Crear usuario

`POST /api/v1/usuarios/crear-usuario`

Ejemplo de cuerpo JSON:

```json
{
  "username": "ana",
  "password": "una-clave-segura",
  "email": "ana@example.com",
  "id_rol": 2
}
```

`username` admite de 2 a 200 caracteres; `password`, de 8 a 200; `email` debe tener formato válido; `id_rol` debe existir. Los IDs iniciales son `1` admin, `2` films, `3` people, `4` locations, `5` species y `6` vehicles. En caso de username o email duplicado responde `409`; un ID de rol inexistente responde `422`. La contraseña no se devuelve en la respuesta.

### Listar y buscar usuarios

`GET /api/v1/usuarios/`

Sin parámetros devuelve la lista completa. El parámetro opcional `username` filtra por coincidencia parcial sin distinguir mayúsculas y minúsculas:

```http
GET /api/v1/usuarios/?username=an
```

### Consultar, actualizar o eliminar por ID

Sustituye `{id_usuario}` por el ID numérico correspondiente.

- `GET /api/v1/usuarios/{id_usuario}` devuelve el usuario o `404` si no existe.
- `PATCH /api/v1/usuarios/{id_usuario}` acepta cualquiera de estos campos opcionales: `username`, `password`, `email`, `id_rol`, `is_active`. Los campos omitidos o enviados como `null` no se actualizan. Devuelve `404` si no existe el usuario, `409` por duplicados o `422` si el rol no existe.
- `DELETE /api/v1/usuarios/{id_usuario}` elimina el usuario y responde con un campo `detail`. No se permite que un administrador se elimine a sí mismo (`400`). Un ID inexistente responde `404`.

Las respuestas de usuario incluyen `id_usuario`, `username`, `email`, `rol` e `is_active`; no exponen la contraseña ni su hash.

## Studio Ghibli

### Consultar un recurso

`GET /api/v1/studios-ghibli/{resource}`

Requiere un token Bearer y un usuario activo. Los recursos válidos son `films`, `people`, `locations`, `species` y `vehicles`. Se puede enviar el parámetro opcional `item_id` para consultar un elemento específico:

```http
GET /api/v1/studios-ghibli/films?item_id=2baf70d1-42bb-4437-b551-e5fed5a87abe
```

Sin `item_id`, la API devuelve una colección limitada a 100 elementos. Con `item_id`, devuelve el elemento solicitado. La consulta se reenvía a la API pública `https://ghibliapi.vercel.app`.

| Rol                  | Recursos permitidos        |
| -------------------- | -------------------------- |
| `admin` (ID `1`)     | Todos los recursos válidos |
| `films` (ID `2`)     | `films`                    |
| `people` (ID `3`)    | `people`                   |
| `locations` (ID `4`) | `locations`                |
| `species` (ID `5`)   | `species`                  |
| `vehicles` (ID `6`)  | `vehicles`                 |

Un recurso no válido responde `400`; la falta de permisos responde `403`; un elemento inexistente responde `404`; y un error de comunicación con el servicio externo responde `502`.

## Health check

`GET /health` no requiere autenticación y devuelve el estado básico del servicio. No forma parte del esquema OpenAPI y no verifica dependencias externas.
