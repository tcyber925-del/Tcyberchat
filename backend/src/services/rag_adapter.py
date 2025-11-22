"""RAG adapter to centralize LangChain usage and provide safe stubs for tests.

This module exposes a small API that the rest of the app can use. When
LangChain is not installed or is incompatible, lightweight stubs are provided
to keep runtime stable for tests.
"""

import importlib
import warnings
from typing import Any


# Helper: detect LangChain availability in a quiet way (suppress noisy warnings)
def _detect_langchain() -> bool:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Prefer langchain_core when present (newer split)
            if importlib.util.find_spec("langchain_core") is not None:
                importlib.import_module("langchain_core")
                return True
            if importlib.util.find_spec("langchain") is not None:
                importlib.import_module("langchain")
                return True
    except Exception:
        return False
    return False


LANGCHAIN_PRESENT = _detect_langchain()


class AdapterMemory:
    def __init__(self, k: int = 5):
        # If LangChain present, wrap its ConversationBufferWindowMemory to expose chat_memory
        if LANGCHAIN_PRESENT:
            try:
                # Import lazily to avoid import-time warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    try:
                        mod = importlib.import_module("langchain_core.memory")
                        ConversationBufferWindowMemory = (
                            mod.ConversationBufferWindowMemory
                        )
                    except Exception:
                        mod = importlib.import_module("langchain.memory")
                        ConversationBufferWindowMemory = (
                            mod.ConversationBufferWindowMemory
                        )

                self.memory = ConversationBufferWindowMemory(
                    k=k, return_messages=True, memory_key="chat_memory"
                )
                # Ensure chat_memory attribute exists
                self.chat_memory = self.memory.chat_memory
            except Exception:
                self.memory = None
                self.chat_memory = _ChatMemoryStub()
        else:
            self.memory = None
            self.chat_memory = _ChatMemoryStub()

    # Backwards-compatible methods
    def add_user(self, content: str):
        try:
            if hasattr(self.chat_memory, "add_user_message"):
                self.chat_memory.add_user_message(content)
            elif hasattr(self.chat_memory, "add_message"):
                self.chat_memory.add_message({"type": "human", "content": content})
        except Exception:
            pass

    def add_ai(self, content: str):
        try:
            if hasattr(self.chat_memory, "add_ai_message"):
                self.chat_memory.add_ai_message(content)
            elif hasattr(self.chat_memory, "add_message"):
                self.chat_memory.add_message({"type": "ai", "content": content})
        except Exception:
            pass

    def get_context(self) -> list[dict]:
        msgs = getattr(self.chat_memory, "messages", [])
        out = []
        for m in msgs:
            try:
                # Normalize supported shapes
                if isinstance(m, dict):
                    role = "user" if m.get("type") in ("human", "user") else "assistant"
                    content = m.get("content", "")
                else:
                    role = (
                        "user"
                        if m.__class__.__name__.lower().startswith("human")
                        else "assistant"
                    )
                    content = getattr(m, "content", str(m))
                out.append({"role": role, "content": content})
            except Exception:
                continue
        return out


class AdapterSplitter:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        if LANGCHAIN_PRESENT:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    try:
                        mod = importlib.import_module("langchain_text_splitters")
                        RecursiveCharacterTextSplitter = (
                            mod.RecursiveCharacterTextSplitter
                        )
                    except Exception:
                        # Try the new package name
                        mod = importlib.import_module("langchain.text_splitter")
                        RecursiveCharacterTextSplitter = (
                            mod.RecursiveCharacterTextSplitter
                        )

                self.splitter = RecursiveCharacterTextSplitter(
                    chunk_size=chunk_size, chunk_overlap=chunk_overlap
                )
            except Exception:
                self.splitter = None
        else:
            self.splitter = None

    def split(self, text: str) -> list[str]:
        if self.splitter:
            try:
                return self.splitter.split_text(text)
            except Exception:
                return [text]
        return [text]

    # Backwards-compatibility: some callers call split_text
    def split_text(self, text: str) -> list[str]:
        return self.split(text)


class _ChatMemoryStub:
    """A small in-memory chat memory stub exposing the interface expected by the app.

    Methods:
    - add_message(dict|object)
    - add_user_message(str)
    - add_ai_message(str)
    - messages (list)
    - clear()
    """

    def __init__(self):
        self.messages = []

    def add_message(self, message):
        # normalize both dict and simple objects
        if isinstance(message, dict):
            self.messages.append(message)
        else:
            try:
                content = getattr(message, "content", str(message))
                mtype = (
                    getattr(message, "type", None)
                    or getattr(message, "__class__", type(message)).__name__
                )
                self.messages.append({"type": mtype, "content": content})
            except Exception:
                self.messages.append({"type": "unknown", "content": str(message)})

    def add_user_message(self, content: str):
        self.messages.append({"type": "human", "content": content})

    def add_ai_message(self, content: str):
        self.messages.append({"type": "ai", "content": content})

    def clear(self):
        self.messages = []


