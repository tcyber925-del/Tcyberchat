# Data Model: Build a Local First Chatbot

## Entities

### Message
Represents individual chat messages in conversations.

**Fields**:
- `id`: String (UUID) - Unique identifier
- `content`: String - Message text content
- `timestamp`: DateTime - When message was sent
- `type`: Enum (user, bot) - Who sent the message
- `conversationId`: String (UUID) - Links to conversation thread
- `citations`: Array<Object> - Source references with documentId, page, snippet
- `metadata`: Object - Additional data like processing time, model used

**Validation Rules**:
- `content` cannot be empty
- `content` max length 10000 characters
- `timestamp` defaults to current time
- `citations` optional array of citation objects

**Relationships**:
- Belongs to Conversation
- References Documents via citations

### Document
Represents uploaded files for processing (text, images, audio).

**Fields**:
- `id`: String (UUID) - Unique identifier
- `filename`: String - Original filename
- `path`: String - Local file system path
- `size`: Number - File size in bytes
- `mimeType`: String - MIME type (text/plain, application/pdf, image/*, audio/*, etc.)
- `uploadedAt`: DateTime - Upload timestamp
- `content`: String - Extracted text content (from text extraction, OCR, transcription)
- `chunks`: Array<String> - Text chunks for embedding (generated from content)
- `vectorStoreId`: String - ChromaDB collection ID for embeddings
- `previewImage`: String - Path to generated preview/thumbnail (for images/documents)
- `transcription`: String - Audio transcription text (for audio files)
- `imageAnalysis`: Object - AI analysis results for images/diagrams
- `status`: Enum (uploading, processing, transcribing, analyzing, embedding, ready, error) - Processing status

**Validation Rules**:
- `size` <= 52428800 (50MB) for text, <= 10485760 (10MB) for images/audio
- `mimeType` in supported formats: ['text/plain', 'application/pdf', 'text/markdown', 'image/jpeg', 'image/png', 'audio/mpeg', 'audio/wav']
- `filename` not empty, max 255 chars

**Relationships**:
- Has many Summaries
- Referenced by Messages (for document-specific chat)
- Contains MediaContent (for rich content rendering)

### Summary
Represents AI-generated summaries of documents.

**Fields**:
- `id`: String (UUID) - Unique identifier
- `documentId`: String (UUID) - Reference to Document
- `content`: String - Summary text
- `createdAt`: DateTime - Generation timestamp
- `model`: String - AI model used (e.g., "llama3.1:8b")

**Validation Rules**:
- `content` cannot be empty
- `content` max length 5000 characters
- `documentId` must reference existing Document

### MediaContent
Represents embedded media and rich content for chat rendering.

**Fields**:
- `id`: String (UUID) - Unique identifier
- `messageId`: String (UUID) - Parent message
- `type`: Enum (image, table, code_block, diagram) - Content type
- `content`: String - Raw content data (HTML, Markdown, JSON)
- `metadata`: Object - Rendering metadata (dimensions, syntax language, etc.)

**Validation Rules**:
- `type` determines validation of `content` format
- `messageId` must reference existing Message

**Relationships**:
- Belongs to Message
- References Documents (for source attribution)

### Conversation (Optional)
Represents chat sessions for organizing message threads.

**Fields**:
- `id`: String (UUID) - Unique identifier
- `title`: String - Auto-generated or user-set conversation title
- `startedAt`: DateTime - Session start
- `lastActivity`: DateTime - Last message timestamp
- `documentId`: String (UUID) - Optional linked document for document-specific chats

**Validation Rules**:
- `title` max length 100 characters, defaults to first message preview

**Relationships**:
- Has many Messages
- Belongs to Document (optional)

## State Transitions

### Document Processing States
- `uploading` → `processing` (after upload complete)
- `processing` → `transcribing` (for audio files)
- `processing` → `analyzing` (for images/diagrams)
- `processing` → `embedding` (after content extraction successful)
- `transcribing` → `embedding` (after transcription complete)
- `analyzing` → `embedding` (after analysis complete)
- `embedding` → `ready` (after vector embeddings generated)
- Any state → `error` (if processing fails)

### Conversation
Represents chat sessions for organizing message threads.

**Fields**:
- `id`: String (UUID) - Unique identifier
- `title`: String - Auto-generated or user-set conversation title
- `startedAt`: DateTime - Session start
- `lastActivity`: DateTime - Last message timestamp
- `documentId`: String (UUID) - Optional linked document for document-specific chats

**Validation Rules**:
- `title` max length 100 characters, defaults to first message preview

**Relationships**:
- Has many Messages
- Belongs to Document (optional)

## State Transitions

### Document Processing States
- `uploading` → `processing` (after upload complete)
- `processing` → `embedding` (after text extraction successful)
- `embedding` → `ready` (after vector embeddings generated)
- `processing` → `error` (if extraction fails)
- `embedding` → `error` (if embedding generation fails)
- `uploading` → `error` (if upload fails)

## Data Storage
- Documents: File system storage with metadata in SQLite
- Messages/Summaries/Conversations: SQLite database
- No external dependencies or cloud storage