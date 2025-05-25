FROM python:3.9-slim

WORKDIR /app

COPY ./statistics_api/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt


# Установка pytest для тестирования
RUN pip install pytest pytest-asyncio httpx pytest-cov

COPY ./protos /app/protos

# Generate gRPC code
RUN mkdir -p /app/statistics_service/generated
RUN python -m grpc_tools.protoc -I/app/protos --python_out=/app/statistics_service/generated --grpc_python_out=/app/statistics_service/generated /app/protos/statistics.proto

COPY ./statistics_api /app/statistics_api

# Копируем тесты
COPY ./tests/ /app/tests/

CMD ["uvicorn", "statistics_api.main:app", "--host", "0.0.0.0", "--port", "8002"]