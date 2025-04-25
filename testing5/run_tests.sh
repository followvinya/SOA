#!/bin/bash

# Генерируем proto-файлы, если они отсутствуют
if [ ! -d "post_service/generated" ]; then
  echo "Генерация proto-файлов..."
  mkdir -p post_service/generated
  python -m grpc_tools.protoc -I./protos --python_out=./post_service/generated --grpc_python_out=./post_service/generated ./protos/posts.proto
  touch post_service/generated/__init__.py
  echo "Proto-файлы сгенерированы"
fi

# Запускаем тесты для репозитория
echo "Запуск тестов репозитория..."
python -m tests.test_repository

# Запускаем тесты для gRPC сервиса
echo "Запуск тестов gRPC сервиса..."
python -m tests.test_service

# Запускаем тесты для REST API
#echo "Запуск тестов REST API..."
#python -m tests.test_api

echo "Все тесты выполнены"