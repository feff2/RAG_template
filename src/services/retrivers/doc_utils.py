import re
from pathlib import Path
from typing import Dict, List

from haystack import Document, component


@component
class DocumentReader:
    @component.output_types(out=List[Document])
    def run(self, source: Path) -> Dict[str, List[Document]]:
        all_files = list(source.rglob("*.*"))
        documents = []
        for file_path in all_files:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    url = file.readline().strip()
                    content = file.read()
                    documents.append(
                        Document(
                            content=content,
                            meta={"name": file_path.name, "common_url": url},
                        )
                    )
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        return {"out": documents}


@component
class LinkFinder:
    @component.output_types(out=List[Document])
    def run(self, docs: List[Document]) -> Dict[str, List[Document]]:
        url_pattern = re.compile(r"https?://[^\s]+")
        for doc in docs:
            doc_text = doc.content
            match = url_pattern.search(doc_text)
            if match:
                link = match.group(0)
                doc.meta["chunk_url"] = link
            else:
                doc.meta["chunk_url"] = None
        return {"out": docs}


@component
class DocumentCombiner:
    @component.output_types(out=str, context=List[Document])
    def run(self, documents: List[Document]) -> Dict[str, object]:
        combined_content = "\n\n".join([doc.content for doc in documents])
        prompt = f"Вот документы, которые могут помочь ответить на вопрос:\n\n{combined_content}"
        return {"out": prompt, "context": documents}
