import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("terramind")


def add_error_handler(app: FastAPI):
    @app.exception_handler(Exception)
    async def global_handler(request: Request, exc: Exception):
        # Full details go to the server log only; internal URLs, paths and
        # library messages are not shown to visitors.
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": "Something went wrong. Please try again."},
        )
