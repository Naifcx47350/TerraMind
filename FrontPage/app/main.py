from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import ask, health, history
from app.middleware.error_handler import add_error_handler
from app.middleware.logger import add_logger

app = FastAPI(
    title="AgroMind API",
    description="Agriculture RAG System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_error_handler(app)
add_logger(app)

app.include_router(ask.router, prefix="/api", tags=["Ask"])
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(history.router, prefix="/api", tags=["History"])


@app.get("/")
def root():
    return {"message": "AgroMind API is running", "docs": "/docs"}
