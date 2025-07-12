from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import logging
from sqlalchemy.orm import Session

from .models.database import create_tables, get_db, User
from .routers import auth, products, quotes, admin
from .utils.security import hash_password
from .services.vector_store import VectorStore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 Starting Audico AI Quoting System...")
    
    # Create database tables
    create_tables()
    
    # Create default admin user
    from .models.database import SessionLocal
    db = SessionLocal()
    try:
        existing_admin = db.query(User).filter(User.email == "admin@audico.co.za").first()
        if not existing_admin:
            admin_user = User(
                email="admin@audico.co.za",
                full_name="Audico Admin",
                company="Audico Audio Solutions",
                hashed_password=hash_password("admin123"),
                is_admin=True,
                customer_group=8
            )
            db.add(admin_user)
            db.commit()
            logger.info("✅ Created admin user: admin@audico.co.za / admin123")
    finally:
        db.close()
    
    # Initialize vector store
    vector_store = VectorStore(os.getenv("OPENAI_API_KEY"))
    logger.info("✅ Vector store initialized")
    
    logger.info("🎯 Audico AI Quoting System ready!")
    
    yield
    
    logger.info("🔄 Shutting down Audico AI Quoting System...")

# Create FastAPI app
app = FastAPI(
    title="Audico AI Audio Solutions Quotation System",
    description="Professional audio solutions with AI-powered quoting and pricelist management",
    version="3.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(quotes.router)
app.include_router(admin.router)

@app.get("/")
async def root():
    return {
        "message": "🎵 Audico AI Audio Solutions Quotation System",
        "version": "3.0.0",
        "status": "operational",
        "features": [
            "AI-powered pricelist processing",
            "Multi-format document support",
            "Vector-based product search",
            "Customer group pricing",
            "Professional quote generation"
        ],
        "admin_login": "admin@audico.co.za / admin123"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "ai_processing": "enabled" if os.getenv("OPENAI_API_KEY") else "disabled",
        "vector_store": "active"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)