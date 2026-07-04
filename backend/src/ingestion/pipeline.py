from loader import extract_html_from_url
from bs4 import Tag
from langchain_text_splitters.html import HTMLSemanticPreservingSplitter


def handle_links(tag: Tag) -> str:
    text = tag.get_text(strip=True)
    url = tag.get('href', '')
    if url:
        # Formattazione personalizzata: invece del markdown standard [testo](url)
        return f" {text} (Link: {url}) "
    return f" {text} "


def handle_blockquote(tag: Tag) -> str:
    return f"\n[NOTA IMPORTANTE: {tag.get_text(strip=True)}]\n"


SEPARATORS = ["\n\n", "\n", ". ", ", ", " ", ""]
custom_tag_handlers_registry = {"a": handle_links,
                                "blockquote": handle_blockquote
                                }
DENYLIST_TARGS = ["head", "nav", "footer", "aside", "script", "style", "form"]
splitter = HTMLSemanticPreservingSplitter(headers_to_split_on=[("h1", "Header 1"), ("h2", "Header 2")],
                                          preserve_links=True,
                                          max_chunk_size=2048,
                                          chunk_overlap=200,
                                          separators=SEPARATORS,
                                          custom_handlers=custom_tag_handlers_registry,
                                          keep_separator=False,
                                          denylist_tags=DENYLIST_TARGS)

class DocumentPipeline:
    def __init__(self):
        pass
    
    def discover_urls_from_sitemap(self):
        pass
