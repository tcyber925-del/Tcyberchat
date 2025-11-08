PS C:\Users\Tcyber\Documents\PROJECTS\TcyberChatbot\backend> uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
INFO:     Will watch for changes in these directories: ['C:\\Users\\Tcyber\\Documents\\PROJECTS\\TcyberChatbot\\backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [9584] using WatchFiles
Initializing databases...
SQLAlchemy tables created successfully
Running lightweight SQLite migrations...
ChromaDB initialized successfully
All databases initialized successfully!
INFO:     Started server process [20420]
INFO:     Waiting for application startup.
2025-11-08 13:38:16,951 - main - INFO - Application starting up...
INFO:     Application startup complete.
2025-11-08 13:45:27,451 - main - INFO - Request: GET /documents from 127.0.0.1
2025-11-08 13:45:27,468 - main - INFO - Response: GET /documents -> 307 (0.017s)
INFO:     127.0.0.1:22249 - "GET /documents HTTP/1.1" 307 Temporary Redirect
2025-11-08 13:45:27,468 - main - INFO - Request: GET /v1/models from 127.0.0.1
2025-11-08 13:45:27,556 - main - INFO - Response: GET /v1/models -> 404 (0.088s)
INFO:     127.0.0.1:22250 - "GET /v1/models HTTP/1.1" 404 Not Found
2025-11-08 13:45:27,814 - main - INFO - Request: GET /documents/ from 127.0.0.1
2025-11-08 13:45:27,842 - src.api.documents - INFO - Fetching all documents
2025-11-08 13:45:28,410 - src.api.documents - INFO - Found 1 documents
2025-11-08 13:45:28,679 - main - INFO - Response: GET /documents/ -> 200 (0.865s)
INFO:     127.0.0.1:22249 - "GET /documents/ HTTP/1.1" 200 OK
2025-11-08 14:02:55,174 - main - INFO - Request: GET /api/v1/models from 127.0.0.1
2025-11-08 14:02:55,185 - src.services.ai_service - INFO - Google Gemini client initialized with model: models/gemini-2.5-flash
2025-11-08 14:03:00,101 - src.services.ai_service - INFO - OpenRouter client initialized with model: openai/gpt-oss-20b:free
2025-11-08 14:03:01,249 - backend.src.clients.llama_cpp_client - INFO - Llama.cpp client initialized for server at http://localhost:8080
2025-11-08 14:03:01,250 - src.services.ai_service - INFO - Fetching available models from Llama.cpp server...
2025-11-08 14:03:03,674 - backend.src.clients.llama_cpp_client - ERROR - Failed to get available models from llama.cpp server: All connection attempts failed
Traceback (most recent call last):
  File "C:\Users\Tcyber\Documents\PROJECTS\TcyberChatbot\backend\.venv\Lib\site-packages\httpx\_transports\default.py", line 101, in map_httpcore_exceptions
    yield
  File "C:\Users\Tcyber\Documents\PROJECTS\TcyberChatbot\backend\.venv\Lib\site-packages\httpx\_transports\default.py", line 394, in handle_async_request
    resp = await self._pool.handle_async_request(req)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Tcyber\Documents\PROJECTS\TcyberChatbot\backend\.venv\Lib\site-packages\httpcore\_async\connection_pool.py", line 256, in handle_async_request
    raise exc from None
  File "C:\Users\Tcyber\Documents\PROJECTS\TcyberChatbot\backend\.venv\Lib\site-packages\httpcore\_async\connection_pool.py", line 236, in handle_async_request
    response = await connection.handle_async_request(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Tcyber\Documents\PROJECTS\TcyberChatbot\backend\.venv\Lib\site-packages\httpcore\_async\connection.py", line 101, in handle_async_request
    raise exc
  File "C:\Users\Tcyber\Documents\PROJECTS\TcyberChatbot\backend\.venv\Lib\site-packages\httpcore\_async\connection.py", line 78, in handle_async_request
    stream = await self._connect(request)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Tcyber\Documents\PROJECTS\TcyberChatbot\backend\.venv\Lib\site-packages\httpcore\_async\connection.py", line 124, in _connect
    stream = await self._network_backend.connect_tcp(**kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Tcyber\Documents\PROJECTS\TcyberChatbot\backend\.venv\Lib\site-packages\httpcore\_backends\auto.py", line 31, in connect_tcp
    return await self._backend.connect_tcp(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Tcyber\Documents\PROJECTS\TcyberChatbot\backend\.venv\Lib\site-packages\httpcore\_backends\anyio.py", line 113, in connect_tcp
    with map_exceptions(exc_map):
  File "C:\Users\Tcyber\AppData\Roaming\uv\python\cpython-3.11.13-windows-x86_64-none\Lib\contextlib.py", line 
158, in __exit__
    self.gen.throw(typ, value, traceback)
  File "C:\Users\Tcyber\Documents\PROJECTS\TcyberChatbot\backend\.venv\Lib\site-packages\httpcore\_exceptions.py", line 14, in map_exceptions
    raise to_exc(exc) from exc
httpcore.ConnectError: All connection attempts failed

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\Tcyber\Documents\PROJECTS\TcyberChatbot\backend\src\clients\llama_cpp_client.py", line 34, in 
get_available_models
    response = await self.client.get("/v1/models")
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Tcyber\Documents\PROJECTS\TcyberChatbot\backend\.venv\Lib\site-packages\httpx\_client.py", line 1768, in get
    return await self.request(
           ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Tcyber\Documents\PROJECTS\TcyberChatbot\backend\.venv\Lib\site-packages\httpx\_client.py", line 1540, in request
    return await self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Tcyber\Documents\PROJECTS\TcyberChatbot\backend\.venv\Lib\site-packages\httpx\_client.py", line 1629, in send
    response = await self._send_handling_auth(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Tcyber\Documents\PROJECTS\TcyberChatbot\backend\.venv\Lib\site-packages\httpx\_client.py", line 1657, in _send_handling_auth
    response = await self._send_handling_redirects(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Tcyber\Documents\PROJECTS\TcyberChatbot\backend\.venv\Lib\site-packages\httpx\_client.py", line 1694, in _send_handling_redirects
    response = await self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Tcyber\Documents\PROJECTS\TcyberChatbot\backend\.venv\Lib\site-packages\httpx\_client.py", line 1730, in _send_single_request
    response = await transport.handle_async_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Tcyber\Documents\PROJECTS\TcyberChatbot\backend\.venv\Lib\site-packages\httpx\_transports\default.py", line 393, in handle_async_request
    with map_httpcore_exceptions():
  File "C:\Users\Tcyber\AppData\Roaming\uv\python\cpython-3.11.13-windows-x86_64-none\Lib\contextlib.py", line 
158, in __exit__
    self.gen.throw(typ, value, traceback)
  File "C:\Users\Tcyber\Documents\PROJECTS\TcyberChatbot\backend\.venv\Lib\site-packages\httpx\_transports\default.py", line 118, in map_httpcore_exceptions
    raise mapped_exc(message) from exc
httpx.ConnectError: All connection attempts failed
2025-11-08 14:03:06,524 - src.services.ai_service - INFO - Found Llama.cpp models: []
2025-11-08 14:03:06,529 - main - INFO - Response: GET /api/v1/models -> 200 (11.355s)
INFO:     127.0.0.1:22486 - "GET /api/v1/models HTTP/1.1" 200 OK
2025-11-08 14:03:06,598 - main - INFO - Request: GET /api/v1/models from 127.0.0.1
2025-11-08 14:03:06,625 - main - INFO - Response: GET /api/v1/models -> 200 (0.027s)
INFO:     127.0.0.1:22489 - "GET /api/v1/models HTTP/1.1" 200 OK
2025-11-08 14:03:35,592 - main - INFO - Request: POST /chat/stream from 127.0.0.1
2025-11-08 14:03:35,629 - src.services.ai_service - INFO - Google Gemini client initialized with model: models/gemini-2.5-flash
2025-11-08 14:03:37,224 - src.services.ai_service - INFO - OpenRouter client initialized with model: openai/gpt-oss-20b:free
2025-11-08 14:03:44,763 - sentence_transformers.SentenceTransformer - INFO - Use pytorch device_name: cpu
2025-11-08 14:03:44,763 - sentence_transformers.SentenceTransformer - INFO - Load pretrained SentenceTransformer: all-MiniLM-L6-v2
Failed to setup compression retriever: 1 validation error for EmbeddingsFilter
embeddings
  instance of Embeddings expected (type=type_error.arbitrary_type; expected_arbitrary_type=Embeddings)
Skipping chain setup: custom_llm is not available (AI service will be lazy-loaded when needed)
2025-11-08 14:03:57,194 - src.api.chat - INFO - Streaming chat request: conversationId=None, documentId=cb9e4263-da65-4db0-b2ea-a8c072fe146e, model=models/gemini-2.5-flash, message_length=2
2025-11-08 14:03:57,923 - main - INFO - Response: POST /chat/stream -> 200 (22.331s)
INFO:     127.0.0.1:22497 - "POST /chat/stream HTTP/1.1" 200 OK
2025-11-08 14:03:57,928 - src.services.ai_service - INFO - Attempting streaming response with OpenRouter using 
model: openai/gpt-3.5-turbo...
2025-11-08 14:04:10,931 - httpx - INFO - HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
2025-11-08 14:04:55,058 - main - INFO - Request: POST /chat/stream from 127.0.0.1
2025-11-08 14:04:55,061 - src.api.chat - INFO - Streaming chat request: conversationId=None, documentId=cb9e4263-da65-4db0-b2ea-a8c072fe146e, model=models/gemini-2.5-flash, message_length=27
2025-11-08 14:04:55,642 - main - INFO - Response: POST /chat/stream -> 200 (0.585s)
INFO:     127.0.0.1:22516 - "POST /chat/stream HTTP/1.1" 200 OK
2025-11-08 14:04:55,648 - src.services.ai_service - INFO - Attempting streaming response with OpenRouter using 
model: openai/gpt-3.5-turbo...
2025-11-08 14:04:59,909 - httpx - INFO - HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 429 Too Many Requests"
2025-11-08 14:04:59,916 - openai._base_client - INFO - Retrying request to /chat/completions in 0.416472 seconds
2025-11-08 14:05:03,961 - httpx - INFO - HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
