import numpy as np
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-m3")

app = FastAPI()
emb_size = 384


class EmbedRequest(BaseModel):
    texts: list[str]


class EmbedResponse(BaseModel):
    embeddings: list[list[float]]


@app.post("/embed", response_model=EmbedResponse)
def embed(req: EmbedRequest) -> EmbedResponse:
    vectors = model.encode(req.texts, convert_to_numpy=True)
    if vectors.shape[1] > emb_size:
        truncated_vectors = vectors[:, :emb_size].tolist()
    else:
        padded_vectors = np.zeros((vectors.shape[0], emb_size))
        padded_vectors[:, : vectors.shape[1]] = vectors
        truncated_vectors = padded_vectors.tolist()
    return EmbedResponse(embeddings=truncated_vectors)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
