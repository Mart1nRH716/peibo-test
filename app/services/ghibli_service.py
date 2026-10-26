"""Servicio para consumir la API pública de Studio Ghibli de forma externa."""

import httpx

GHIBLI_BASE_URL = "https://ghibliapi.vercel.app"

# Mapeo oficial de los nombres de recursos de Ghibli
VALID_RESOURCES = {"films", "people", "locations", "species", "vehicles"}
LIMITED_LIST_SIZE = 100  # Limite de elementos a retornar en la lista (por defecto Ghibli retorna 50, max 250)


class InvalidGhibliResourceError(Exception):
	"""Se lanza cuando se solicita un recurso que la API de Ghibli no ofrece."""


class GhibliItemNotFoundError(Exception):
	"""Se lanza cuando la API de Ghibli no encuentra el elemento solicitado."""


class GhibliUpstreamError(Exception):
	"""Se lanza cuando falla la comunicación con la API de Ghibli."""


class GhibliService:
	"""Clase encargada de realizar peticiones HTTP hacia la API de Studio Ghibli."""

	@staticmethod
	async def get_ghibli_data(resource: str, item_id: str | None = None) -> list | dict:
		"""Consume la API de Ghibli validando el recurso y opcionalmente buscando por ID."""
		if resource not in VALID_RESOURCES:
			raise InvalidGhibliResourceError(f"El recurso '{resource}' no es válido.")

		# Construcción de la URL (con o sin ID)
		url = f"{GHIBLI_BASE_URL}/{resource}"
		if item_id:
			url = f"{url}/{item_id}"

		async with httpx.AsyncClient(timeout=10.0) as client:
			try:
				response = await client.get(url=url, params={"limit": LIMITED_LIST_SIZE})
				
				# Si Ghibli responde 404 (ej. ID no encontrado)
				if response.status_code == 404:
					raise GhibliItemNotFoundError(
						"El elemento solicitado no existe en la API de Studio Ghibli."
					)
				
				response.raise_for_status()
				data = response.json()
					
				return data

			except httpx.HTTPError as exc:
				raise GhibliUpstreamError(
					f"Error al conectar con la API de Studio Ghibli: {str(exc)}"
				) from exc