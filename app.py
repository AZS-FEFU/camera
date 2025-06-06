from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
import logging

# Импортируем роутер для номерных знаков
from src.api.license_plate import license_plate_router

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="License Plate API",
    description="API для работы с номерными знаками автомобилей",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене лучше указать конкретные домены
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Основной роутер с префиксом /api
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(license_plate_router, prefix="/license-plates", tags=["License Plates"])

app.include_router(api_router)

# Health check эндпоинт
@app.get("/health", tags=["Health"])
async def health_check():
    """Проверка работоспособности сервиса"""
    return {
        "status": "healthy", 
        "service": "license-plate-api",
        "version": "1.0.0"
    }

# Root эндпоинт
@app.get("/", tags=["Root"])
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "License Plate API",
        "docs": "/docs",
        "health": "/health"
    }

# Обработчик ошибок валидации
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error for {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Ошибка валидации данных",
            "details": exc.errors()
        },
    )

# Обработчик общих HTTP ошибок
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error for {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Внутренняя ошибка сервера",
            "message": "Попробуйте позже"
        },
    )