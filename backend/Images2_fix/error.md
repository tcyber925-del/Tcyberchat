Initializing databases...
SQLAlchemy tables created successfully
Running lightweight SQLite migrations...
ChromaDB initialized successfully
All databases initialized successfully!
INFO:     Started server process [5812]
INFO:     Waiting for application startup.
2025-11-03 18:37:48,348 - main - INFO - Application starting up...
INFO:     Application startup complete.
2025-11-03 18:47:08,619 - main - INFO - Request: GET /documents from 127.0.0.1
2025-11-03 18:47:08,771 - main - INFO - Response: GET /documents -> 307 (0.153s)
INFO:     127.0.0.1:26670 - "GET /documents HTTP/1.1" 307 Temporary Redirect
2025-11-03 18:47:08,949 - main - INFO - Request: GET /documents/ from 127.0.0.1
2025-11-03 18:47:09,064 - src.api.documents - INFO - Fetching all documents
2025-11-03 18:47:09,272 - src.api.documents - INFO - Found 0 documents
2025-11-03 18:47:09,380 - main - INFO - Response: GET /documents/ -> 200 (0.430s)
INFO:     127.0.0.1:26670 - "GET /documents/ HTTP/1.1" 200 OK
2025-11-03 18:49:04,022 - main - INFO - Request: GET /api/v1/models from 127.0.0.1
2025-11-03 18:49:05,071 - src.services.ai_service - INFO - Google Gemini client initialized with model: models/gemini-2.5-flash
2025-11-03 18:49:05,728 - src.services.ai_service - INFO - OpenRouter client initialized with model: openai/gpt-oss-20b:free2025-11-03 18:49:14,607 - httpx - INFO - HTTP Request: GET http://127.0.0.1:11434/api/tags "HTTP/1.1 200 OK"
2025-11-03 18:49:14,945 - src.services.ai_service - WARNING - Could not retrieve Ollama models: "Model" object has no field 
"provider"
2025-11-03 18:49:14,947 - main - INFO - Response: GET /api/v1/models -> 200 (10.925s)
INFO:     127.0.0.1:26694 - "GET /api/v1/models HTTP/1.1" 200 OK
2025-11-03 18:49:14,951 - main - INFO - Request: GET /api/v1/models from 127.0.0.1
2025-11-03 18:49:15,042 - httpx - INFO - HTTP Request: GET http://127.0.0.1:11434/api/tags "HTTP/1.1 200 OK"
2025-11-03 18:49:15,044 - src.services.ai_service - WARNING - Could not retrieve Ollama models: "Model" object has no field 
"provider"
2025-11-03 18:49:15,045 - main - INFO - Response: GET /api/v1/models -> 200 (0.094s)
INFO:     127.0.0.1:26697 - "GET /api/v1/models HTTP/1.1" 200 OK
2025-11-03 18:49:41,231 - main - INFO - Request: POST /chat/stream from 127.0.0.1
2025-11-03 18:49:41,948 - src.services.ai_service - INFO - Google Gemini client initialized with model: models/gemini-2.5-flash
2025-11-03 18:49:42,678 - src.services.ai_service - INFO - OpenRouter client initialized with model: openai/gpt-oss-20b:free2025-11-03 18:49:43,755 - src.services.ai_service - INFO - Google Gemini client initialized with model: models/gemini-2.5-flash
2025-11-03 18:49:44,510 - src.services.ai_service - INFO - OpenRouter client initialized with model: openai/gpt-oss-20b:free2025-11-03 18:49:51,912 - sentence_transformers.SentenceTransformer - INFO - Use pytorch device_name: cpu
2025-11-03 18:49:51,913 - sentence_transformers.SentenceTransformer - INFO - Load pretrained SentenceTransformer: all-MiniLM-L6-v2
Failed to setup advanced retrievers: name 'EnsembleRetriever' is not defined
Failed to setup chains: name 'BaseLLM' is not defined
2025-11-03 18:50:04,879 - src.api.chat - INFO - Streaming chat request: conversationId=None, documentId=None, model=llama3.2:latest, message_length=5
2025-11-03 18:50:05,882 - main - INFO - Response: POST /chat/stream -> 200 (24.651s)
INFO:     127.0.0.1:26721 - "POST /chat/stream HTTP/1.1" 200 OK
2025-11-03 18:50:06,130 - httpx - INFO - HTTP Request: GET http://127.0.0.1:11434/api/tags "HTTP/1.1 200 OK"
2025-11-03 18:50:06,133 - src.services.ai_service - INFO - Attempting streaming response with Ollama using model: llama3.2:latest...
2025-11-03 18:50:06,403 - httpx - INFO - HTTP Request: POST http://127.0.0.1:11434/api/generate "HTTP/1.1 404 Not Found"
2025-11-03 18:50:06,407 - src.services.ai_service - ERROR - Streaming response failed for llama3.2:latest: model 'llama3.2:latest' not found (status code: 404)
