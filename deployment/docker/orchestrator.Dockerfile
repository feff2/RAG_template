FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

COPY src/services/orchestrator /app/src/
COPY src/shared /app/src/shared

ENV PYTHONPATH=/app/src:$PYTHONPATH

WORKDIR /app

EXPOSE 8001

CMD ["uvicorn", "src.orchestrator.main:app", "--host", "0.0.0.0", "--port", "8001"]
