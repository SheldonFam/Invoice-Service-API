from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, invoices, templates, users

app = FastAPI(title="Invoice API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://your-production-domain.com"],
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
