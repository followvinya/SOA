#!/bin/bash
set -e

echo "Generating proto files..."
python /app/statistics_service/generate_protos.py

echo "Starting statistics service..."
python /app/statistics_service/app/main.py