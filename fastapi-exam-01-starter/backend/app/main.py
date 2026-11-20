
from fastapi import FastAPI

from app.database import Base, engine
from app import models

from app.routers import auth,parcels

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Okwu Couriers API",
    description="Parcel booking and tracking system",
    version="1.0.0"
)

# Register authentication router
app.include_router(auth.router)
app.include_router(auth.router)
app.include_router(parcels.router)


@app.get("/")
def home():
    return {
        "message": "Welcome to Okwu Couriers API",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