def create_memory(k: int = 5) -> AdapterMemory:
    return AdapterMemory(k=k)


def create_splitter(
    chunk_size: int = 1000, chunk_overlap: int = 200
) -> AdapterSplitter:
    return AdapterSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)


def create_embeddings(model_name: str = "all-MiniLM-L6-v2") -> Any | None:
    """Return an embeddings object or None when LangChain embeddings not present."""
    if LANGCHAIN_PRESENT:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                # Prefer the langchain-huggingface package when available to avoid
                # deprecation warnings for the older HuggingFace embedding classes.
                SentenceTransformerEmbeddings = None
                try:
                    mod = importlib.import_module("langchain_huggingface")
                    SentenceTransformerEmbeddings = mod.HuggingFaceEmbeddings
                except Exception:
                    # Fall back to community/langchain embeddings
                    try:
                        mod = importlib.import_module("langchain_community.embeddings")
                        SentenceTransformerEmbeddings = (
                            mod.SentenceTransformerEmbeddings
                        )
                    except Exception:
                        mod = importlib.import_module("langchain.embeddings")
                        SentenceTransformerEmbeddings = (
                            mod.SentenceTransformerEmbeddings
                        )

            # Instantiate embeddings while suppressing deprecation warnings from
            # LangChain internals (some embedding classes issue deprecation
            # warnings when langchain-huggingface is not installed).
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                emb = SentenceTransformerEmbeddings(model_name=model_name)

            # Wrap in a simple adapter exposing .embed(list[str]) for tests
            class _EmbWrapper:
                def __init__(self, inner):
                    self._inner = inner
                def embed(self, texts):
                    if hasattr(self._inner, "embed_documents"):
                        return self._inner.embed_documents(texts)
                    if hasattr(self._inner, "embed_query"):
                        return [self._inner.embed_query(t) for t in texts]
                    return [len(t) for t in texts]

            return _EmbWrapper(emb)
        except Exception:
            return None
    return None


def create_vectorstore(
    client: Any, collection_name: str = "documents", embedding=None
) -> Any | None:
    """Return a vectorstore instance or None when not available."""
    # Try to get the chroma_client from the database module
    if client is None:
        try:
            from ..database import chroma_client as _ch

            client = _ch
        except Exception:
            client = None

    # If LangChain is available, use the official Chroma vectorstore
    if LANGCHAIN_PRESENT:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    # Prefer dedicated package to avoid deprecation warnings
                    mod = importlib.import_module("langchain_chroma")
                    Chroma = mod.Chroma
                except Exception:
                    try:
                        mod = importlib.import_module("langchain_community.vectorstores")
                        Chroma = mod.Chroma
                    except Exception:
                        mod = importlib.import_module("langchain.vectorstores")
                        Chroma = mod.Chroma

            # Pass the existing client if available
            return Chroma(
                client=client,
                collection_name=collection_name,
                embedding_function=embedding,
            )
        except Exception:
            # If creating the LangChain Chroma store fails, fall through to the fallback
            pass

    # Fallback to a minimal implementation if LangChain is not available or fails
    try:
        return _FallbackVectorStore(
            client=client, collection_name=collection_name, embedding_function=embedding
        )
    except Exception:
        return None


