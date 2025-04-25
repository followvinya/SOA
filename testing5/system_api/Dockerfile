FROM python:3.9-slim

WORKDIR /app

COPY ./protos /app/protos

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Generate gRPC code
RUN mkdir -p /app/post_service/generated
RUN python -m grpc_tools.protoc -I/app/protos --python_out=/app/post_service/generated --grpc_python_out=/app/post_service/generated /app/protos/posts.proto

COPY ./system_api /app/system_api

CMD ["uvicorn", "system_api.main:app", "--host", "0.0.0.0", "--port", "8000"]