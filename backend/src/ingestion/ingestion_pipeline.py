from typing import Optional
from src.ingestion.loader import extract_html_from_url, normalize_url
from src.ingestion.splitter import splitter
from src.ai_engines.embeddings_model import EmbeddingModel
from src.db.qdrant_store import QdrantStore

class DocumentIngestionPipeline:
    def __init__(self, 
                 urls: list[str], 
                 embedding_model: EmbeddingModel = None,
                 vector_store: QdrantStore = None):
        self.urls = [normalize_url(url) for url in urls]# if urls else []
        self.embedding_model = embedding_model or EmbeddingModel()
        self.vector_store = vector_store

    def discover_urls_from_sitemap(self):
        pass

    def run_pipeline(self):
        if not self.urls:
            raise Exception("No urls provided in pipeline")
        
        for url in self.urls:
            print(f"Processing {url=}")
            html_code = extract_html_from_url(url)
            print(f"Processing {html_code=}")
            documents = splitter.split_text(html_code)

            texts = [d.page_content for d in documents]
            embeddings = self.embedding_model.embed(texts)
            
            for doc, embedding in zip(documents, embeddings):
                metadata = doc.metadata
                original_text = doc.page_content    
                # Save embeddings as vectors in vector db
                self.vector_store.insert(original_text, embedding, metadata)



