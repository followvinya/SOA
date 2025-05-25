FROM python:3.9-slim

WORKDIR /app

COPY ./statistics_service/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Установка pytest для тестирования
RUN pip install pytest pytest-asyncio pytest-mock pytest-cov


COPY ./protos/ /app/protos/
COPY ./statistics_service/ /app/statistics_service/

# Копируем тесты
COPY ./tests/ /app/tests/

RUN mkdir -p /app/statistics_service/generated

ENV PYTHONPATH="${PYTHONPATH}:/app"

COPY ./statistics_service/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]