from qdrant_haystack import QdrantDocumentStore
from haystack import Document
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
from haystack.components.embedders import SentenceTransformersDocumentEmbedder

#from haystack.components.converters import DocxToDocument
from haystack.components.converters import (
    TextFileToDocument,      # 🔄 Cambio de TextFileToDocument
    #PDFToDocument,       # 🔄 Cambio de PyPDFToDocument  
    MarkdownToDocument   # 🔄 Cambio de MarkdownFileToDocument
)

import os

from fastapi_response_standard import success_response
from fastapi_response_standard import (
    CatchAllMiddleware,
    success_response,
    error_response
)
from fastapi_response_standard.common_exception_handlers import (
    not_found_handler,
    validation_error_handler
)



print("🔧 Conectando a Qdrant...")
document_store = QdrantDocumentStore(host="qdrant", port=6333, embedding_dim=384)

converter_map = {
#    ".pdf": PDFToTextConverter(),
    ".txt": TextConverter(),
    ".md": MarkdownConverter(),
 #   ".docx": DocxToTextConverter()
}

docs_dir = "./docs"
all_docs = []

for filename in os.listdir(docs_dir):
    ext = os.path.splitext(filename)[1]
    if ext in converter_map:
        filepath = os.path.join(docs_dir, filename)
        print(f"📄 Procesando {filename}...")
        documents = converter_map[ext].convert(file_path=filepath, meta={"name": filename})
        all_docs.extend(documents)

preprocessor = PreProcessor(
    clean_empty_lines=True,
    clean_whitespace=True,
    split_by="word",
    split_length=200,
    split_overlap=20,
    split_respect_sentence_boundary=True,
)

processed_docs = preprocessor.process(all_docs)

print("🔎 Generando embeddings...")
retriever = EmbeddingRetriever(
    document_store=document_store,
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    use_gpu=False
)

document_store.write_documents(processed_docs)
document_store.update_embeddings(retriever)
print("✅ Indexación completada.")
