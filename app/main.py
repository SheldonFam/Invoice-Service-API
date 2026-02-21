import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.routers import auth, invoices, templates, users

logger = logging.getLogger(__name__)

app = FastAPI(title="Invoice API", version="1.0.0")

app.state.limiter = auth.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# CORS must be added last — FastAPI middleware runs in reverse order,
# so this runs first and ensures CORS headers are on ALL responses
# (including error responses from rate limiting, validation, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix="/api/v1")
app.include_router(invoices.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(templates.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Invoice API is running"}
