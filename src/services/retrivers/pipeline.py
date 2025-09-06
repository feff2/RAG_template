from pathlib import Path
from typing import List

from haystack import Document, Pipeline
from haystack.components.preprocessors import DocumentSplitter
from haystack.components.writers import DocumentWriter
from haystack_integrations.components.embedders.fastembed import (
    FastembedSparseDocumentEmbedder,
    FastembedSparseTextEmbedder,
)
from haystack_integrations.components.retrievers.qdrant import QdrantHybridRetriever
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

from src.services.retrivers.doc_utils import DocumentCombiner, DocumentReader
from src.services.retrivers.embedder import DocEmbedder, EmbedClient, QueryEmbedder
from src.shared import config


class SavePipeline:
    def __init__(self) -> None:
        embed_client = EmbedClient()
        document_embedder = DocEmbedder(embed_client=embed_client)
        sparce_embedder = FastembedSparseDocumentEmbedder(model="Qdrant/bm25")
        document_reader = DocumentReader()
        document_store = QdrantDocumentStore(
            url=config.db_server_url,
            embedding_dim=config.embedding_model_dim,
            recreate_index=True,
            use_sparse_embeddings=True,
        )
        document_splitter = DocumentSplitter(
            split_by="word", split_length=512, split_overlap=30
        )
        document_writer = DocumentWriter(document_store=document_store)

        indexing_pipeline = Pipeline()
        indexing_pipeline.add_component("document_reader", document_reader)
        indexing_pipeline.add_component("document_splitter", document_splitter)
        indexing_pipeline.add_component("document_embedder", document_embedder)
        indexing_pipeline.add_component("document_writer", document_writer)
        indexing_pipeline.add_component("sparce_embedder", sparce_embedder)

        indexing_pipeline.connect("document_reader.out", "document_splitter.documents")
        indexing_pipeline.connect("document_splitter", "sparce_embedder")
        indexing_pipeline.connect("sparce_embedder", "document_embedder")
        indexing_pipeline.connect("document_embedder", "document_writer")
        self.pipeline = indexing_pipeline

    def run(self, path_to_docs: Path) -> None:
        self.pipeline.run({"document_reader": {"source": path_to_docs}})


class RetrievePipeline:
    def __init__(self) -> None:
        document_store = QdrantDocumentStore(
            url=config.db_server_url,
            embedding_dim=config.embedding_model_dim,
            use_sparse_embeddings=True,
        )
        retriever = QdrantHybridRetriever(
            document_store=document_store, top_k=config.top_k
        )
        sparse_embedder = FastembedSparseTextEmbedder(model="Qdrant/bm25")
        embedder = QueryEmbedder(
            embed_client=EmbedClient(),
        )
        combiner = DocumentCombiner()
        self.rag_pipeline = Pipeline()
        self.rag_pipeline.add_component("sparse_text_embedder", sparse_embedder)
        self.rag_pipeline.add_component("embedder", embedder)
        self.rag_pipeline.add_component("retriever", retriever)
        self.rag_pipeline.add_component("combiner", combiner)
        self.rag_pipeline.connect(
            "sparse_text_embedder.sparse_embedding", "retriever.query_sparse_embedding"
        )
        self.rag_pipeline.connect("embedder.embedding", "retriever.query_embedding")
        self.rag_pipeline.connect("retriever", "combiner.documents")

    def run(self, question: str) -> tuple[str, List[Document]]:
        results = self.rag_pipeline.run(
            {
                "embedder": {"query": question},
                "sparse_text_embedder": {"text": question},
            }
        )
        return results["combiner"]["out"], results["combiner"]["context"]


if __name__ == "__main__":
    # Пример использования пайплайна для сохранения документов в базу
    path_to_docs = Path("./data/documents")
    save_pipeline = SavePipeline()
    save_pipeline.run(path_to_docs)

    # Пример использования пайплайна для получения релевантных документов по вопросу
    retrieve_pipeline = RetrievePipeline()
    question = "Что произошло во Франции в 18 веке?"
    answer, docs = retrieve_pipeline.run(question)
    print("Ответ:", answer)
    print(f"Найдено {len(docs)} релевантных документов.")
