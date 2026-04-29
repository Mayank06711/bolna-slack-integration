import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        start_time = time.perf_counter()

        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={"extra_data": {"request_id": request_id, "client": request.client.host if request.client else "unknown"}},
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={"extra_data": {"request_id": request_id, "duration_ms": round(duration_ms, 2), "error": str(exc)}},
            )
            raise

        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            f"Request completed: {request.method} {request.url.path} -> {response.status_code}",
            extra={"extra_data": {"request_id": request_id, "status_code": response.status_code, "duration_ms": round(duration_ms, 2)}},
        )

        response.headers["X-Request-ID"] = request_id
        return response
