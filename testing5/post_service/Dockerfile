FROM python:3.9-slim

WORKDIR /app

# Устанавливаем зависимости
COPY ./post_service/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Копируем proto файлы
COPY ./protos/ /app/protos/

# Копируем скрипт генерации и код приложения
COPY ./post_service/generate_protos.py /app/
COPY ./post_service/app/ /app/post_service/app/

# Создаем директорию для сгенерированных файлов
RUN mkdir -p /app/generated

# Добавляем сгенерированную директорию в PYTHONPATH
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Скрипт запуска
COPY ./post_service/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Запускаем сервис через скрипт
ENTRYPOINT ["/app/entrypoint.sh"]