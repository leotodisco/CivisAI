from trafilatura import fetch_url
from src.core.settings import get_settings
from pathlib import Path
import json
from urllib.parse import unquote
from trafilatura.sitemaps import sitemap_search
from urllib.parse import urljoin
import logging

_logger = logging.getLogger(__name__)
settings = get_settings()
raw_documents_path: Path = settings.assets_folder_path / settings.documents_raw_name


def normalize_url(url: str) -> str:
    return unquote(url)


def extract_html_from_url(normalized_url: str) -> str:
    try:
        html_code = fetch_url(normalized_url)
        return html_code
    except Exception as e:
        raise e


def find_urls_from_sitemap(sitemap_url: str) -> list[str]:
    return sitemap_search(sitemap_url)

def get_sitemap_from_base_url(base_url: str) -> str:
    return urljoin(base_url, "sitemap.xml")


def save_document_local(normalized_url: str, document_content: str) -> None:
    if not raw_documents_path.exists():
        raw_documents_path.parent.mkdir(parents=True, exist_ok=True)
        raw_documents_path.write_text("{}")

    with open(raw_documents_path, "r") as f:
        stored_docs = json.load(f)

    stored_docs[normalized_url] = document_content

    with open(raw_documents_path, "w") as f:
        json.dump(stored_docs, f, indent=2)
