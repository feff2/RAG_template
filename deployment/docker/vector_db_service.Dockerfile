FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY src/services/vector_db_service/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY src/ /app/src
ENV PYTHONPATH=/app/src

EXPOSE 8003

CMD ["python", "-m", "uvicorn", "services.vector_db_service.main:app", "--host", "0.0.0.0", "--port", "8003"]
