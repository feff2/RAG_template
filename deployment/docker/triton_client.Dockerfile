FROM pytorch/pytorch:2.7.1-cuda11.8-cudnn9-runtime

RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

COPY src/services/triton_service/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

WORKDIR /app

COPY src/triton_service ./src/
COPY models/bi_encoder ./models/bi_encoder
COPY models/reranker ./models/reranker

RUN mkdir -p /app/.models && \
    ln -s /app/models/bi_encoder /app/.models/bi_encoder && \
    ln -s /app/models/reranker /app/.models/reranker

RUN mkdir -p /app/src/services/ && \
    mkdir -p /app/src/models/ && \
    mkdir -p /app/src/shared/ && \
    ln -s /app/src/services/llm_service /app/src/services/triton_service && \
    ln -s /app/src/models/bi_encoder /app/src/models/bi_encoder && \
    ln -s /app/src/models/reranker /app/src/models/reranker && \
    ln -s /app/src/shared /app/src/shared

EXPOSE 8000

CMD ["uvicorn", "src.services.llm_service.main:app", "--host", "0.0.0.0", "--port", "8000"]