from bs4 import Tag
from langchain_text_splitters.html import HTMLSemanticPreservingSplitter


def handle_links(tag: Tag) -> str:
    text = tag.get_text(strip=True)
    url = tag.get('href', '')
    if url:
        return f" {text} (Link: {url}) "
    return f" {text} "


def handle_blockquote(tag: Tag) -> str:
    return f"\n[Important: {tag.get_text(strip=True)}]\n"


SEPARATORS = ["\n\n", "\n", ". ", ", ", " ", ""]
TAG_HANDLER_REGISTRY = {"a": handle_links,
                        "blockquote": handle_blockquote
                        }
DENYLIST_TARGS = ["head", "nav", "footer", "aside", "script", "style", "form"]

splitter = HTMLSemanticPreservingSplitter(headers_to_split_on=[("h1", "Header 1"), ("h2", "Header 2")],
                                          preserve_links=True,
                                          max_chunk_size=2048,
                                          chunk_overlap=200,
                                          separators=SEPARATORS,
                                          custom_handlers=TAG_HANDLER_REGISTRY,
                                          keep_separator=False,
                                          denylist_tags=DENYLIST_TARGS)
