from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from app.core.logging import get_logger

logger = get_logger(__name__)


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """Restricts webhook endpoints to requests from allowed IPs.

    Only applies to paths starting with /api/v1/webhook.
    Other endpoints (health, docs) are unrestricted.
    """

    def __init__(self, app, allowed_ips: list[str]):
        super().__init__(app)
        self.allowed_ips = set(allowed_ips)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Only filter webhook endpoints
        if request.url.path.startswith("/api/v1/webhook"):
            client_ip = request.client.host if request.client else "unknown"

            if client_ip not in self.allowed_ips:
                logger.warning(
                    f"Blocked request from unauthorized IP: {client_ip}",
                    extra={"extra_data": {"client_ip": client_ip, "path": request.url.path}},
                )
                return JSONResponse(
                    status_code=403,
                    content={"status": "error", "message": "Forbidden"},
                )

        return await call_next(request)
