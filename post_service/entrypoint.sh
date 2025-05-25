#!/bin/bash
set -e

echo "Waiting for database to be ready..."
sleep 5

echo "Generating proto files..."
python /app/generate_protos.py

echo "Checking generated files..."
ls -la /app/post_service/generated/

echo "Starting gRPC server..."
cd /app && python -m post_service.app.main