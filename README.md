# License Plate API

API для валидации российских номерных знаков автомобилей.

## Структура проекта

```
├── src/
│   ├── __init__.py
│   └── api/
│       ├── __init__.py
│       └── license_plate.py    # Роутер для работы с номерными знаками
├── app.py                      # Основное приложение FastAPI
├── requirements.txt            # Зависимости
└── README.md                   # Документация
```

## Установка и запуск

### Установка зависимостей
```bash
uv sync
```

### Запуск сервера
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Запуск в Docker
```bash
# Создать Dockerfile
cat > Dockerfile << EOF
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Собрать и запустить
docker build -t license-plate-api .
docker run -p 8000:8000 license-plate-api
```

## API Эндпоинты

### Health Check
- `GET /health` - Проверка работоспособности сервиса

### Валидация номерных знаков

#### Валидация одного номера (POST)
```http
POST /api/v1/license-plates/validate
Content-Type: application/json

{
  "plate_number": "А123ВС77"
}
```

#### Валидация одного номера (GET)
```http
GET /api/v1/license-plates/А123ВС77
```

#### Валидация нескольких номеров
```http
GET /api/v1/license-plates/?plates=А123ВС77,В456УК78,С789МН99
```

#### Статистика валидации
```http
GET /api/v1/license-plates/stats/validation
```

### Ответ API
```json
{
  "plate_number": "А123ВС77",
  "is_valid": true,
  "region_code": "77",
  "plate_type": "standard",
  "message": "Номерной знак корректен (тип: standard)"
}
```

## Поддерживаемые типы номеров

- **standard**: А123ВС77, А123ВС777 - обычные номера
- **taxi**: АВ12377, АВ123777 - номера такси
- **trailer**: АВ123477, АВ1234777 - номера прицепов
- **motorcycle**: 1234АВ77, 1234АВ777 - номера мотоциклов
- **transit**: Т12345А - транзитные номера
- **diplomatic**: 123Д77, 1234Д123 - дипломатические номера

## Документация

После запуска сервера документация доступна по адресам:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Примеры использования

### Python (requests)
```python
import requests

# POST запрос
response = requests.post(
    "http://localhost:8000/api/v1/license-plates/validate",
    json={"plate_number": "А123ВС77"}
)
print(response.json())

# GET запрос
response = requests.get("http://localhost:8000/api/v1/license-plates/А123ВС77")
print(response.json())
```

### cURL
```bash
# POST запрос
curl -X POST "http://localhost:8000/api/v1/license-plates/validate" \
     -H "Content-Type: application/json" \
     -d '{"plate_number": "А123ВС77"}'

# GET запрос
curl "http://localhost:8000/api/v1/license-plates/А123ВС77"

# Множественная валидация
curl "http://localhost:8000/api/v1/license-plates/?plates=А123ВС77,В456УК78"
```

### JavaScript (fetch)
```javascript
// POST запрос
const response = await fetch('http://localhost:8000/api/v1/license-plates/validate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ plate_number: 'А123ВС77' })
});
const data = await response.json();
console.log(data);

// GET запрос
const response2 = await fetch('http://localhost:8000/api/v1/license-plates/А123ВС77');
const data2 = await response2.json();
console.log(data2);
```

## Статусы ответов

- `200` - Успешная обработка
- `400` - Некорректные данные запроса
- `422` - Ошибка валидации данных
- `500` - Внутренняя ошибка сервера

## Разработка

### Структура кода
- `app.py` - основное приложение FastAPI с middleware и обработчиками ошибок
- `src/api/license_plate.py` - роутер с логикой валидации номерных знаков
- Валидация основана на регулярных выражениях для российских номеров
- Поддержка различных форматов номеров (обычные, такси, прицепы, мотоциклы, транзитные, дипломатические)

### Логирование
Все операции логируются с помощью стандартного модуля `logging` Python.

### Тестирование
Для тестирования API можно использовать встроенную документацию Swagger UI или любой HTTP клиент.