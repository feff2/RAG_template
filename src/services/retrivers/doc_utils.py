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
                    content = file.read()
                    documents.append(
                        Document(content=content, meta={"name": file_path.name})
                    )
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        return {"out": documents}


@component
class DocumentCombiner:
    @component.output_types(out=str, context=List[Document])
    def run(self, documents: List[Document]) -> Dict[str, object]:
        combined_content = "\n\n".join([doc.content for doc in documents])
        prompt = f"Вот документы, которые могут помочь ответить на вопрос:\n\n{combined_content}"
        return {"out": prompt, "context": documents}
