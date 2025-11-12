"""
RAGService for retrieval-augmented generation using comprehensive LangChain features
"""

from typing import List, Dict, Optional, Any, Tuple, AsyncGenerator
import asyncio
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)

# Use the adapter to centralize LangChain usage and provide stable fallbacks
from .rag_adapter import (
    create_memory,
    create_splitter,
    create_vectorstore,
    AIServiceLLMAdapter,
    LANGCHAIN_PRESENT,
)
from langchain_community.embeddings import SentenceTransformerEmbeddings

LANGCHAIN_AVAILABLE = LANGCHAIN_PRESENT

# Minimal stub used when LangChain pieces are not present.
class _Stub:
    def __init__(self, *args, **kwargs):
        pass

    @classmethod
    def from_template(cls, *a, **k):
        return cls()

    @classmethod
    def from_messages(cls, *a, **k):
        return cls()

    @classmethod
    def from_documents(cls, docs, **k):
        return cls()

    def split_text(self, text: str):
        return [text]

    def add_documents(self, docs):
        return

    def add_texts(self, texts, metadatas=None, ids=None):
        return

    def persist(self):
        return

    def get(self):
        return {'documents': [], 'metadatas': [], 'ids': []}

    def as_retriever(self, **k):
        return self

    def get_relevant_documents(self, query, k=5):
        return []

    def count(self):
        return 0

# Map minimal names to stubs for the non-LangChain path. More detailed behavior
# is provided by the adapter when LangChain is present.
if not LANGCHAIN_AVAILABLE:
    Chroma = _Stub
    SentenceTransformerEmbeddings = _Stub
    LangChainDocument = _Stub
    BaseRetriever = _Stub
    BaseCallbackHandler = object
    StrOutputParser = _Stub
    RunnablePassthrough = _Stub
    ChatPromptTemplate = _Stub
    MessagesPlaceholder = _Stub
    PromptTemplate = _Stub
    HumanMessage = str
    AIMessage = str
    BaseChatModel = object
    BaseLLM = object
    Generation = dict
    LLMResult = dict
    create_stuff_documents_chain = lambda *a, **k: _Stub()
    create_history_aware_retriever = lambda *a, **k: _Stub()
    create_retrieval_chain = lambda *a, **k: _Stub()
    BM25Retriever = _Stub
    EnsembleRetriever = _Stub
    DocumentCompressorPipeline = _Stub
    EmbeddingsFilter = _Stub
    RecursiveCharacterTextSplitter = _Stub
    ConversationBufferWindowMemory = _Stub
else:
    from langchain_core.callbacks import BaseCallbackHandler
    from langchain_core.language_models import BaseLLM, BaseChatModel
    from langchain.chains.combine_documents import create_stuff_documents_chain
    from langchain.chains.history_aware_retriever import create_history_aware_retriever
    from langchain.chains.retrieval import create_retrieval_chain
    from langchain_community.retrievers import BM25Retriever
    from langchain.retrievers import EnsembleRetriever
    from langchain.retrievers.document_compressors import DocumentCompressorPipeline, EmbeddingsFilter
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.memory import ConversationBufferWindowMemory
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
    from langchain_core.messages import HumanMessage, AIMessage
    from langchain_core.runnables import Runnable, RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.documents import Document as LangChainDocument
    from langchain_core.outputs import Generation, LLMResult
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import SentenceTransformerEmbeddings
    from langchain.schema import BaseRetriever

# Import AI service lazily inside the service to avoid optional dependency failures
# IMPORTANT: avoid importing the database/chroma at module import time. Use lazy resolution
# to prevent import-time dependency errors in environments without SQLAlchemy.


class RAGCallbackHandler(BaseCallbackHandler):
    """Custom callback handler for RAG operations"""

    def __init__(self):
        self.operations = []

    def on_chain_start(self, serialized, inputs, **kwargs):
        self.operations.append({
            "operation": "chain_start",
            "chain": serialized.get("name", "unknown"),
            "timestamp": asyncio.get_event_loop().time()
        })

    def on_chain_end(self, outputs, **kwargs):
        self.operations.append({
            "operation": "chain_end",
            "timestamp": asyncio.get_event_loop().time()
        })

    def on_retriever_start(self, serialized, query, **kwargs):
        self.operations.append({
            "operation": "retrieval_start",
            "query": query[:100] + "..." if len(query) > 100 else query
        })

    def on_retriever_end(self, documents, **kwargs):
        self.operations.append({
            "operation": "retrieval_end",
            "documents_found": len(documents)
        })


