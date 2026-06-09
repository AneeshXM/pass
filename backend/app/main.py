"""Main FastAPI application."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.database import init_db, SessionLocal
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    init_db()
    
    # Create default roles and admin user
    create_defaults()
    
    yield
    
    # Shutdown
    pass


def create_defaults():
    """Create default roles and admin user."""
    import logging
    logger = logging.getLogger(__name__)
    
    from app.core.security import security
    
    db = SessionLocal()
    try:
        # Check if roles exist
        from app.models.user import Role
        
        if db.query(Role).count() == 0:
            logger.info("Creating default roles...")
            # Create default roles
            roles = [
                Role(name="Admin", description="Full system access", permissions="all"),
                Role(name="Manager", description="Manage vaults and users", permissions="vault:create,vault:manage,user:read"),
                Role(name="User", description="Basic user access", permissions="vault:read,credential:read"),
            ]
            for role in roles:
                db.add(role)
            db.commit()
            
            # Create admin user
            logger.info("Creating default admin user...")
            from app.models.user import User
            admin = User(
                email="admin@passwordmanager.local",
                username="admin",
                full_name="System Administrator",
                hashed_password=security.hash_password("ChangeMe123!"),
                role_id=1,  # Admin role
                is_superuser=True
            )
            db.add(admin)
            db.commit()
            logger.info("Default admin user created successfully")
        else:
            logger.info("Default roles already exist, skipping creation")
    except Exception as e:
        logger.error(f"Error creating defaults: {e}")
        raise
    finally:
        db.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": errors}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    # Log error
    print(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": f"{settings.API_V1_PREFIX}/docs"
    }