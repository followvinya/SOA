#!/bin/bash

echo "Generating proto files..."
python /app/generate_protos.py

echo "Starting post service..."
python -m post_service.app.main