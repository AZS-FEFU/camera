from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
import re
import logging

logger = logging.getLogger(__name__)

license_plate_router = APIRouter()

# Схемы для номерных знаков
class LicensePlateRequest(BaseModel):
    plate_number: str = Field(..., description="Номерной знак автомобиля", min_length=1, max_length=20)
    
    @validator('plate_number')
    def validate_plate_number(cls, v):
        if not v or not v.strip():
            raise ValueError('Номерной знак не может быть пустым')
        return v.strip()

class LicensePlateResponse(BaseModel):
    plate_number: str = Field(description="Обработанный номерной знак")
    is_valid: bool = Field(description="Валиден ли номерной знак")
    region_code: Optional[str] = Field(None, description="Код региона")
    plate_type: Optional[Literal["standard", "taxi", "trailer", "motorcycle", "transit", "diplomatic"]] = Field(None, description="Тип номерного знака")
    message: str = Field(description="Сообщение о результате валидации")

class ValidationStats(BaseModel):
    total_validated: int
    valid_plates: int
    invalid_plates: int

# Статистика (в реальном проекте лучше использовать базу данных или Redis)
validation_stats = {"total": 0, "valid": 0, "invalid": 0}

def validate_russian_plate(plate_number: str) -> dict:
    """
    Валидация российского номерного знака
    
    Поддерживаемые форматы:
    - Стандартные: А123ВС77, А123ВС777
    - Такси: АВ12377, АВ123777  
    - Прицепы: АВ123477, АВ1234777
    - Мотоциклы: 1234АВ77, 1234АВ777
    - Транзитные: Т12345А, Т123456А
    - Дипломатические: 123Д123, 1234Д123
    """
    plate_number = plate_number.upper().replace(" ", "").replace("-", "")
    
    # Паттерны для разных типов номеров
    patterns = {
        "standard": r"^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$",  # А123ВС77
        "taxi": r"^[АВЕКМНОРСТУХ]{2}\d{3}\d{2,3}$",  # АВ12377
        "trailer": r"^[АВЕКМНОРСТУХ]{2}\d{4}\d{2,3}$",  # АВ123477
        "motorcycle": r"^\d{4}[АВЕКМНОРСТУХ]{2}\d{2,3}$",  # 1234АВ77
        "transit": r"^Т\d{5}[АВЕКМНОРСТУХ]$",  # Т12345А
        "diplomatic": r"^\d{3,4}Д\d{2,3}$",  # 123Д77
    }
    
    for plate_type, pattern in patterns.items():
        if re.match(pattern, plate_number):
            # Извлекаем код региона
            region_code = None
            if plate_type in ["standard", "taxi", "trailer", "motorcycle"]:
                # Для обычных номеров регион в конце
                if plate_type == "standard":
                    region_code = plate_number[-2:] if len(plate_number) == 8 else plate_number[-3:]
                else:
                    region_code = plate_number[-2:] if len(plate_number) <= 8 else plate_number[-3:]
            elif plate_type == "diplomatic":
                # Для дипломатических номеров регион после Д
                region_code = plate_number.split('Д')[1]
            
            return {
                "is_valid": True,
                "plate_type": plate_type,
                "region_code": region_code,
                "message": f"Номерной знак корректен (тип: {plate_type})"
            }
    
    return {
        "is_valid": False,
        "plate_type": None,
        "region_code": None,
        "message": "Некорректный формат номерного знака"
    }

@license_plate_router.post("/validate", response_model=LicensePlateResponse)
async def validate_license_plate(request: LicensePlateRequest):
    """
    Валидация номерного знака автомобиля через POST запрос
    
    Принимает JSON с номерным знаком и возвращает результат валидации
    """
    try:
        # Валидируем номер
        validation_result = validate_russian_plate(request.plate_number)
        
        # Обновляем статистику
        validation_stats["total"] += 1
        if validation_result["is_valid"]:
            validation_stats["valid"] += 1
        else:
            validation_stats["invalid"] += 1
        
        logger.info(f"Validated plate: {request.plate_number}, result: {validation_result['is_valid']}")
        
        return LicensePlateResponse(
            plate_number=request.plate_number.upper().replace(" ", "").replace("-", ""),
            **validation_result
        )
    
    except Exception as e:
        logger.error(f"Error validating plate {request.plate_number}: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при обработке номерного знака")

@license_plate_router.get("/{plate_number}", response_model=LicensePlateResponse)
async def get_license_plate_info(
    plate_number: str = Field(..., description="Номерной знак автомобиля", min_length=1, max_length=20)
):
    """
    Получение информации о номерном знаке через GET запрос
    
    Номерной знак передается в URL как path параметр
    """
    if not plate_number or not plate_number.strip():
        raise HTTPException(status_code=400, detail="Номерной знак не может быть пустым")
    
    try:
        validation_result = validate_russian_plate(plate_number)
        
        # Обновляем статистику
        validation_stats["total"] += 1
        if validation_result["is_valid"]:
            validation_stats["valid"] += 1
        else:
            validation_stats["invalid"] += 1
        
        logger.info(f"Validated plate: {plate_number}, result: {validation_result['is_valid']}")
        
        return LicensePlateResponse(
            plate_number=plate_number.upper().replace(" ", "").replace("-", ""),
            **validation_result
        )
    
    except Exception as e:
        logger.error(f"Error validating plate {plate_number}: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при обработке номерного знака")

@license_plate_router.get("/", response_model=list[LicensePlateResponse])
async def validate_multiple_plates(
    plates: str = Query(..., description="Номерные знаки через запятую", example="А123ВС77,В456УК78")
):
    """
    Валидация нескольких номерных знаков одновременно
    
    Номера передаются через запятую в query параметре
    """
    plate_list = [plate.strip() for plate in plates.split(',') if plate.strip()]
    
    if not plate_list:
        raise HTTPException(status_code=400, detail="Необходимо указать хотя бы один номерной знак")
    
    if len(plate_list) > 10:
        raise HTTPException(status_code=400, detail="Максимум 10 номерных знаков за раз")
    
    results = []
    for plate in plate_list:
        try:
            validation_result = validate_russian_plate(plate)
            
            # Обновляем статистику
            validation_stats["total"] += 1
            if validation_result["is_valid"]:
                validation_stats["valid"] += 1
            else:
                validation_stats["invalid"] += 1
            
            results.append(LicensePlateResponse(
                plate_number=plate.upper().replace(" ", "").replace("-", ""),
                **validation_result
            ))
        except Exception as e:
            logger.error(f"Error validating plate {plate}: {str(e)}")
            results.append(LicensePlateResponse(
                plate_number=plate,
                is_valid=False,
                message=f"Ошибка при обработке: {str(e)}"
            ))
    
    return results

@license_plate_router.get("/stats/validation", response_model=ValidationStats)
async def get_validation_stats():
    """
    Получение статистики валидации номерных знаков
    """
    return ValidationStats(
        total_validated=validation_stats["total"],
        valid_plates=validation_stats["valid"],
        invalid_plates=validation_stats["invalid"]
    )