#!/bin/bash

echo "Running unit tests (excluding Kafka tests)..."

# Запускаем только определенные тесты
python -m pytest tests/test_repository.py tests/test_api.py -v --cov=post_service --cov=system_api --cov=user_service --cov-report=html --cov-report=term

echo "Tests completed. Coverage report available in htmlcov/index.html"