"""
Knowledge Base loader.

Reads documents from knowledge/{prompts,facts,procedures}/,
using registry.json files in facts/ and procedures/ to decide
which documents are always loaded into the system prompt and
which are only retrieved via semantic search.
"""

import json
import logging
import os

from config import KNOWLEDGE_BASE_DIR

logger = logging.getLogger(__name__)

PROMPTS_DIR = os.path.join(KNOWLEDGE_BASE_DIR, "prompts")
FACTS_DIR = os.path.join(KNOWLEDGE_BASE_DIR, "facts")
PROCEDURES_DIR = os.path.join(KNOWLEDGE_BASE_DIR, "procedures")


def _read_file(path):
    if not os.path.exists(path):
        logger.warning("File not found, skipping: %s", path)
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def _load_registry(directory):
    registry_path = os.path.join(directory, "registry.json")
    if not os.path.exists(registry_path):
        return []
    with open(registry_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            logger.warning(
                "Malformed registry.json in %s (%s). Skipping this directory.",
                directory, e
            )
            return []


def load_prompts():
    """Loads every document from knowledge/prompts/. Always loaded, no registry."""
    documents = []
    if not os.path.isdir(PROMPTS_DIR):
        return documents

    for filename in sorted(os.listdir(PROMPTS_DIR)):
        path = os.path.join(PROMPTS_DIR, filename)
        if not os.path.isfile(path):
            continue
        doc_id, _ = os.path.splitext(filename)
        content = _read_file(path)
        if content is None:
            continue
        documents.append({
            "id": doc_id,
            "name": doc_id.replace("_", " ").title(),
            "content": content
        })
    return documents


def _load_section_documents(directory, only_always_load=None):
    documents = []
    for entry in _load_registry(directory):
        if only_always_load is not None and entry.get("always_load") != only_always_load:
            continue

        file_path = os.path.join(directory, f"{entry['id']}.md")
        content = _read_file(file_path)
        if content is None:
            continue

        documents.append({
            "id": entry["id"],
            "name": entry["name"],
            "always_load": entry.get("always_load", False),
            "content": content
        })
    return documents


def load_facts(only_always_load=None):
    return _load_section_documents(FACTS_DIR, only_always_load)


def load_procedures(only_always_load=None):
    return _load_section_documents(PROCEDURES_DIR, only_always_load)