# RAG chat bot
## Environment instalation guide
```
conda create -n rlt python=3.12 pip
conda activate rlt
pip install -r requirements.txt
pre-commit install
```

## Pull redis container and run it
```
docker pull redis:7

docker run -d \  --name redis-rag \
  -p 6379:6379 \
  redis:7
```

## Run api_gateway by
```
python -m src.services.api_gateway.main
```

## Send request to service
```
curl -sS -X POST "http://localhost:8080/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"request_id": "req-1", "query": "Привет!"}' | jq
```

## Get questions with some count (default=10)
```
curl -X GET "http://localhost:8080/api/v1/faq?limit=10" -H "Accept: application/json"
```


## Build knowledge base
Store documents in readable format (txt for example)

```
data/documents
```

Then go to the
```
src/services/retrivers/pipeline.py
```
Uncomment loading script and run it
