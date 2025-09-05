# RAG chat bot
## Environment instalation guide
```
conda create -n rlt python=3.12 pip
conda activate rlt
pip install -r requirements.txt
pre-commit install
```

## Run chat servise by
```
python src/services/chat/run_chat.py
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