class _FallbackVectorStore:
    """A minimal vectorstore fallback that uses chroma_client when available,
    otherwise keeps data in-memory. Exposes a subset of the LangChain Chroma API
    used by the app: add_documents, add_texts, persist, as_retriever, get,
    get_relevant_documents, count.
    """

    def __init__(
        self,
        client: Any = None,
        collection_name: str = "documents",
        embedding_function=None,
    ):
        # Delay importing database/chroma to avoid bringing heavy deps (sqlalchemy) at module import
        if client is None:
            try:
                from ..database import chroma_client as _ch

                client = _ch
            except Exception:
                client = None

        self.client = client
        self.collection_name = collection_name
        self.embedding_function = embedding_function
        self._in_memory = []  # list of (text, metadata, id)

        # If chroma client is provided and ready, try to get/create collection
        self._collection = None
        try:
            if self.client is not None:
                try:
                    self._collection = self.client.get_or_create_collection(
                        self.collection_name
                    )
                except Exception:
                    # Some chroma clients use different API
                    try:
                        self._collection = self.client.get_collection(
                            self.collection_name
                        )
                    except Exception:
                        self._collection = None
        except Exception:
            self._collection = None

    def add_documents(self, docs: list[Any]):
        texts = []
        metadatas = []
        ids = []
        for i, d in enumerate(docs):
            try:
                text = (
                    getattr(d, "page_content", None)
                    or (d.get("page_content") if isinstance(d, dict) else None)
                    or str(d)
                )
                meta = (
                    getattr(d, "metadata", None)
                    or (d.get("metadata") if isinstance(d, dict) else {})
                    or {}
                )
            except Exception:
                text = str(d)
                meta = {}
            texts.append(text)
            metadatas.append(meta)
            ids.append(meta.get("document_id") or f"doc-{len(self._in_memory) + i}")

        self.add_texts(texts, metadatas=metadatas, ids=ids)

    def add_texts(self, texts: list[str], metadatas=None, ids=None):
        metadatas = metadatas or [{} for _ in texts]
        ids = ids or [f"doc-{len(self._in_memory) + i}" for i in range(len(texts))]

        if self._collection is not None:
            try:
                # chroma collection add may accept documents and metadatas
                self._collection.add(documents=texts, metadatas=metadatas, ids=ids)
                return
            except Exception:
                pass

        # Fallback to in-memory storage
        for t, m, i in zip(texts, metadatas, ids, strict=False):
            self._in_memory.append((t, m, i))

    def persist(self):
        # chroma_client handles persistence; nothing to do for in-memory
        try:
            if self._collection is not None and hasattr(self._collection, "persist"):
                self._collection.persist()
        except Exception:
            pass

    def get(self):
        # Return list of documents/metadatas/ids similar to LangChain's Chroma.get()
        if self._collection is not None:
            try:
                res = self._collection.get(include=["documents", "metadatas", "ids"])
                return res
            except Exception:
                pass
        documents = [t for (t, m, i) in self._in_memory]
        metadatas = [m for (t, m, i) in self._in_memory]
        ids = [i for (t, m, i) in self._in_memory]
        return {"documents": documents, "metadatas": metadatas, "ids": ids}

    def as_retriever(self, **kwargs):
        # Return self as a simple retriever with a get_relevant_documents method
        return self

    def get_relevant_documents(self, query: str, k: int = 5):
        # If chroma collection is present, try vector search via query
        if self._collection is not None:
            try:
                q = self._collection.query(
                    query_texts=[query],
                    n_results=k,
                    include=["documents", "metadatas", "distances"],
                )
                docs = []
                # q may return dict with 'documents' list of lists
                docs_list = q.get("documents", [[]])[0]
                metas_list = q.get("metadatas", [[]])[0]
                dists = (
                    q.get("distances", [[]])[0]
                    if "distances" in q
                    else [None] * len(docs_list)
                )
                for text, meta, dist in zip(docs_list, metas_list, dists, strict=False):
                    doc = type("D", (), {})()
                    doc.page_content = text
                    doc.metadata = meta
                    # Convert distance to score (simple inverse)
                    score = None
                    try:
                        if dist is not None:
                            score = 1.0 / (1.0 + float(dist))
                    except Exception:
                        score = None
                    doc.score = score
                    docs.append(doc)
                return docs
            except Exception:
                pass

        # Simple keyword-based ranking for in-memory data
        scored = []
        for i, (text, meta, _id) in enumerate(self._in_memory):
            score = 1.0 if query.lower() in text.lower() else max(0.0, 1.0 - (i * 0.1))
            doc = type("D", (), {})()
            doc.page_content = text
            doc.metadata = meta
            doc.score = score
            scored.append(doc)

        scored.sort(key=lambda d: getattr(d, "score", 0), reverse=True)
        return scored[:k]

    def count(self):
        if self._collection is not None:
            try:
                return self._collection.count()
            except Exception:
                pass
        return len(self._in_memory)


class AIServiceLLMAdapter:
    """Minimal adapter that exposes a .generate(prompt) method backed by the AI service."""

    def __init__(self, ai_service):
        self.ai_service = ai_service

    def generate(self, prompt: str) -> str:
        # Support sync or async AI service
        try:
            if hasattr(self.ai_service, "generate_response"):
                # ai_service.generate_response may be async; try sync first
                result = self.ai_service.generate_response(prompt=prompt)
                # If coroutine, run it
                if hasattr(result, "__await__"):
                    import asyncio
                    try:
                        # Prefer asyncio.run when not in a running loop
                        return asyncio.run(result)
                    except RuntimeError:
                        # Fallback when already inside a loop: create a new loop
                        loop = asyncio.new_event_loop()
                        try:
                            return loop.run_until_complete(result)
                        finally:
                            loop.close()
                return result
        except Exception:
            pass
        # Last resort: str() the service
        return str(self.ai_service)
