FROM pytorch/pytorch:2.7.1-cuda12.8-cudnn9-runtime

RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*



COPY src/services/llm_service/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

WORKDIR /app

COPY models/llm/ /app/models/llm
COPY src/services/llm_service/ /app/src/services/llm_service/
COPY src/models/llm/ /app/src/models/llm/
COPY src/shared/ /app/src/shared/

ENV PYTHONPATH=/app/src:${PYTHONPATH}

EXPOSE 8000
CMD ["uvicorn", "services.llm_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