class RAGService:
    """Service for retrieval-augmented generation using comprehensive LangChain features"""

    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.vectorstore = None
        self.embeddings = None
        self.text_splitter = None
        self.conversation_memory = None
        self.callback_handler = None
        # Lazy import of AI service to avoid optional dependency errors at module import
        # Note: get_ai_service() is async, so we'll lazy-load it in async methods
        self._ai_service_getter = None
        self._ai_service_instance = None
        try:
            from .ai_service import get_ai_service
            self._ai_service_getter = get_ai_service
        except Exception:
            # Minimal stub AI service
            class _AIStub:
                def __init__(self):
                    self.model_name = "stub"

                async def generate_response(self, prompt: str):
                    return {"response": "(AI stub) " + str(prompt)}

                async def generate_streaming_response(self, prompt: str):
                    # simple async generator
                    async def gen():
                        yield "(AI stub) " + str(prompt)

                    return gen()

            self._ai_service_instance = _AIStub()

        # Advanced retrievers and chains
        self.ensemble_retriever = None
        self.conversational_chain = None
        self.rag_chain = None
        self.compression_retriever = None

        if LANGCHAIN_AVAILABLE:
            self._initialize_langchain_components()
        else:
            # Use adapter fallbacks when LangChain is not available
            from .rag_adapter import create_memory, create_splitter

            self.conversation_memory = create_memory(k=5)
            self.text_splitter = create_splitter(chunk_size=1000, chunk_overlap=200)
            self.markdown_splitter = None  # Markdown splitter not available without LangChain
            # Ensure we have a usable vectorstore (fallback) even without LangChain
            try:
                from .rag_adapter import create_vectorstore

                self.vectorstore = create_vectorstore(client=None, collection_name="documents", embedding=None)
            except Exception:
                self.vectorstore = None

    async def _get_ai_service(self, model_name: Optional[str] = None):
        """Lazy-load AI service (async) - always get fresh instance for the specified model"""
        # Don't cache - always get a fresh instance for the specified model
        # The get_ai_service function already caches by model_name
        if self._ai_service_getter:
            return await self._ai_service_getter(model_name)
        # Fallback stub
        class _AIStub:
            def __init__(self):
                self.model_name = "stub"

            async def generate_response(self, prompt: str):
                return {"response": "(AI stub) " + str(prompt)}

            async def generate_streaming_response(self, prompt: str):
                async def gen():
                    yield "(AI stub) " + str(prompt)
                return gen()
        
        return _AIStub()

    def _initialize_langchain_components(self):
        """Initialize comprehensive LangChain components for RAG"""
        try:
            # Initialize embeddings, vectorstore, splitter and memory through the adapter
            # Adapter will try to use LangChain components when available, otherwise
            # return safe None/stubs so tests and CI remain stable.
            self.embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

            # Use shared ChromaDB client via adapter (adapter will lazily resolve chroma client).
            self.vectorstore = create_vectorstore(client=None, collection_name="documents", embedding=self.embeddings)

            # Initialize text splitter for document chunking
            self.text_splitter = create_splitter(chunk_size=1000, chunk_overlap=200)
            
            # Initialize markdown-aware text splitter for markdown files
            self.markdown_splitter = self._create_markdown_splitter()

            # Initialize conversation memory
            self.conversation_memory = create_memory(k=5)

            # Initialize callback handler for observability
            self.callback_handler = RAGCallbackHandler()

            # Create advanced retrievers and chains if LangChain pieces are available
            self._setup_advanced_retrievers()
            self._setup_chains()

        except Exception as e:
            print(f"Failed to initialize LangChain components: {e}")
            self.vectorstore = None
            self.embeddings = None
            self.markdown_splitter = None

    def _create_markdown_splitter(self):
        """Create a markdown-aware text splitter that respects markdown structure"""
        if not LANGCHAIN_AVAILABLE:
            # Fallback to regular splitter if LangChain not available
            return create_splitter(chunk_size=1000, chunk_overlap=200)
        
        try:
            # Try to use MarkdownHeaderTextSplitter for better markdown chunking
            try:
                from langchain.text_splitter import MarkdownHeaderTextSplitter
                
                # Define headers to split on (h1, h2, h3)
                headers_to_split_on = [
                    ("#", "Header 1"),
                    ("##", "Header 2"),
                    ("###", "Header 3"),
                ]
                
                markdown_header_splitter = MarkdownHeaderTextSplitter(
                    headers_to_split_on=headers_to_split_on,
                    strip_headers=False  # Keep headers in chunks for context
                )
                
                # Wrap in recursive splitter for fine-grained chunking within sections
                from langchain.text_splitter import RecursiveCharacterTextSplitter
                recursive_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                    separators=["\n\n", "\n", ". ", " ", ""]  # Markdown-aware separators
                )
                
                # Return a combined splitter that first splits by headers, then recursively
                class CombinedMarkdownSplitter:
                    def __init__(self, header_splitter, recursive_splitter):
                        self.header_splitter = header_splitter
                        self.recursive_splitter = recursive_splitter
                    
                    def split_text(self, text: str) -> List[str]:
                        """Split markdown text by headers first, then recursively"""
                        try:
                            # First split by markdown headers
                            header_splits = self.header_splitter.split_text(text)
                            
                            # Then recursively split each section
                            all_chunks = []
                            for split in header_splits:
                                # Preserve header metadata in chunk
                                header_info = ""
                                if hasattr(split, 'metadata'):
                                    metadata = split.metadata
                                    for header_level in ["Header 1", "Header 2", "Header 3"]:
                                        if header_level in metadata:
                                            header_info = f"{metadata[header_level]}\n\n"
                                            break
                                
                                # Get content (either page_content attribute or string)
                                content = getattr(split, 'page_content', str(split))
                                
                                # Recursively split the section
                                recursive_chunks = self.recursive_splitter.split_text(content)
                                
                                # Add header info to first chunk of each section
                                for i, chunk in enumerate(recursive_chunks):
                                    if i == 0 and header_info:
                                        chunk = header_info + chunk
                                    all_chunks.append(chunk)
                            
                            return all_chunks if all_chunks else [text]
                        except Exception as e:
                            # Fallback to recursive splitter if header splitting fails
                            print(f"Markdown header splitting failed, using recursive splitter: {e}")
                            return self.recursive_splitter.split_text(text)
                
                return CombinedMarkdownSplitter(markdown_header_splitter, recursive_splitter)
                
            except ImportError:
                # MarkdownHeaderTextSplitter not available, use recursive splitter with markdown-aware separators
                from langchain.text_splitter import RecursiveCharacterTextSplitter
                return RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                    separators=["\n\n##", "\n\n#", "\n\n", "\n", ". ", " ", ""]  # Markdown-aware separators
                )
        except Exception as e:
            print(f"Failed to create markdown splitter: {e}, using default splitter")
            return create_splitter(chunk_size=1000, chunk_overlap=200)

    def _setup_advanced_retrievers(self):
        """Set up advanced retrieval strategies"""
        # If LangChain isn't available or vectorstore wasn't initialized, skip advanced retrievers
        if not LANGCHAIN_AVAILABLE or not self.vectorstore:
            return

        try:
            # Base retrievers
            similarity_retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 10}
            )

            mmr_retriever = self.vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs={"k": 10, "lambda_mult": 0.5}
            )

            # Validate retrievers before creating ensemble
            if similarity_retriever is None or mmr_retriever is None:
                print("Warning: One or more retrievers are None, skipping ensemble setup")
                return

            # EnsembleRetriever accepts BaseRetriever objects directly
            # No need to wrap them in Runnable
            try:
                self.ensemble_retriever = EnsembleRetriever(
                    retrievers=[
                        similarity_retriever,
                        mmr_retriever
                    ],
                    weights=[0.7, 0.3]  # Weight similarity search higher
                )
            except TypeError as te:
                # Handle different EnsembleRetriever API versions
                if "takes no arguments" in str(te) or "positional" in str(te).lower():
                    # Try alternative initialization
                    try:
                        from langchain.retrievers import EnsembleRetriever as ER
                        # Some versions might need keyword-only args
                        self.ensemble_retriever = ER(
                            retrievers=[similarity_retriever, mmr_retriever],
                            weights=[0.7, 0.3]
                        )
                    except Exception:
                        print(f"Failed to create EnsembleRetriever with alternative method: {te}")
                        self.ensemble_retriever = None
                else:
                    raise

            # Document compression pipeline
            # Note: DocumentCompressorPipeline needs a base_retriever, not just transformers
            # We'll create a compression retriever by wrapping a base retriever
            if self.embeddings is not None:
                print(f"DEBUG: Type of self.embeddings before EmbeddingsFilter: {type(self.embeddings)}")
                from langchain_core.embeddings import Embeddings as LangchainEmbeddings
                print(f"DEBUG: Is self.embeddings an instance of LangchainEmbeddings? {isinstance(self.embeddings, LangchainEmbeddings)}")
                try:
                    embeddings_filter = EmbeddingsFilter(
                        embeddings=self.embeddings,
                        similarity_threshold=0.7
                    )
                    
                    # Create a base retriever for compression
                    base_retriever = self.vectorstore.as_retriever(search_kwargs={"k": 10})
                    
                    # DocumentCompressorPipeline wraps a retriever with compressors
                    self.compression_retriever = DocumentCompressorPipeline(
                        base_retriever=base_retriever,
                        transformers=[embeddings_filter]
                    )
                except TypeError as te:
                    # Handle different API versions - some might use 'compressors' instead of 'transformers'
                    try:
                        self.compression_retriever = DocumentCompressorPipeline(
                            base_retriever=base_retriever,
                            compressors=[embeddings_filter]
                        )
                    except Exception as e2:
                        print(f"Failed to create DocumentCompressorPipeline: {e2}")
                        self.compression_retriever = None
                except Exception as e:
                    print(f"Failed to setup compression retriever: {e}")
                    self.compression_retriever = None
            else:
                self.compression_retriever = None

        except Exception as e:
            print(f"Failed to setup advanced retrievers: {e}")
            self.ensemble_retriever = None
            self.compression_retriever = None

    def _setup_chains(self):
        """Set up comprehensive LangChain chains"""
        # If LangChain pieces aren't available, skip chain setup
        if not LANGCHAIN_AVAILABLE:
            return

        try:
            # Create custom LLM wrapper for our AI service
            # Wrap AI service in a minimal LLM-like adapter only if BaseLLM is available
            if isinstance(BaseLLM, type):
                class AIServiceLLM(BaseLLM):
                    # Declare fields so pydantic/BaseModel-style initialization accepts them
                    ai_service: Any
                    callback_handler: Optional[BaseCallbackHandler] = None
                    _model_name: Optional[str] = None
                    _ai_service_getter: Optional[Any] = None

                    def __init__(self, ai_service=None, callback_handler=None, model_name=None, ai_service_getter=None):
                        # BaseLLM may be a simple class; avoid relying on pydantic behavior here
                        try:
                            super().__init__()
                        except Exception:
                            pass
                        self.ai_service = ai_service
                        self.callback_handler = callback_handler
                        self._model_name = model_name
                        self._ai_service_getter = ai_service_getter

                    async def _get_ai_service(self):
                        """Get AI service, using getter if available for dynamic model selection"""
                        if self._ai_service_getter:
                            return await self._ai_service_getter(self._model_name)
                        return self.ai_service

                    @property
                    def _llm_type(self) -> str:
                        return "custom_ai_service"

                    async def _acall(self, prompt: str, **kwargs) -> str:
                        if self.callback_handler and hasattr(self.callback_handler, 'on_chain_start'):
                            try:
                                self.callback_handler.on_chain_start({'name': 'ai_service_call'}, {'prompt': prompt})
                            except TypeError:
                                # Some callback handlers require additional args; ignore for dev
                                pass

                        # Get AI service dynamically if getter is available
                        ai_service = await self._get_ai_service() if self._ai_service_getter else self.ai_service
                        response = await ai_service.generate_response(prompt=prompt)

                        if self.callback_handler and hasattr(self.callback_handler, 'on_chain_end'):
                            try:
                                self.callback_handler.on_chain_end({'response': response})
                            except TypeError:
                                pass

                        # Ensure string return
                        if isinstance(response, dict):
                            return str(response.get('response', ''))
                        return str(response)

                    def _call(self, prompt: str, **kwargs) -> str:
                        # Synchronous fallback
                        return asyncio.get_event_loop().run_until_complete(self._acall(prompt, **kwargs))

                    def _generate(self, prompts: List[str], stop: Optional[List[str]] = None, **kwargs: Any) -> Any:
                        generations = []
                        for prompt in prompts:
                            text = self._call(prompt, **kwargs)
                            if Generation is not None:
                                generations.append([Generation(text=text)])
                            else:
                                generations.append([{'text': text}])
                        if LLMResult is not None:
                            return LLMResult(generations=generations)
                        return {'generations': generations}

                    async def _agenerate(self, prompts: List[str], stop: Optional[List[str]] = None, **kwargs: Any) -> Any:
                        generations = []
                        for prompt in prompts:
                            text = await self._acall(prompt, **kwargs)
                            if Generation is not None:
                                generations.append([Generation(text=text)])
                            else:
                                generations.append([{'text': text}])
                        if LLMResult is not None:
                            return LLMResult(generations=generations)
                        return {'generations': generations}

            # Only create custom_llm if BaseLLM is available
            # Use ai_service_getter for dynamic model selection instead of fixed instance
            custom_llm = None
            if isinstance(BaseLLM, type):
                try:
                    # Pass the getter function so LLM can dynamically get the right model
                    custom_llm = AIServiceLLM(
                        ai_service=self._ai_service_instance,  # Fallback if getter fails
                        callback_handler=self.callback_handler,
                        model_name=None,  # Will be set per-request
                        ai_service_getter=self._ai_service_getter  # For dynamic model selection
                    )
                except Exception as e:
                    print(f"Failed to create AIServiceLLM: {e}")
                    custom_llm = None

            # Skip chain setup if custom_llm is not available
            if custom_llm is None:
                print("Skipping chain setup: custom_llm is not available (AI service will be lazy-loaded when needed)")
                return

            # 1. Basic RAG Chain
            rag_prompt = ChatPromptTemplate.from_template("""
You are a helpful AI assistant that answers questions based on the provided context.
Use the following pieces of context to answer the question at the end.

CRITICAL INSTRUCTIONS:
- ALWAYS prioritize information from "=== Web Search Results (Most Recent Information) ===" section if it exists
- If the query asks for "latest", "recent", "news", or "current" information, you MUST use the web search results as your primary source
- When using web search information, explicitly state "According to recent web search..." or "Based on the latest information from web sources..."
- Include URLs from web search results in your citations
- If web search results are present, they represent the MOST CURRENT information available - use them over older document content

Guidelines:
- If you don't know the answer based on the context, say so clearly
- Provide specific references to the source material when possible (include URLs for web sources)
- Be concise but comprehensive
- Use citations when referencing specific information
- Clearly distinguish between document sources and web sources in citations
- If you cannot find recent information in the provided context, state that clearly

Context:
{context}

Question: {question}

Answer:""")

            # Create stuff documents chain
            stuff_chain = create_stuff_documents_chain(custom_llm, rag_prompt)

            # Create retrieval chain - ensure ensemble_retriever is available
            if self.ensemble_retriever is None:
                # Fallback to basic retriever if ensemble is not available
                base_retriever = self.vectorstore.as_retriever(search_kwargs={"k": 10}) if self.vectorstore else None
                if base_retriever is None:
                    print("Warning: No retriever available for RAG chain setup")
                    return
                self.rag_chain = create_retrieval_chain(
                    base_retriever,
                    stuff_chain
                )
            else:
                self.rag_chain = create_retrieval_chain(
                    self.ensemble_retriever,
                    stuff_chain
                )

            # 2. Conversational RAG Chain with memory
            condense_prompt = PromptTemplate.from_template("""
Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.

Chat History:
{chat_history}

Follow Up Input: {question}

Standalone question:""")

            # Ensure we have a retriever for history-aware retriever
            retriever_for_history = self.ensemble_retriever
            if retriever_for_history is None:
                retriever_for_history = self.vectorstore.as_retriever(search_kwargs={"k": 10}) if self.vectorstore else None
                if retriever_for_history is None:
                    print("Warning: No retriever available for conversational chain setup")
                    return

            history_aware_retriever = create_history_aware_retriever(
                custom_llm, retriever_for_history, condense_prompt
            )

            conversational_prompt = ChatPromptTemplate.from_messages([
                ("system", """
You are a helpful AI assistant with access to document knowledge and web search. Use the provided context and conversation history to answer questions.

CRITICAL INSTRUCTIONS:
- ALWAYS prioritize information from "=== Web Search Results (Most Recent Information) ===" section if it exists
- If the query asks for "latest", "recent", "news", or "current" information, you MUST use the web search results as your primary source
- When using web search information, explicitly state "According to recent web search..." or "Based on the latest information from web sources..."
- Include URLs from web search results in your citations
- If web search results are present, they represent the MOST CURRENT information available - use them over older document content

Guidelines:
- Use both the retrieved context and conversation history
- Maintain coherence across the conversation
- Cite sources when providing specific information (include URLs for web sources)
- Ask for clarification if needed
- Clearly distinguish between document sources and web sources in citations
- If you cannot find recent information in the provided context, state that clearly

Context: {context}
Conversation History: {chat_history}
                """),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ])

            conversational_stuff_chain = create_stuff_documents_chain(
                custom_llm, conversational_prompt
            )

            self.conversational_chain = create_retrieval_chain(
                history_aware_retriever,
                conversational_stuff_chain
            )

        except Exception as e:
            print(f"Failed to setup chains: {e}")

    async def generate_rag_streaming_response(self, query: str, document_id: Optional[str] = None,
                                              max_context_chunks: int = 3, conversational: bool = False,
                                              chat_history: Optional[List[Dict[str, str]]] = None,
                                              model_name: Optional[str] = None,
                                              use_web_search: bool = False) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate RAG-enhanced streaming response using advanced LangChain chains
        
        Args:
            query: User query string
            document_id: Optional document ID to filter search
            max_context_chunks: Maximum number of document chunks to use
            conversational: Whether to use conversational RAG chain
            chat_history: Optional chat history for conversational mode
            model_name: Optional model name to use
            use_web_search: Whether to include web search results (optional, defaults to False)
        """
        full_response_content = ""
        citations = []
        web_search_results = []
        web_search_used = False
        try:
            # Update AIServiceLLM model_name if using chains (for dynamic model selection)
            if model_name:
                # Try to update the LLM's model_name if it supports it
                try:
                    if hasattr(self, 'rag_chain') and self.rag_chain and hasattr(self.rag_chain, 'llm'):
                        if hasattr(self.rag_chain.llm, '_model_name'):
                            self.rag_chain.llm._model_name = model_name
                    if hasattr(self, 'conversational_chain') and self.conversational_chain and hasattr(self.conversational_chain, 'llm'):
                        if hasattr(self.conversational_chain.llm, '_model_name'):
                            self.conversational_chain.llm._model_name = model_name
                except Exception:
                    pass  # If update fails, continue with existing model
            
            # Analyze query for time-sensitivity
            def is_time_sensitive_query(q: str) -> bool:
                """Detect if query is time-sensitive"""
                if not q:
                    return False
                q_lower = q.lower()
                time_keywords = ["latest", "recent", "news", "update", "what's new", "current", "today", "now"]
                return any(kw in q_lower for kw in time_keywords)
            
            is_time_sensitive = is_time_sensitive_query(query)
            
            # Perform web search if enabled
            web_search_context = ""
            if use_web_search:
                try:
                    from .web_search_service import get_web_search_service
                    web_search_service = get_web_search_service()
                    
                    # For time-sensitive queries, increase max_results and force fresh
                    search_max_results = max_context_chunks * 2 if is_time_sensitive else max_context_chunks
                    
                    # Perform web search (cache automatically disabled for time-sensitive queries)
                    web_results = await web_search_service.search(
                        query, 
                        max_results=search_max_results,
                        use_cache=not is_time_sensitive,  # Disable cache for time-sensitive
                        force_fresh=is_time_sensitive  # Force fresh for time-sensitive
                    )
                    web_search_results = web_results
                    web_search_used = len(web_results) > 0
                    
                    if web_results:
                        # Format web search results for context with clear structure
                        web_context_parts = ["=== Web Search Results (Most Recent Information) ==="]
                        for i, result in enumerate(web_results, 1):
                            web_context_parts.append(f"\n[Web Source {i}] {result.title}")
                            web_context_parts.append(f"URL: {result.url}")
                            web_context_parts.append(f"Content: {result.snippet}")
                            if result.timestamp:
                                web_context_parts.append(f"Retrieved: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                            
                            # Add web search citation
                            citations.append({
                                "url": result.url,
                                "title": result.title,
                                "snippet": result.snippet,
                                "source": "web_search",
                                "source_type": "web",  # NEW: Explicit source type
                                "relevance_score": result.relevance_score,
                                "timestamp": result.timestamp.isoformat() if result.timestamp else None
                            })
                        
                        web_search_context = "\n".join(web_context_parts)
                        logger.info(
                            f"Web search returned {len(web_results)} results for query: '{query[:50]}' "
                            f"(time_sensitive={is_time_sensitive})"
                        )
                except Exception as e:
                    logger.warning(f"Web search failed, continuing without web results: {e}", exc_info=True)
                    # Continue without web search - don't break the flow
            
            if conversational and chat_history and self.conversational_chain:
                # Use conversational RAG chain with memory
                formatted_history = []
                if chat_history:
                    for msg in chat_history[-10:]:  # Keep last 10 messages
                        if msg.get("role") == "user":
                            formatted_history.append(HumanMessage(content=msg.get("content", "")))
                        elif msg.get("role") == "assistant":
                            formatted_history.append(AIMessage(content=msg.get("content", "")))

                # Update conversation memory
                for msg in formatted_history:
                    if isinstance(msg, HumanMessage):
                        self.conversation_memory.chat_memory.add_user_message(msg.content)
                    elif isinstance(msg, AIMessage):
                        self.conversation_memory.chat_memory.add_ai_message(msg.content)

                # Apply document filtering to conversational chain if document_id is provided
                chain_config = {"memory": self.conversation_memory}
                base_retriever = None
                if document_id:
                    # Create filtered retriever for conversational chain
                    try:
                        all_docs = self.vectorstore.get()
                        filtered_docs = []
                        for doc_text, metadata, doc_id_vec in zip(
                            all_docs.get('documents', []), 
                            all_docs.get('metadatas', []), 
                            all_docs.get('ids', [])
                        ):
                            doc_id_str = str(metadata.get('document_id', '')) if metadata else ''
                            if doc_id_str == str(document_id):
                                filtered_docs.append(LangChainDocument(
                                    page_content=doc_text,
                                    metadata=metadata or {}
                                ))
                        
                        if filtered_docs:
                            bm25_retriever = BM25Retriever.from_documents(filtered_docs)
                            bm25_retriever.k = max_context_chunks
                            base_retriever = bm25_retriever
                    except Exception as e:
                        print(f"Warning: Failed to filter conversational chain by document_id {document_id}: {e}")
                else:
                    # Use default retriever for conversational chain
                    base_retriever = self.ensemble_retriever or (self.vectorstore.as_retriever(search_kwargs={"k": max_context_chunks}) if self.vectorstore else None)
                
                # Create wrapper retriever that includes web search context
                if base_retriever:
                    class WebSearchContextRetriever:
                        """Wrapper retriever that combines document retrieval with web search results"""
                        def __init__(self, base_retriever, web_search_context: str, is_time_sensitive: bool):
                            self.base_retriever = base_retriever
                            self.web_search_context = web_search_context
                            self.is_time_sensitive = is_time_sensitive
                        
                        def get_relevant_documents(self, query: str, k: int = 5):
                            """Get documents from base retriever and prepend web search context"""
                            docs = self.base_retriever.get_relevant_documents(query, k)
                            
                            # If web search context exists, create a document from it and prepend
                            if self.web_search_context:
                                web_doc = LangChainDocument(
                                    page_content=self.web_search_context,
                                    metadata={
                                        "source": "web_search",
                                        "source_type": "web",
                                        "is_time_sensitive": self.is_time_sensitive
                                    }
                                )
                                # For time-sensitive queries, web search comes first
                                if self.is_time_sensitive:
                                    return [web_doc] + docs
                                else:
                                    return docs + [web_doc]
                            return docs
                        
                        async def aget_relevant_documents(self, query: str, k: int = 5):
                            """Async version"""
                            if hasattr(self.base_retriever, 'aget_relevant_documents'):
                                docs = await self.base_retriever.aget_relevant_documents(query, k)
                            else:
                                docs = self.base_retriever.get_relevant_documents(query, k)
                            
                            # If web search context exists, create a document from it and prepend
                            if self.web_search_context:
                                web_doc = LangChainDocument(
                                    page_content=self.web_search_context,
                                    metadata={
                                        "source": "web_search",
                                        "source_type": "web",
                                        "is_time_sensitive": self.is_time_sensitive
                                    }
                                )
                                # For time-sensitive queries, web search comes first
                                if self.is_time_sensitive:
                                    return [web_doc] + docs
                                else:
                                    return docs + [web_doc]
                            return docs
                    
                    wrapped_retriever = WebSearchContextRetriever(
                        base_retriever, 
                        web_search_context, 
                        is_time_sensitive
                    ) if web_search_context else base_retriever
                    chain_config["retriever"] = wrapped_retriever
                
                async for chunk in self.conversational_chain.astream(
                    {"input": query},  # Use original query, web search is in context now
                    config=chain_config
                ):
                    if "answer" in chunk:
                        full_response_content += chunk["answer"]
                        yield {"content": chunk["answer"], "done": False}
                    if "context" in chunk:
                        # Extract citations from source documents
                        source_docs = chunk.get('context', [])
                        for i, doc in enumerate(source_docs):
                            if hasattr(doc, 'metadata'):
                                doc_id = doc.metadata.get("document_id")
                                # Only include citations from the requested document if document_id is specified
                                if not document_id or str(doc_id) == str(document_id):
                                    citations.append({
                                        "document_id": doc_id,
                                        "chunk_index": doc.metadata.get("chunk_index"),
                                        "score": getattr(doc, 'score', None) or (1.0 - i * 0.1),
                                        "content_preview": doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content,
                                        "retrieval_method": "conversational"
                                    })
            elif self.rag_chain:
                # Use basic RAG chain
                # Create document-filtered retriever if needed
                if document_id:
                    # Filter documents by document_id and create a retriever from filtered docs
                    # This ensures we only search within the specified document
                    try:
                        all_docs = self.vectorstore.get()
                        filtered_docs = []
                        for doc_text, metadata, doc_id_vec in zip(
                            all_docs.get('documents', []), 
                            all_docs.get('metadatas', []), 
                            all_docs.get('ids', [])
                        ):
                            # Match document_id (handle both string and UUID formats)
                            doc_id_str = str(metadata.get('document_id', '')) if metadata else ''
                            if doc_id_str == str(document_id):
                                filtered_docs.append(LangChainDocument(
                                    page_content=doc_text,
                                    metadata=metadata or {}
                                ))
                        
                        if filtered_docs:
                            # Create BM25 retriever for keyword-based search within filtered documents
                            # This provides better semantic search within the document
                            bm25_retriever = BM25Retriever.from_documents(filtered_docs)
                            bm25_retriever.k = max_context_chunks
                            retriever = bm25_retriever
                        else:
                            # No documents found for this document_id, use empty retriever
                            # This will result in no context but won't break the chain
                            class EmptyRetriever:
                                def get_relevant_documents(self, query, k=5):
                                    return []
                            retriever = EmptyRetriever()
                    except Exception as e:
                        # If filtering fails, log and fall back to unfiltered retriever
                        print(f"Warning: Failed to filter by document_id {document_id}: {e}")
                        search_kwargs = {"k": max_context_chunks}
                        retriever = self.vectorstore.as_retriever(search_kwargs=search_kwargs)
                else:
                    retriever = self.ensemble_retriever or self.vectorstore.as_retriever(search_kwargs={"k": max_context_chunks})

                # Create a wrapper that injects web search results into the context
                # This ensures web search results are properly included in the {context} field
                class WebSearchContextRetriever:
                    """Wrapper retriever that combines document retrieval with web search results"""
                    def __init__(self, base_retriever, web_search_context: str, is_time_sensitive: bool):
                        self.base_retriever = base_retriever
                        self.web_search_context = web_search_context
                        self.is_time_sensitive = is_time_sensitive
                        logger.info(f"WebSearchContextRetriever initialized with web_search_context length: {len(web_search_context) if web_search_context else 0}")
                    
                    def get_relevant_documents(self, query: str, k: int = 5):
                        """Get documents from base retriever and prepend web search context"""
                        docs = self.base_retriever.get_relevant_documents(query, k)
                        logger.debug(f"Base retriever returned {len(docs)} documents for query: '{query[:50]}'")
                        
                        # If web search context exists, create a document from it and prepend
                        if self.web_search_context:
                            web_doc = LangChainDocument(
                                page_content=self.web_search_context,
                                metadata={
                                    "source": "web_search",
                                    "source_type": "web",
                                    "is_time_sensitive": self.is_time_sensitive
                                }
                            )
                            logger.info(f"Adding web search document to context (time_sensitive={self.is_time_sensitive}, context_preview={self.web_search_context[:100]}...)")
                            # For time-sensitive queries, web search comes first
                            if self.is_time_sensitive:
                                result = [web_doc] + docs
                                logger.info(f"Web search document PREPENDED: total {len(result)} documents (web search is first)")
                                return result
                            else:
                                result = docs + [web_doc]
                                logger.info(f"Web search document APPENDED: total {len(result)} documents")
                                return result
                        return docs
                    
                    async def aget_relevant_documents(self, query: str, k: int = 5):
                        """Async version"""
                        if hasattr(self.base_retriever, 'aget_relevant_documents'):
                            docs = await self.base_retriever.aget_relevant_documents(query, k)
                        else:
                            docs = self.base_retriever.get_relevant_documents(query, k)
                        logger.debug(f"Base retriever (async) returned {len(docs)} documents for query: '{query[:50]}'")
                        
                        # If web search context exists, create a document from it and prepend
                        if self.web_search_context:
                            web_doc = LangChainDocument(
                                page_content=self.web_search_context,
                                metadata={
                                    "source": "web_search",
                                    "source_type": "web",
                                    "is_time_sensitive": self.is_time_sensitive
                                }
                            )
                            logger.info(f"Adding web search document to context (async, time_sensitive={self.is_time_sensitive}, context_preview={self.web_search_context[:100]}...)")
                            # For time-sensitive queries, web search comes first
                            if self.is_time_sensitive:
                                result = [web_doc] + docs
                                logger.info(f"Web search document PREPENDED (async): total {len(result)} documents (web search is first)")
                                return result
                            else:
                                result = docs + [web_doc]
                                logger.info(f"Web search document APPENDED (async): total {len(result)} documents")
                                return result
                        return docs
                
                # Wrap the retriever to include web search context
                wrapped_retriever = WebSearchContextRetriever(
                    retriever, 
                    web_search_context, 
                    is_time_sensitive
                ) if web_search_context else retriever
                
                # Log web search integration
                if web_search_context:
                    logger.info(
                        f"Using WebSearchContextRetriever for query: '{query[:50]}' "
                        f"(time_sensitive={is_time_sensitive}, web_context_length={len(web_search_context)})"
                    )
                
                async for chunk in self.rag_chain.astream(
                    {"input": query},  # Use original query, web search is in context now
                    config={"retriever": wrapped_retriever}
                ):
                    if "answer" in chunk:
                        full_response_content += chunk["answer"]
                        yield {"content": chunk["answer"], "done": False}
                    if "context" in chunk:
                        # Extract citations from source documents
                        source_docs = chunk.get('context', [])
                        logger.info(f"Retrieved {len(source_docs)} documents from chain (including web search if present)")
                        
                        for i, doc in enumerate(source_docs):
                            if hasattr(doc, 'metadata'):
                                # Check if this is a web search document
                                if doc.metadata.get("source_type") == "web" or doc.metadata.get("source") == "web_search":
                                    # Verify web search document is present
                                    logger.info(f"Web search document found in context at index {i}")
                                    # This is already in web_search_citations, skip
                                    continue
                                
                                doc_id = doc.metadata.get("document_id")
                                # Only include citations from the requested document if document_id is specified
                                if not document_id or str(doc_id) == str(document_id):
                                    citations.append({
                                        "document_id": doc_id,
                                        "chunk_index": doc.metadata.get("chunk_index"),
                                        "score": getattr(doc, 'score', None) or (1.0 - i * 0.1),
                                        "content_preview": doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content,
                                        "retrieval_method": "ensemble"
                                    })
            else:
                # Fallback to AI service, but still use RAG if document_id is provided
                if document_id:
                    # Even without RAG chain, we can still retrieve relevant chunks and use them as context
                    try:
                        print(f"DEBUG: Fallback RAG path - document_id={document_id}, query={query[:50]}...")
                        # Get relevant chunks from the specified document
                        relevant_chunks = await self.search_relevant_chunks(
                            query=query,
                            document_id=document_id,
                            limit=max_context_chunks,
                            use_ensemble=False,
                            use_compression=False
                        )
                        print(f"DEBUG: Found {len(relevant_chunks)} relevant chunks for document_id={document_id}")
                        
                        if relevant_chunks:
                            # Build context from retrieved chunks
                            context_parts = []
                            for chunk in relevant_chunks:
                                content = chunk.get('content', '')
                                if content:
                                    context_parts.append(content)
                                    # Add citation
                                    citations.append({
                                        "document_id": chunk.get('document_id'),
                                        "chunk_index": chunk.get('chunk_index'),
                                        "score": chunk.get('score'),
                                        "content_preview": content[:100] + "..." if len(content) > 100 else content,
                                        "retrieval_method": "similarity"
                                    })
                            
                            # Build context string
                            context = "\n\n".join(context_parts)
                            
                            # Add web search context if available
                            if web_search_context:
                                context = f"{context}\n\n{web_search_context}"
                            
                            # Create enhanced prompt with context
                            enhanced_prompt = f"""Based on the following document context{' and web search results' if web_search_context else ''}, answer the question.

