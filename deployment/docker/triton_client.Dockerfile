FROM nvidia/cuda:12.8.1-cudnn-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3.10 python3.10-venv python3.10-distutils python3-pip \
    build-essential git curl wget \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV VENV=/opt/venv
RUN python3.10 -m venv $VENV
ENV PATH="$VENV/bin:$PATH"

RUN pip install --upgrade pip setuptools wheel
RUN pip install torch --index-url https://download.pytorch.org/whl/cu128

COPY src/services/triton_service/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY src/ /app/src/
COPY models/bi_encoder /app/models/bi_encoder
COPY models/reranker /app/models/reranker

ENV PYTHONPATH=/app/src:$PYTHONPATH

WORKDIR /app

EXPOSE 8002

CMD ["python", "-m", "uvicorn", "services.triton_service.main:app", "--host", "0.0.0.0", "--port", "8002"]
