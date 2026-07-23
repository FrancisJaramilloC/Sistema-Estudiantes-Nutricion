"""
Middleware CORS permisivo y robusto.

Refleja el encabezado `Origin` de la petición en la respuesta, lo que permite
cualquier origen (http(s), IP de red local, `null` en iframes/preview y esquemas
de webviews móviles como `capacitor://` o `ionic://`) sin romper el flujo de
credenciales (cookie/JWT en header Authorization).

Se registra como el middleware más externo para garantizar que TODAS las
respuestas (incluidas las de error 401/403 y los preflight OPTIONS) incluyan
los encabezados CORS necesarios.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class PermissiveCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")

        # Preflight (OPTIONS) de la browser
        if request.method == "OPTIONS":
            response = Response(status_code=200)
            self._set_cors_headers(response, origin)
            response.headers["Access-Control-Max-Age"] = "600"
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            )
            requested_headers = request.headers.get(
                "access-control-request-headers", ""
            )
            response.headers["Access-Control-Allow-Headers"] = (
                requested_headers if requested_headers else "*"
            )
            return response

        response = await call_next(request)
        self._set_cors_headers(response, origin)
        return response

    @staticmethod
    def _set_cors_headers(response: Response, origin: str | None):
        # Refleja el origen real de la petición (o "*" si no hay origen).
        # Con credenciales el navegador exige que el origen sea exacto, por lo
        # que usamos el valor del header Origin en lugar de "*".
        response.headers["Access-Control-Allow-Origin"] = origin if origin else "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        )
        response.headers["Access-Control-Allow-Headers"] = (
            "Authorization, Content-Type, Accept, Origin, X-Requested-With"
        )
        response.headers["Vary"] = "Origin"
