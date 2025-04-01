FROM python:3.9-slim

WORKDIR /app

# Copy proto files
COPY ./protos /app/protos

# Copy requirements and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Generate gRPC code
RUN mkdir -p /app/post_service/generated
RUN python -m grpc_tools.protoc -I/app/protos --python_out=/app/post_service/generated --grpc_python_out=/app/post_service/generated /app/protos/posts.proto

# Copy application code
COPY ./system_api /app/system_api

# Run API server
CMD ["uvicorn", "system_api.main:app", "--host", "0.0.0.0", "--port", "8000"]