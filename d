version: "3.9"

networks:
  rag-network:
    driver: bridge

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant/storage:/qdrant/storage
      - ./qdrant/logs:/qdrant/logs
    environment:
      - QDRANT__SERVICE__AUTOFLUSH_INTERVAL=1
    restart: unless-stopped
    networks:
      - rag-network

  vector_db_service:
    image: rag-template_vector_db_service
    container_name: vector-db-service
    ports:
      - "8003:8003"
    environment:
      - QDRANT_URL=http://qdrant:6333
      - PYTHONPATH=/app/src
    volumes:
      - ./src:/app/src
    working_dir: /app
    restart: unless-stopped
    depends_on:
      - qdrant
    networks:
      - rag-network

  