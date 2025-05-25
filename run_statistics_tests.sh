#!/bin/bash

echo "Running tests inside containers..."

if ! docker-compose ps | grep -q "statistics-service.*Up"; then
    echo "Starting services..."
    docker-compose up -d
    sleep 10
fi

echo -e "\n📋 Testing ClickHouse Client..."
docker-compose exec -T statistics-service pytest /app/tests/statistics/test_clickhouse_client.py -v --tb=short 2>&1 | grep -E "(PASSED|FAILED|ERROR|test_)"

echo -e "\n📋 Testing Kafka Consumer..."
docker-compose exec -T statistics-service pytest /app/tests/statistics/test_kafka_consumer.py -v --tb=short 2>&1 | grep -E "(PASSED|FAILED|ERROR|test_)"

echo -e "\n📋 Testing gRPC Service..."
docker-compose exec -T statistics-service pytest /app/tests/statistics/test_grpc_service.py -v --tb=short 2>&1 | grep -E "(PASSED|FAILED|ERROR|test_)"

echo -e "\n📋 Testing REST API..."
docker-compose exec -T statistics-api pytest /app/tests/statistics/test_api.py -v --tb=short 2>&1 | grep -E "(PASSED|FAILED|ERROR|test_)"

echo -e "\n📋 Running Integration Tests..."
pytest tests/statistics/test_integration.py -v --tb=short

echo -e "\n✅ Tests completed!"