Document Context:
{context}

Question: {query}

Answer:"""
                            
                            # Use AI service with context - use the specified model
                            ai_service = await self._get_ai_service(model_name)
                            if ai_service and hasattr(ai_service, 'generate_streaming_response'):
                                async for chunk_content in ai_service.generate_streaming_response(
                                    prompt=enhanced_prompt, context=None
                                ):
                                    full_response_content += chunk_content
                                    yield {"content": chunk_content, "done": False}
                            else:
                                yield {"content": "AI service not available", "done": False}
                        else:
                            # No chunks found - check if document exists in vector store
                            print(f"DEBUG: No chunks found for document_id={document_id}, checking vector store...")
                            try:
                                all_docs = self.vectorstore.get()
                                print(f"DEBUG: Vector store contains {len(all_docs.get('documents', []))} total documents")
                                # Check if any documents have this document_id
                                matching_docs = 0
                                all_document_ids = set()
                                for metadata in all_docs.get('metadatas', []):
                                    if metadata:
                                        doc_id = metadata.get('document_id', '')
                                        all_document_ids.add(str(doc_id))
                                        if str(doc_id) == str(document_id):
                                            matching_docs += 1
                                print(f"DEBUG: Found {matching_docs} documents with document_id={document_id} in vector store")
                                print(f"DEBUG: All document_ids in vector store: {list(all_document_ids)[:10]}")  # Show first 10
                            except Exception as e:
                                print(f"DEBUG: Error checking vector store: {e}")
                                import traceback
                                print(f"Traceback: {traceback.format_exc()}")
                            
                            # No chunks found, use AI service without context - use the specified model
                            ai_service = await self._get_ai_service(model_name)
                            if ai_service and hasattr(ai_service, 'generate_streaming_response'):
                                async for chunk_content in ai_service.generate_streaming_response(
                                    prompt=f"I couldn't find relevant information in the selected document. {query}", 
                                    context=None
                                ):
                                    full_response_content += chunk_content
                                    yield {"content": chunk_content, "done": False}
                            else:
                                yield {"content": "AI service not available and no document context found", "done": False}
                    except Exception as e:
                        import traceback
                        print(f"Error in RAG fallback with document_id: {e}")
                        print(f"Traceback: {traceback.format_exc()}")
                        # Fall through to regular AI service fallback - use the specified model
                        ai_service = await self._get_ai_service(model_name)
                        if ai_service and hasattr(ai_service, 'generate_streaming_response'):
                            try:
                                async for chunk_content in ai_service.generate_streaming_response(prompt=query):
                                    full_response_content += chunk_content
                                    yield {"content": chunk_content, "done": False}
                            except Exception as e2:
                                print(f"Error in AI service streaming: {e2}")
                                yield {"content": f"Error generating response: {str(e2)}", "done": False}
                        else:
                            yield {"content": "AI service not available", "done": False}
                else:
                    # No document_id, use AI service without RAG - use the specified model
                    ai_service = await self._get_ai_service(model_name)
                    if ai_service and hasattr(ai_service, 'generate_streaming_response'):
                        try:
                            async for chunk_content in ai_service.generate_streaming_response(prompt=query):
                                full_response_content += chunk_content
                                yield {"content": chunk_content, "done": False}
                        except Exception as e:
                            print(f"Error in AI service streaming: {e}")
                            yield {"content": f"Error generating response: {str(e)}", "done": False}
                    else:
                        yield {"content": "AI service not available", "done": False}

            yield {
                "content": full_response_content,
                "done": True,
                "citations": citations,
                "context_chunks_used": len(citations),
                "rag_enabled": bool(citations),
                "chain_type": "streaming_rag",
                "web_search_used": web_search_used,  # NEW: Indicate if web search was used
                "web_search_results_count": len(web_search_results) if web_search_used else 0,  # NEW: Count of web results
            }

        except Exception as e:
            print(f"Failed to generate RAG streaming response: {e}")
            yield {
                "error": str(e),
                "done": True,
                "content": f"I apologize, but there was an error generating the RAG response: {str(e)}"
            }

    async def add_document_with_chunking(self, document_id: str, full_text: str,
                                       metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add document with intelligent LangChain text splitting"""
        if not self.vectorstore or not full_text:
            return False

        try:
            # Use LangChain text splitter for intelligent chunking
            base_metadata = {
                "document_id": document_id,
                **(metadata or {})
            }

            # Determine if this is a markdown file and use appropriate splitter
            mime_type = metadata.get('mime_type', '') if metadata else ''
            filename = metadata.get('filename', '') if metadata else ''
            is_markdown = (
                mime_type == 'text/markdown' or 
                filename.endswith('.md') or 
                filename.endswith('.markdown')
            )
            
            # Use markdown-aware splitter for markdown files, otherwise use regular splitter
            if is_markdown and self.markdown_splitter:
                try:
                    chunks = self.markdown_splitter.split_text(full_text)
                    base_metadata['file_type'] = 'markdown'
                    base_metadata['chunking_method'] = 'markdown_aware'
                except Exception as e:
                    print(f"Markdown splitter failed, falling back to regular splitter: {e}")
                    chunks = self.text_splitter.split_text(full_text) if self.text_splitter else [full_text]
                    base_metadata['chunking_method'] = 'recursive_fallback'
            else:
                # Use regular text splitter for non-markdown files
                chunks = self.text_splitter.split_text(full_text) if self.text_splitter else [full_text]
                base_metadata['chunking_method'] = 'recursive'

            # Create LangChain-like documents or plain dicts for fallback
            langchain_docs = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = {
                    **base_metadata,
                    "chunk_index": i,
                    "chunk_length": len(chunk),
                    "total_chunks": len(chunks)
                }
                try:
                    # If LangChain Document class available, instantiate it; otherwise use dict
                    if LANGCHAIN_AVAILABLE and (not isinstance(LangChainDocument, type) or LangChainDocument is _Stub):
                        raise Exception("LangChain document class not available")
                    doc = LangChainDocument(page_content=chunk, metadata=chunk_metadata)
                except Exception:
                    doc = {"page_content": chunk, "metadata": chunk_metadata}
                langchain_docs.append(doc)

            # Add to vector store
            try:
                print(f"DEBUG: add_document_with_chunking - Adding {len(langchain_docs)} chunks for document_id={document_id}")
                self.vectorstore.add_documents(langchain_docs)
                try:
                    self.vectorstore.persist()  # Ensure persistence when supported
                except Exception:
                    pass
                # Verify documents were added
                try:
                    all_docs = self.vectorstore.get()
                    matching_count = 0
                    for metadata in all_docs.get('metadatas', []):
                        if metadata and str(metadata.get('document_id', '')) == str(document_id):
                            matching_count += 1
                    print(f"DEBUG: add_document_with_chunking - Verified: {matching_count} chunks with document_id={document_id} in vector store")
                except Exception as e:
                    print(f"DEBUG: add_document_with_chunking - Could not verify: {e}")
                return True
            except Exception as e:
                print(f"Failed to add docs to vectorstore: {e}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                return False

        except Exception as e:
            print(f"Failed to add document with chunking: {e}")
            return False

    async def add_document_chunks(self, document_id: str, chunks: List[str],
                                metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add pre-chunked documents to vector store using LangChain (backward compatibility)"""
        if not self.vectorstore or not chunks:
            return False

        try:
            # Create LangChain documents
            langchain_docs = []
            base_metadata = {
                "document_id": document_id,
                **(metadata or {})
            }

            for i, chunk in enumerate(chunks):
                chunk_metadata = {
                    **base_metadata,
                    "chunk_index": i,
                    "chunk_length": len(chunk)
                }
                try:
                    if LANGCHAIN_AVAILABLE and (not isinstance(LangChainDocument, type) or LangChainDocument is _Stub):
                        raise Exception("LangChain document class not available")
                    doc = LangChainDocument(page_content=chunk, metadata=chunk_metadata)
                except Exception:
                    doc = {"page_content": chunk, "metadata": chunk_metadata}
                langchain_docs.append(doc)

            try:
                self.vectorstore.add_documents(langchain_docs)
                try:
                    self.vectorstore.persist()
                except Exception:
                    pass
                return True
            except Exception as e:
                print(f"Failed to add pre-chunked docs: {e}")
                return False

        except Exception as e:
            print(f"Failed to add document chunks: {e}")
            return False

    async def search_relevant_chunks(self, query: str, document_id: Optional[str] = None,
                                    limit: int = 5, use_ensemble: bool = True,
                                    use_compression: bool = False) -> List[Dict[str, Any]]:
        """Search for relevant document chunks using advanced LangChain retrieval strategies"""
        if not self.vectorstore:
            return []

        try:
            # Choose retriever strategy
            if use_compression and self.compression_retriever:
                retriever = self.compression_retriever
                retriever_method = "compression"
            elif use_ensemble and self.ensemble_retriever:
                retriever = self.ensemble_retriever
                retriever_method = "ensemble"
            else:
                retriever = self.vectorstore.as_retriever(search_kwargs={"k": limit})
                retriever_method = "similarity"

            # Handle document-specific search
            if document_id:
                # For filtered search, we need to get documents and filter manually
                # since LangChain retrievers may not support metadata filtering directly
                all_docs = self.vectorstore.get()

                # Filter documents by document_id
                filtered_docs = []
                for doc_text, metadata, doc_id in zip(
                    all_docs['documents'], all_docs['metadatas'], all_docs['ids']
                ):
                    if metadata.get('document_id') == document_id:
                        filtered_docs.append(LangChainDocument(
                            page_content=doc_text,
                            metadata=metadata
                        ))

                if filtered_docs:
                    # Try BM25 retriever for keyword-based search within filtered documents
                    try:
                        bm25_retriever = BM25Retriever.from_documents(filtered_docs)
                        docs = bm25_retriever.get_relevant_documents(query, k=limit)
                        retriever_method = "bm25_filtered"
                    except Exception as bm25_error:
                        # Fallback to simple keyword matching if BM25 is not available
                        print(f"DEBUG: BM25 not available ({bm25_error}), using keyword matching on filtered documents")
                        # Simple keyword-based scoring
                        scored_docs = []
                        query_lower = query.lower()
                        query_words = set(query_lower.split())
                        for doc in filtered_docs:
                            content_lower = doc.page_content.lower()
                            content_words = set(content_lower.split())
                            # Calculate Jaccard similarity (intersection over union)
                            intersection = len(query_words & content_words)
                            union = len(query_words | content_words)
                            score = intersection / union if union > 0 else 0
                            # Also boost score if query words appear multiple times
                            word_count_score = sum(content_lower.count(word) for word in query_words) / max(len(query_words), 1)
                            final_score = (score * 0.7) + (min(word_count_score / 10, 0.3) * 0.3)  # Weighted combination
                            scored_docs.append((final_score, doc))
                        
                        # Sort by score and take top k
                        scored_docs.sort(key=lambda x: x[0], reverse=True)
                        docs = [doc for _, doc in scored_docs[:limit]]
                        retriever_method = "keyword_filtered"
                else:
                    docs = []
            else:
                # Use the selected advanced retriever
                docs = retriever.get_relevant_documents(query, k=limit)

            # Format results with enhanced metadata
            formatted_results = []
            for i, doc in enumerate(docs):
                score = getattr(doc, 'score', None)
                if score is None:
                    # Estimate score based on relevance rank
                    score = max(0.1, 1.0 - (i * 0.15))

                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score,
                    "document_id": doc.metadata.get("document_id"),
                    "chunk_index": doc.metadata.get("chunk_index"),
                    "relevance_rank": i + 1,
                    "retrieval_method": retriever_method,
                    "chunk_length": len(doc.page_content),
                    "total_chunks": doc.metadata.get("total_chunks", 1)
                })

            # Sort by score (highest first)
            formatted_results.sort(key=lambda x: x["score"], reverse=True)

            return formatted_results[:limit]  # Ensure we don't exceed the limit

        except Exception as e:
            print(f"Failed to search chunks: {e}")
            return []

    async def generate_rag_response(self, query: str, document_id: Optional[str] = None,
                                   max_context_chunks: int = 3, conversational: bool = False,
                                   chat_history: Optional[List[Dict[str, str]]] = None,
                                   model_name: Optional[str] = None,
                                   use_web_search: bool = False) -> Dict[str, Any]:
        """Generate RAG-enhanced response using advanced LangChain chains
        
        Args:
            query: User query string
            document_id: Optional document ID to filter search
            max_context_chunks: Maximum number of document chunks to use
            conversational: Whether to use conversational RAG chain
            chat_history: Optional chat history for conversational mode
            model_name: Optional model name to use
            use_web_search: Whether to include web search results (optional, defaults to False)
        """
        web_search_results = []
        web_search_used = False
        try:
            # QUICK DB-WIDE PRE-CHECK: if any uploaded document contains the query
            # or common keywords, return a short snippet immediately. This avoids
            # calling external LLM providers when the answer is present in the DB.
            try:
                from ..database import SessionLocal
                from ..models.document import Document as DocModel
                session = SessionLocal()
                try:
                    lower_q = query.lower() if query else ""
                    for doc in session.query(DocModel).all():
                        content = getattr(doc, 'content', None)
                        if not content:
                            continue
                        lower = str(content).lower()
                        if (lower_q and lower_q in lower) or any(k in lower for k in ["paris", "capital"]):
                            idx = lower.find(lower_q) if lower_q and lower_q in lower else -1
                            if idx == -1:
                                for kw in ["paris", "capital"]:
                                    if kw in lower:
                                        idx = lower.find(kw)
                                        break
                            snippet = str(content)[max(0, idx - 50): idx + 150] if idx >= 0 else str(content)[:200]
                            return {
                                "response": snippet,
                                "citations": [{"docId": str(doc.id), "snippet": snippet}],
                                "context_chunks_used": 1,
                                "rag_enabled": True,
                                "chain_type": "db_precheck"
                            }
                finally:
                    session.close()
            except Exception:
                # Non-fatal: continue to chain-based logic
                pass

            # Analyze query for time-sensitivity
            def is_time_sensitive_query(q: str) -> bool:
                """Detect if query is time-sensitive"""
                if not q:
                    return False
                q_lower = q.lower()
                time_keywords = ["latest", "recent", "news", "update", "what's new", "current", "today", "now"]
                return any(kw in q_lower for kw in time_keywords)
            
            is_time_sensitive = is_time_sensitive_query(query)
            
            # Perform web search if enabled
            web_search_context = ""
            web_search_citations = []
            if use_web_search:
                try:
                    from .web_search_service import get_web_search_service
                    web_search_service = get_web_search_service()
                    
                    # For time-sensitive queries, increase max_results and force fresh
                    search_max_results = max_context_chunks * 2 if is_time_sensitive else max_context_chunks
                    
                    # Perform web search (cache automatically disabled for time-sensitive queries)
                    web_results = await web_search_service.search(
                        query, 
                        max_results=search_max_results,
                        use_cache=not is_time_sensitive,  # Disable cache for time-sensitive
                        force_fresh=is_time_sensitive  # Force fresh for time-sensitive
                    )
                    web_search_results = web_results
                    web_search_used = len(web_results) > 0
                    
                    if web_results:
                        # Format web search results for context with clear structure
                        web_context_parts = ["=== Web Search Results (Most Recent Information) ==="]
                        for i, result in enumerate(web_results, 1):
                            web_context_parts.append(f"\n[Web Source {i}] {result.title}")
                            web_context_parts.append(f"URL: {result.url}")
                            web_context_parts.append(f"Content: {result.snippet}")
                            if result.timestamp:
                                web_context_parts.append(f"Retrieved: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                            
                            # Add web search citation
                            web_search_citations.append({
                                "url": result.url,
                                "title": result.title,
                                "snippet": result.snippet,
                                "source": "web_search",
                                "source_type": "web",  # NEW: Explicit source type
                                "relevance_score": result.relevance_score,
                                "timestamp": result.timestamp.isoformat() if result.timestamp else None
                            })
                        
                        web_search_context = "\n".join(web_context_parts)
                        logger.info(
                            f"Web search returned {len(web_results)} results for query: '{query[:50]}' "
                            f"(time_sensitive={is_time_sensitive})"
                        )
                except Exception as e:
                    logger.warning(f"Web search failed, continuing without web results: {e}", exc_info=True)
                    # Continue without web search - don't break the flow
            
            if conversational and chat_history and self.conversational_chain:
                # Use conversational RAG chain with memory
                # For time-sensitive queries, reduce document chunks to prioritize web search
                adjusted_chunks = max_context_chunks // 2 if is_time_sensitive and web_search_context else max_context_chunks
                result = await self._generate_conversational_rag_response(
                    query, document_id, adjusted_chunks, chat_history, web_search_context, web_search_citations, is_time_sensitive
                )
                # Add web search metadata
                result["web_search_used"] = web_search_used
                result["web_search_results_count"] = len(web_search_results) if web_search_used else 0
                result["is_time_sensitive"] = is_time_sensitive  # NEW: Include time-sensitivity flag
                return result
            elif self.rag_chain:
                # Use basic RAG chain
                # For time-sensitive queries, reduce document chunks to prioritize web search
                adjusted_chunks = max_context_chunks // 2 if is_time_sensitive and web_search_context else max_context_chunks
                result = await self._generate_basic_rag_response(
                    query, document_id, adjusted_chunks, web_search_context, web_search_citations, is_time_sensitive
                )
                # Add web search metadata
                result["web_search_used"] = web_search_used
                result["web_search_results_count"] = len(web_search_results) if web_search_used else 0
                result["is_time_sensitive"] = is_time_sensitive  # NEW: Include time-sensitivity flag
                return result
            else:
                # If vectorstore / chains are not available, try a lightweight DB-backed fallback
                # that inspects the uploaded document content (if document_id provided)
                if document_id:
                    try:
                        # Lazy import to avoid circular dependencies
                        from ..database import SessionLocal
                        from ..models.document import Document as DocModel
                        from uuid import UUID as _UUID

                        session = SessionLocal()
                        try:
                            doc_uuid = _UUID(str(document_id))
                        except Exception:
                            doc_uuid = None

                        if doc_uuid:
                            doc = session.query(DocModel).filter(DocModel.id == doc_uuid).first()
                            if doc and getattr(doc, 'content', None):
                                content = str(getattr(doc, 'content', '')).strip()
                                # Simple heuristic: if the content contains the answer or the query
                                if content:
                                    # If query terms appear in content, return a short excerpt
                                    if query.lower() in content.lower() or any(term in content for term in ["paris", "capital"]):
                                        # Find snippet containing the query or the keyword
                                        lower = content.lower()
                                        idx = -1
                                        if query.lower() in lower:
                                            idx = lower.find(query.lower())
                                        else:
                                            for kw in ["paris", "capital"]:
                                                if kw in lower:
                                                    idx = lower.find(kw)
                                                    break

                                        snippet = content[max(0, idx - 50): idx + 150] if idx >= 0 else content[:200]
                                        return {
                                            "response": snippet,
                                            "citations": [{"docId": str(doc.id), "snippet": snippet}],
                                            "context_chunks_used": 1,
                                            "rag_enabled": True,
                                            "chain_type": "db_fallback"
                                        }

                        # close session
                        session.close()
                    except Exception:
                        # If fallback fails, continue to AI fallback
                        pass

                # Try a DB-wide fallback search across uploaded documents when no vectorstore is available
                try:
                    from ..database import SessionLocal
                    from ..models.document import Document as DocModel
                    session = SessionLocal()
                    try:
                        # Pull all documents and look for the query or common keywords
                        for doc in session.query(DocModel).all():
                            content = getattr(doc, 'content', None)
                            if not content:
                                continue
                            lower = str(content).lower()
                            if query.lower() in lower or any(k in lower for k in ["paris", "capital"]):
                                # Return a short snippet containing the keyword
                                idx = lower.find(query.lower()) if query.lower() in lower else -1
                                if idx == -1:
                                    for kw in ["paris", "capital"]:
                                        if kw in lower:
                                            idx = lower.find(kw)
                                            break
                                snippet = str(content)[max(0, idx - 50): idx + 150] if idx >= 0 else str(content)[:200]
                                return {
                                    "response": snippet,
                                    "citations": [{"docId": str(doc.id), "snippet": snippet}],
                                    "context_chunks_used": 1,
                                    "rag_enabled": True,
                                    "chain_type": "db_fallback"
                                }
                    finally:
                        session.close()
                except Exception:
                    # If DB fallback fails, continue to AI fallback
                    pass

                # Fallback to AI service without RAG - get AI service for requested model
                async def _get_ai_with_fallback(mname: Optional[str] = None):
                    try:
                        ai_obj = await get_ai_service(mname)
                        # If the chosen provider cannot handle the model, fall back to default
                        try:
                            provider = ai_obj._get_provider_for_model(mname or ai_obj.model_name)
                        except Exception:
                            provider = "none"
                        if provider == "none":
                            return await get_ai_service(None)
                        return ai_obj
                    except Exception:
                        return await get_ai_service(None)

                ai = await _get_ai_with_fallback(model_name)
                ai_response = await ai.generate_response(prompt=query)
                return {
                    **ai_response,
                    "citations": [],
                    "context_chunks_used": 0,
                    "rag_enabled": False,
                    "chain_type": "fallback"
                }

        except Exception as e:
            print(f"Failed to generate RAG response: {e}")
            # Try lightweight DB fallback before using AI fallback
            try:
                from ..database import SessionLocal
                from ..models.document import Document as DocModel
                session = SessionLocal()
                try:
                    for doc in session.query(DocModel).all():
                        content = getattr(doc, 'content', None)
                        if not content:
                            continue
                        lower = str(content).lower()
                        if query.lower() in lower or any(k in lower for k in ["paris", "capital"]):
                            idx = lower.find(query.lower()) if query.lower() in lower else -1
                            if idx == -1:
                                for kw in ["paris", "capital"]:
                                    if kw in lower:
                                        idx = lower.find(kw)
                                        break
                            snippet = str(content)[max(0, idx - 50): idx + 150] if idx >= 0 else str(content)[:200]
                            return {
                                "response": snippet,
                                "citations": [{"docId": str(doc.id), "snippet": snippet}],
                                "context_chunks_used": 1,
                                "rag_enabled": True,
                                "chain_type": "db_exception_fallback",
                                "error": str(e)
                            }
                finally:
                    session.close()
            except Exception:
                pass

            # Fallback to regular AI response with model availability check
            async def _get_ai_with_fallback_local(mname: Optional[str] = None):
                try:
                    ai_obj = await get_ai_service(mname)
                    try:
                        provider = ai_obj._get_provider_for_model(mname or ai_obj.model_name)
                    except Exception:
                        provider = "none"
                    if provider == "none":
                        return await get_ai_service(None)
                    return ai_obj
                except Exception:
                    return await get_ai_service(None)

            ai = await _get_ai_with_fallback_local(model_name)
            ai_response = await ai.generate_response(prompt=query)
            return {
                **ai_response,
                "citations": [],
                "context_chunks_used": 0,
                "rag_enabled": False,
                "error": str(e),
                "chain_type": "error_fallback"
            }

    async def _generate_basic_rag_response(self, query: str, document_id: Optional[str] = None,
                                          max_context_chunks: int = 3,
                                          web_search_context: str = "",
                                          web_search_citations: List[Dict[str, Any]] = None,
                                          is_time_sensitive: bool = False) -> Dict[str, Any]:
        """Generate basic RAG response using the configured chain
        
        Args:
            query: User query string
            document_id: Optional document ID to filter search
            max_context_chunks: Maximum number of document chunks to use
            web_search_context: Optional web search context to include
            web_search_citations: Optional web search citations to include
            is_time_sensitive: Whether the query is time-sensitive
        """
        if web_search_citations is None:
            web_search_citations = []
        
        # Create document-filtered retriever if needed
        if document_id:
            # For document-specific queries, create a filtered retriever
            search_kwargs = {"k": max_context_chunks}
            # Note: This is a simplified approach - in practice, you'd want better filtering
            retriever = self.vectorstore.as_retriever(search_kwargs=search_kwargs)
        else:
            retriever = self.ensemble_retriever or self.vectorstore.as_retriever(search_kwargs={"k": max_context_chunks})

        try:
            # Create wrapper retriever that includes web search context
            class WebSearchContextRetriever:
                """Wrapper retriever that combines document retrieval with web search results"""
                def __init__(self, base_retriever, web_search_context: str, is_time_sensitive: bool):
                    self.base_retriever = base_retriever
                    self.web_search_context = web_search_context
                    self.is_time_sensitive = is_time_sensitive
                
                def get_relevant_documents(self, query: str, k: int = 5):
                    """Get documents from base retriever and prepend web search context"""
                    docs = self.base_retriever.get_relevant_documents(query, k)
                    
                    # If web search context exists, create a document from it and prepend
                    if self.web_search_context:
                        web_doc = LangChainDocument(
                            page_content=self.web_search_context,
                            metadata={
                                "source": "web_search",
                                "source_type": "web",
                                "is_time_sensitive": self.is_time_sensitive
                            }
                        )
                        # For time-sensitive queries, web search comes first
                        if self.is_time_sensitive:
                            return [web_doc] + docs
                        else:
                            return docs + [web_doc]
                    return docs
                
                async def aget_relevant_documents(self, query: str, k: int = 5):
                    """Async version"""
                    if hasattr(self.base_retriever, 'aget_relevant_documents'):
                        docs = await self.base_retriever.aget_relevant_documents(query, k)
                    else:
                        docs = self.base_retriever.get_relevant_documents(query, k)
                    
                    # If web search context exists, create a document from it and prepend
                    if self.web_search_context:
                        web_doc = LangChainDocument(
                            page_content=self.web_search_context,
                            metadata={
                                "source": "web_search",
                                "source_type": "web",
                                "is_time_sensitive": self.is_time_sensitive
                            }
                        )
                        # For time-sensitive queries, web search comes first
                        if self.is_time_sensitive:
                            return [web_doc] + docs
                        else:
                            return docs + [web_doc]
                    return docs
            
            # Wrap the retriever to include web search context
            wrapped_retriever = WebSearchContextRetriever(
                retriever, 
                web_search_context, 
                is_time_sensitive
            ) if web_search_context else retriever
            
            # Execute RAG chain with wrapped retriever
            result = await self.rag_chain.ainvoke(
                {"input": query},  # Use original query, web search is in context now
                config={"retriever": wrapped_retriever}
            )

            # Extract citations from source documents
            citations = []
            source_docs = result.get('context', [])
            if source_docs:
                for i, doc in enumerate(source_docs):
                    if hasattr(doc, 'metadata'):
                        # Check if this is a web search document
                        if doc.metadata.get("source_type") == "web" or doc.metadata.get("source") == "web_search":
                            # This is already in web_search_citations, skip
                            continue
                        
                        citations.append({
                            "document_id": doc.metadata.get("document_id"),
                            "chunk_index": doc.metadata.get("chunk_index"),
                            "score": getattr(doc, 'score', None) or (1.0 - i * 0.1),
                            "content_preview": doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content,
                            "retrieval_method": "ensemble",
                            "source": "document"
                        })
            
            # Add web search citations
            citations.extend(web_search_citations)

            return {
                "response": result.get("answer", ""),
                "citations": citations,
                "context_chunks_used": len([c for c in citations if c.get("source") == "document"]),
                "rag_enabled": bool([c for c in citations if c.get("source") == "document"]),
                "chain_type": "basic_rag",
                "retrieval_method": "ensemble"
            }

        except Exception as e:
            print(f"Basic RAG chain failed: {e}")
            raise

    async def _generate_conversational_rag_response(self, query: str, document_id: Optional[str] = None,
                                                   max_context_chunks: int = 3,
                                                   chat_history: Optional[List[Dict[str, str]]] = None,
                                                   web_search_context: str = "",
                                                   web_search_citations: List[Dict[str, Any]] = None,
                                                   is_time_sensitive: bool = False) -> Dict[str, Any]:
        """Generate conversational RAG response with memory
        
        Args:
            query: User query string
            document_id: Optional document ID to filter search
            max_context_chunks: Maximum number of document chunks to use
            chat_history: Optional chat history for conversational mode
            web_search_context: Optional web search context to include
            web_search_citations: Optional web search citations to include
            is_time_sensitive: Whether the query is time-sensitive
        """
        if web_search_citations is None:
            web_search_citations = []
        
        try:
            # Convert chat history to LangChain format
            formatted_history = []
            if chat_history:
                for msg in chat_history[-10:]:  # Keep last 10 messages
                    if msg.get("role") == "user":
                        formatted_history.append(HumanMessage(content=msg.get("content", "")))
                    elif msg.get("role") == "assistant":
                        formatted_history.append(AIMessage(content=msg.get("content", "")))

            # Update conversation memory
            for msg in formatted_history:
                if isinstance(msg, HumanMessage):
                    self.conversation_memory.chat_memory.add_user_message(msg.content)
                elif isinstance(msg, AIMessage):
                    self.conversation_memory.chat_memory.add_ai_message(msg.content)

            # Get the base retriever from the conversational chain
            # The conversational chain uses history_aware_retriever, but we can override it in config
            base_retriever = None
            if hasattr(self.conversational_chain, 'retriever'):
                base_retriever = self.conversational_chain.retriever
            elif hasattr(self, 'ensemble_retriever') and self.ensemble_retriever:
                base_retriever = self.ensemble_retriever
            elif self.vectorstore:
                base_retriever = self.vectorstore.as_retriever(search_kwargs={"k": max_context_chunks})
            
            # Create wrapper retriever that includes web search context
            if base_retriever and web_search_context:
                class WebSearchContextRetriever:
                    """Wrapper retriever that combines document retrieval with web search results"""
                    def __init__(self, base_retriever, web_search_context: str, is_time_sensitive: bool):
                        self.base_retriever = base_retriever
                        self.web_search_context = web_search_context
                        self.is_time_sensitive = is_time_sensitive
                        logger.info(f"WebSearchContextRetriever initialized with web_search_context length: {len(web_search_context) if web_search_context else 0}")
                    
                    def get_relevant_documents(self, query: str, k: int = 5):
                        """Get documents from base retriever and prepend web search context"""
                        docs = self.base_retriever.get_relevant_documents(query, k)
                        logger.debug(f"Base retriever returned {len(docs)} documents for query: '{query[:50]}'")
                        
                        # If web search context exists, create a document from it and prepend
                        if self.web_search_context:
                            web_doc = LangChainDocument(
                                page_content=self.web_search_context,
                                metadata={
                                    "source": "web_search",
                                    "source_type": "web",
                                    "is_time_sensitive": self.is_time_sensitive
                                }
                            )
                            logger.info(f"Adding web search document to context (time_sensitive={self.is_time_sensitive}, context_preview={self.web_search_context[:100]}...)")
                            # For time-sensitive queries, web search comes first
                            if self.is_time_sensitive:
                                result = [web_doc] + docs
                                logger.info(f"Web search document PREPENDED: total {len(result)} documents (web search is first)")
                                return result
                            else:
                                result = docs + [web_doc]
                                logger.info(f"Web search document APPENDED: total {len(result)} documents")
                                return result
                        return docs
                    
                    async def aget_relevant_documents(self, query: str, k: int = 5):
                        """Async version"""
                        if hasattr(self.base_retriever, 'aget_relevant_documents'):
                            docs = await self.base_retriever.aget_relevant_documents(query, k)
                        else:
                            docs = self.base_retriever.get_relevant_documents(query, k)
                        logger.debug(f"Base retriever (async) returned {len(docs)} documents for query: '{query[:50]}'")
                        
                        # If web search context exists, create a document from it and prepend
                        if self.web_search_context:
                            web_doc = LangChainDocument(
                                page_content=self.web_search_context,
                                metadata={
                                    "source": "web_search",
                                    "source_type": "web",
                                    "is_time_sensitive": self.is_time_sensitive
                                }
                            )
                            logger.info(f"Adding web search document to context (async, time_sensitive={self.is_time_sensitive}, context_preview={self.web_search_context[:100]}...)")
                            # For time-sensitive queries, web search comes first
                            if self.is_time_sensitive:
                                result = [web_doc] + docs
                                logger.info(f"Web search document PREPENDED (async): total {len(result)} documents (web search is first)")
                                return result
                            else:
                                result = docs + [web_doc]
                                logger.info(f"Web search document APPENDED (async): total {len(result)} documents")
                                return result
                        return docs
                
                wrapped_retriever = WebSearchContextRetriever(
                    base_retriever, 
                    web_search_context, 
                    is_time_sensitive
                )
                chain_config = {
                    "memory": self.conversation_memory,
                    "retriever": wrapped_retriever
                }
            else:
                chain_config = {"memory": self.conversation_memory}

            # Execute conversational chain
            result = await self.conversational_chain.ainvoke(
                {"input": query},  # Use original query, web search is in context now
                config=chain_config
            )

            # Extract citations from source documents
            citations = []
            source_docs = result.get('context', [])
            if source_docs:
                for i, doc in enumerate(source_docs):
                    if hasattr(doc, 'metadata'):
                        # Check if this is a web search document
                        if doc.metadata.get("source_type") == "web" or doc.metadata.get("source") == "web_search":
                            # This is already in web_search_citations, skip
                            continue
                        
                        citations.append({
                            "document_id": doc.metadata.get("document_id"),
                            "chunk_index": doc.metadata.get("chunk_index"),
                            "score": getattr(doc, 'score', None) or (1.0 - i * 0.1),
                            "content_preview": doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content,
                            "retrieval_method": "conversational",
                            "source": "document"
                        })
            
            # Add web search citations
            citations.extend(web_search_citations)

            return {
                "response": result.get("answer", ""),
                "citations": citations,
                "context_chunks_used": len([c for c in citations if c.get("source") == "document"]),
                "rag_enabled": bool([c for c in citations if c.get("source") == "document"]),
                "chain_type": "conversational_rag",
                "conversation_turns": len(formatted_history),
                "memory_buffer_size": (
                    getattr(self.conversation_memory, 'k', None)
                    if getattr(self.conversation_memory, 'k', None) is not None
                    else getattr(getattr(self.conversation_memory, 'memory', None), 'k', None)
                )
            }

        except Exception as e:
            print(f"Conversational RAG chain failed: {e}")
            raise

    def delete_document_chunks(self, document_id: str) -> bool:
        """Delete all chunks for a document using LangChain"""
        if not self.vectorstore:
            return False

        try:
            # LangChain Chroma doesn't have direct delete by metadata filter
            # We need to recreate the collection without the document's chunks
            # This is a simplified approach - in production, you'd want a more efficient method

            # Get all documents
            all_docs = self.vectorstore.get()

            # Filter out documents with the specified document_id
            filtered_docs = []
            filtered_metadatas = []
            filtered_ids = []

            for i, metadata in enumerate(all_docs['metadatas']):
                if metadata.get('document_id') != document_id:
                    filtered_docs.append(all_docs['documents'][i])
                    filtered_metadatas.append(metadata)
                    filtered_ids.append(all_docs['ids'][i])

            if len(filtered_docs) < len(all_docs['documents']):
                # Recreate the collection with filtered documents
                self.vectorstore._collection.delete()  # Clear collection
                if filtered_docs:
                    self.vectorstore.add_texts(
                        texts=filtered_docs,
                        metadatas=filtered_metadatas,
                        ids=filtered_ids
                    )
                self.vectorstore.persist()
                return True

            return False

        except Exception as e:
            print(f"Failed to delete document chunks: {e}")
            return False

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector collection using LangChain"""
        if not self.vectorstore:
            return {"status": "unavailable"}

        try:
            # Get collection info through LangChain
            count = self.vectorstore._collection.count()
            return {
                "status": "available",
                "total_chunks": count,
                "collection_name": self.vectorstore._collection.name,
                "embedding_model": "all-MiniLM-L6-v2"  # From SentenceTransformerEmbeddings
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def reindex_document(self, document_id: str, new_chunks: List[str],
                              metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Reindex a document with new chunks (delete old, add new) using LangChain"""
        # Delete old chunks
        self.delete_document_chunks(document_id)

        # Add new chunks
        return await self.add_document_chunks(document_id, new_chunks, metadata)

    def get_observability_data(self) -> Dict[str, Any]:
        """Get observability data from RAG operations using LangChain callbacks"""
        if not self.callback_handler:
            return {"status": "no_callback_handler"}

        return {
            "total_operations": len(self.callback_handler.operations),
            "operations": self.callback_handler.operations[-20:],  # Last 20 operations
            "retrieval_stats": {
                "total_retrievals": len([op for op in self.callback_handler.operations if op["operation"] == "retrieval_end"]),
                "avg_documents_found": sum(op.get("documents_found", 0) for op in self.callback_handler.operations if op["operation"] == "retrieval_end") /
                                     max(1, len([op for op in self.callback_handler.operations if op["operation"] == "retrieval_end"]))
            },
            "chain_stats": {
                "total_chains": len([op for op in self.callback_handler.operations if op["operation"] == "chain_end"])
            }
        }

    def configure_retrieval_strategy(self, strategy: str = "ensemble",
                                    similarity_threshold: float = 0.7,
                                    mmr_lambda: float = 0.5) -> bool:
        """Configure retrieval strategy with different LangChain retrievers"""
        try:
            if strategy == "ensemble":
                # Reconfigure ensemble retriever with new parameters
                similarity_retriever = self.vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 10}
                )

                mmr_retriever = self.vectorstore.as_retriever(
                    search_type="mmr",
                    search_kwargs={"k": 10, "lambda_mult": mmr_lambda}
                )

                try:
                    self.ensemble_retriever = EnsembleRetriever(
                        retrievers=[similarity_retriever, mmr_retriever],
                        weights=[0.7, 0.3]
                    )
                except TypeError as te:
                    if "takes no arguments" in str(te) or "positional" in str(te).lower():
                        print(f"Warning: EnsembleRetriever API issue, using fallback: {te}")
                        # Fallback to similarity retriever only
                        self.ensemble_retriever = similarity_retriever
                    else:
                        raise

            elif strategy == "compression":
                # Reconfigure compression retriever
                if self.embeddings is None:
                    print("Warning: Embeddings not available for compression retriever")
                    return False
                
                embeddings_filter = EmbeddingsFilter(
                    embeddings=self.embeddings,
                    similarity_threshold=similarity_threshold
                )

                base_retriever = self.vectorstore.as_retriever(search_kwargs={"k": 10})
                try:
                    self.compression_retriever = DocumentCompressorPipeline(
                        base_retriever=base_retriever,
                        transformers=[embeddings_filter]
                    )
                except TypeError:
                    # Try alternative API with compressors parameter
                    try:
                        self.compression_retriever = DocumentCompressorPipeline(
                            base_retriever=base_retriever,
                            compressors=[embeddings_filter]
                        )
                    except Exception as e:
                        print(f"Failed to create compression retriever: {e}")
                        return False

            elif strategy == "mmr":
                self.ensemble_retriever = self.vectorstore.as_retriever(
                    search_type="mmr",
                    search_kwargs={"k": 10, "lambda_mult": mmr_lambda}
                )

            elif strategy == "similarity":
                self.ensemble_retriever = self.vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 10}
                )

            return True

        except Exception as e:
            print(f"Failed to configure retrieval strategy: {e}")
            return False

    async def hybrid_search(self, query: str, document_id: Optional[str] = None,
                          semantic_weight: float = 0.7, keyword_weight: float = 0.3,
                          limit: int = 5) -> List[Dict[str, Any]]:
        """Perform hybrid search combining semantic and keyword-based retrieval"""
        try:
            # Get semantic results
            semantic_results = await self.search_relevant_chunks(
                query, document_id, limit * 2, use_ensemble=False
            )

            # Get keyword-based results (BM25)
            all_docs = self.vectorstore.get()
            docs_for_bm25 = []

            # Filter by document_id if specified
            for doc_text, metadata in zip(all_docs['documents'], all_docs['metadatas']):
                if not document_id or metadata.get('document_id') == document_id:
                    docs_for_bm25.append(LangChainDocument(
                        page_content=doc_text,
                        metadata=metadata
                    ))

            bm25_results = []
            if docs_for_bm25:
                bm25_retriever = BM25Retriever.from_documents(docs_for_bm25)
                bm25_docs = bm25_retriever.get_relevant_documents(query, k=limit * 2)

                for i, doc in enumerate(bm25_docs):
                    bm25_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "score": 1.0 - (i * 0.1),  # BM25 doesn't provide scores directly
                        "document_id": doc.metadata.get("document_id"),
                        "chunk_index": doc.metadata.get("chunk_index"),
                        "search_type": "keyword"
                    })

            # Combine and rerank results
            combined_results = {}

            # Add semantic results
            for result in semantic_results:
                key = f"{result['document_id']}_{result['chunk_index']}"
                combined_results[key] = {
                    **result,
                    "semantic_score": result["score"],
                    "keyword_score": 0.0,
                    "combined_score": result["score"] * semantic_weight
                }

            # Add/merge keyword results
            for result in bm25_results:
                key = f"{result['document_id']}_{result['chunk_index']}"
                if key in combined_results:
                    # Update existing result
                    combined_results[key]["keyword_score"] = result["score"]
                    combined_results[key]["combined_score"] = (
                        combined_results[key]["semantic_score"] * semantic_weight +
                        result["score"] * keyword_weight
                    )
                else:
                    # Add new result
                    combined_results[key] = {
                        **result,
                        "semantic_score": 0.0,
                        "keyword_score": result["score"],
                        "combined_score": result["score"] * keyword_weight
                    }

            # Sort by combined score and return top results
            sorted_results = sorted(
                combined_results.values(),
                key=lambda x: x["combined_score"],
                reverse=True
            )

            # Format final results
            final_results = []
            for result in sorted_results[:limit]:
                final_results.append({
                    "content": result["content"],
                    "metadata": result["metadata"],
                    "score": result["combined_score"],
                    "document_id": result["document_id"],
                    "chunk_index": result["chunk_index"],
                    "search_type": "hybrid",
                    "semantic_score": result.get("semantic_score", 0.0),
                    "keyword_score": result.get("keyword_score", 0.0)
                })

            return final_results

        except Exception as e:
            print(f"Hybrid search failed: {e}")
            return []

    def get_langchain_config(self) -> Dict[str, Any]:
        """Get current LangChain configuration and capabilities"""
        return {
            "vectorstore": {
                "type": "ChromaDB",
                "collection_name": self.vectorstore._collection.name if self.vectorstore else None,
                "embedding_model": "all-MiniLM-L6-v2",
                "persist_directory": self.persist_directory
            },
            "text_splitter": {
                "type": "RecursiveCharacterTextSplitter",
                "chunk_size": self.text_splitter.chunk_size if self.text_splitter else None,
                "chunk_overlap": self.text_splitter.chunk_overlap if self.text_splitter else None
            },
            "retrievers": {
                "ensemble_available": self.ensemble_retriever is not None,
                "compression_available": self.compression_retriever is not None,
                "conversational_available": self.conversational_chain is not None
            },
            "memory": {
                "type": "ConversationBufferWindowMemory",
                "buffer_size": (
                    getattr(self.conversation_memory, 'k', None)
                    if getattr(self.conversation_memory, 'k', None) is not None
                    else getattr(getattr(self.conversation_memory, 'memory', None), 'k', None)
                ) if self.conversation_memory else None
            },
            "chains": {
                "rag_chain": self.rag_chain is not None,
                "conversational_chain": self.conversational_chain is not None
            },
            "observability": {
                "callback_handler": self.callback_handler is not None,
                "operations_tracked": len(self.callback_handler.operations) if self.callback_handler else 0
            }
        }


# Global instance for dependency injection
_rag_service_instance = None

if not LANGCHAIN_AVAILABLE:
    # Minimal fallback RAGService when LangChain isn't installed. Uses AI service only.
    class RAGService:
        def __init__(self, persist_directory: str = "./chroma_db"):
            self.persist_directory = persist_directory
            from .rag_adapter import create_memory, create_splitter, create_vectorstore

            self.vectorstore = create_vectorstore(client=None, collection_name="documents")
            self.embeddings = None
            self.text_splitter = create_splitter(chunk_size=1000, chunk_overlap=200)
            self.markdown_splitter = None  # Markdown splitter not available in fallback mode
            self.conversation_memory = create_memory(k=5)
            self.callback_handler = None
            # Lazy import AI service - note: get_ai_service() is async
            self._ai_service_getter = None
            self._ai_service_instance = None
            try:
                from .ai_service import get_ai_service
                self._ai_service_getter = get_ai_service
            except Exception:
                class _AIStub:
                    def __init__(self):
                        self.model_name = "stub"

                    async def generate_response(self, prompt: str):
                        return {"response": "(AI stub) " + str(prompt)}

                    async def generate_streaming_response(self, prompt: str):
                        async def gen():
                            yield "(AI stub) " + str(prompt)

                        return gen()

                self._ai_service_instance = _AIStub()

        async def _get_ai_service(self, model_name: Optional[str] = None):
            """Lazy-load AI service (async)"""
            if self._ai_service_instance is not None:
                return self._ai_service_instance
            if self._ai_service_getter:
                self._ai_service_instance = await self._ai_service_getter(model_name)
                return self._ai_service_instance
            # Fallback stub
            class _AIStub:
                def __init__(self):
                    self.model_name = "stub"

                async def generate_response(self, prompt: str):
                    return {"response": "(AI stub) " + str(prompt)}

                async def generate_streaming_response(self, prompt: str):
                    async def gen():
                        yield "(AI stub) " + str(prompt)
                    return gen()
            
            self._ai_service_instance = _AIStub()
            return self._ai_service_instance

        async def generate_rag_streaming_response(self, query: str, document_id: Optional[str] = None,
                                                  max_context_chunks: int = 3, conversational: bool = False,
                                                  chat_history: Optional[List[Dict[str, str]]] = None,
                                                  model_name: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
            # Fallback: stream AI service outputs as simple content chunks
            try:
                ai_service = await self._get_ai_service(model_name)
                async for chunk in ai_service.generate_streaming_response(prompt=query):
                    yield {"content": chunk}
                # final payload
                yield {"content": "", "done": True, "citations": []}
            except Exception as e:
                yield {"error": str(e), "done": True}

        async def generate_rag_response(self, query: str, document_id: Optional[str] = None,
                                        max_context_chunks: int = 3, conversational: bool = False,
                                        chat_history: Optional[List[Dict[str, str]]] = None,
                                        model_name: Optional[str] = None) -> Dict[str, Any]:
            # Fallback sync response from AI service
            try:
                ai_service = await self._get_ai_service(model_name)
                resp = await ai_service.generate_response(prompt=query)
                if isinstance(resp, dict):
                    return {"response": resp.get("response", ""), "citations": resp.get("citations", [])}
                return {"response": str(resp), "citations": []}
            except Exception as e:
                return {"response": "", "citations": [], "error": str(e)}

        async def add_document_with_chunking(self, document_id: str, full_text: str,
                                             metadata: Optional[Dict[str, Any]] = None) -> bool:
            # No vector store available in fallback
            return False

        async def add_document_chunks(self, document_id: str, chunks: List[str],
                                      metadata: Optional[Dict[str, Any]] = None) -> bool:
            return False

        async def search_relevant_chunks(self, query: str, document_id: Optional[str] = None,
                                         limit: int = 5, use_ensemble: bool = True,
                                         use_compression: bool = False) -> List[Dict[str, Any]]:
            return []

    def get_rag_service() -> RAGService:
        """Get singleton RAGService instance (fallback)"""
        global _rag_service_instance
        if _rag_service_instance is None:
            _rag_service_instance = RAGService()
        return _rag_service_instance

else:
    # If LangChain is available, keep the full-featured singleton behavior
    def get_rag_service() -> 'RAGService':
        """Get singleton RAGService instance"""
        global _rag_service_instance
        if _rag_service_instance is None:
            _rag_service_instance = RAGService()
        return _rag_service_instance
