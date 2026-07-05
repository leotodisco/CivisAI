from typing import Optional
from src.ingestion.loader import extract_html_from_url, normalize_url, find_urls_from_sitemap, get_sitemap_from_base_url
from src.ingestion.splitter import splitter
from src.ai_engines.embeddings_model import EmbeddingModel
from src.db.qdrant_store import QdrantStore
import logging

_logger = logging.getLogger(__name__)

class DocumentIngestionPipeline:
    def __init__(self,
                 base_url: str,
                 embedding_model: EmbeddingModel = None,
                 vector_store: QdrantStore = None):
        base_url = normalize_url(base_url)
        sitemap_url = get_sitemap_from_base_url(base_url)
        self.urls = find_urls_from_sitemap(sitemap_url)
        self.embedding_model = embedding_model or EmbeddingModel()
        self.vector_store = vector_store

    def run_pipeline(self):
        if not self.urls:
            raise Exception("No urls provided in pipeline")

        for url in self.urls:
            try:
                html_code = extract_html_from_url(url)
            except Exception as e:
                _logger.error(f"Error while extracting HTML from {url}. {str(e)}")
                continue

            documents = splitter.split_text(html_code)

            texts = [d.page_content for d in documents]
            embeddings = self.embedding_model.embed(texts)

            for doc, embedding in zip(documents, embeddings):
                metadata = doc.metadata
                original_text = doc.page_content
                # Save embeddings as vectors in vector db
                self.vector_store.insert(original_text, embedding, metadata)
