"""Seed ChromaDB with a small collection and a document used by integration tests.

Run from the `backend` directory with the project's venv active:

uv run python scripts/seed_chroma.py

This script will attempt to import the project's configured chroma client and
create/get a collection called `documents` and add a small seed document.
"""

import sys
import traceback

try:
    # Import the project's chroma client
    from src.database import chroma_client as client
except Exception:
    try:
        # Fallback path if run from a different CWD
        from ..src.database import chroma_client as client
    except Exception:
        print("Could not import chroma_client from src.database. Make sure you're running this from the backend folder and the venv is active.")
        traceback.print_exc()
        sys.exit(1)

if client is None:
    print("No chroma client configured (client is None). Exiting.")
    sys.exit(0)

COLLECTION_NAME = "documents"
try:
    # Try get_or_create_collection (chroma client API varies by version)
    try:
        col = client.get_or_create_collection(COLLECTION_NAME)
    except Exception:
        try:
            col = client.get_collection(COLLECTION_NAME)
        except Exception:
            # Some clients require explicitly creating a collection via client.create_collection
            try:
                col = client.create_collection(COLLECTION_NAME)
            except Exception:
                col = None

    if col is None:
        print("Unable to obtain or create collection. Exiting.")
        sys.exit(1)

    # Add a small seed document
    texts = ["Seed document for integration tests: Paris is the capital of France."]
    metadatas = [{"document_id": "seed_doc", "source": "seed"}]
    ids = ["seed_doc"]

    try:
        # Some Chroma collections expose an add() method
        if hasattr(col, 'add'):
            col.add(documents=texts, metadatas=metadatas, ids=ids)
        else:
            # try add_documents / add
            try:
                col.add_documents(texts, metadatas=metadatas, ids=ids)
            except Exception:
                col.add(documents=texts, metadatas=metadatas, ids=ids)
    except Exception:
        print("Failed to add documents to collection; continuing:")
        traceback.print_exc()

    try:
        if hasattr(col, 'persist'):
            col.persist()
    except Exception:
        pass

    print(f"Seeded collection '{COLLECTION_NAME}' with document id 'seed_doc'.")
    sys.exit(0)

except Exception:
    traceback.print_exc()
    sys.exit(1)
