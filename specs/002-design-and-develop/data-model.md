# Data Model: Responsive Frontend UI

## Frontend Data Entities

### ChatSession
Represents a conversation thread in the chat interface.

**Fields:**
- `id`: string (UUID) - Unique identifier
- `title`: string - Auto-generated or user-edited title
- `summary`: string - Brief summary of conversation
- `timestamp`: Date - Creation timestamp
- `lastActivity`: Date - Last message timestamp
- `messageCount`: number - Total messages in session
- `documentId`: string? - Associated document ID if chat is document-specific

**Validation Rules:**
- `id`: required, UUID format
- `title`: required, max 100 characters
- `summary`: optional, max 500 characters
- `timestamp`: required, ISO date string
- `lastActivity`: required, ISO date string
- `messageCount`: required, >= 0

**State Transitions:**
- Created → Active (first message sent)
- Active → Paused (user navigates away)
- Paused → Active (user resumes)
- Any state → Deleted (user deletes session)

### Message
Represents individual messages in a chat session.

**Fields:**
- `id`: string (UUID) - Unique identifier
- `content`: string - Message text content
- `timestamp`: Date - Send timestamp
- `type`: 'user' | 'ai' - Message sender type
- `conversationId`: string - Parent conversation ID
- `citations`: Citation[] - Array of citations (see below)
- `metadata`: object - Additional data (model used, tokens, etc.)

**Validation Rules:**
- `id`: required, UUID format
- `content`: required, non-empty
- `timestamp`: required, ISO date string
- `type`: required, enum values
- `conversationId`: required, valid UUID

**Relationships:**
- Belongs to ChatSession (conversationId)
- Has many Citations

### Citation
Represents a reference to source material in AI responses.

**Fields:**
- `id`: number - Sequential citation number
- `docId`: string - Document ID being cited
- `page`: number? - Page number if applicable
- `snippet`: string - Quoted text snippet
- `url`: string? - Link to source if web result

**Validation Rules:**
- `id`: required, > 0
- `docId`: required, valid document ID
- `snippet`: required, non-empty, max 500 characters

**Relationships:**
- Belongs to Message

### Document
Represents uploaded documents for chat reference.

**Fields:**
- `id`: string (UUID) - Unique identifier
- `filename`: string - Original filename
- `size`: number - File size in bytes
- `mimeType`: string - MIME type
- `uploadedAt`: Date - Upload timestamp
- `status`: 'uploading' | 'processing' | 'analyzing' | 'transcribing' | 'embedding' | 'ready' | 'error'
- `hasContent`: boolean - Whether text content is extracted
- `hasTranscription`: boolean - Whether audio transcription exists
- `hasImageAnalysis`: boolean - Whether OCR/image analysis done
- `previewImage`: string? - Base64 or URL for preview

**Validation Rules:**
- `id`: required, UUID format
- `filename`: required, max 255 characters
- `size`: required, > 0, < 100MB
- `mimeType`: required, valid MIME type
- `uploadedAt`: required, ISO date string
- `status`: required, enum values

### UserSettings
Represents user preferences and configuration.

**Fields:**
- `theme`: 'light' | 'dark' | 'system' - UI theme preference
- `selectedModel`: string - Preferred AI model ID
- `notifications`: boolean - Enable notifications
- `language`: string - UI language code
- `apiKeys`: object - Stored API keys (encrypted)

**Validation Rules:**
- `theme`: required, enum values
- `selectedModel`: required, valid model ID
- `language`: optional, valid language code

**Default Values:**
- `theme`: 'system'
- `notifications`: true
- `language`: 'en'

## API Integration Models

These mirror backend models for frontend consumption:

### API Response Models
- `ChatResponse`: Streaming response from chat API
- `DocumentUploadResponse`: Upload confirmation
- `ExportResponse`: Export download URL
- `SearchResponse`: Web search results

### Form Models
- `MessageForm`: Input validation for new messages
- `SettingsForm`: Settings panel validation
- `UploadForm`: File upload validation

## Client-side State Management

### Global State
- Current chat session
- User settings
- Document list cache
- UI state (sidebar open/closed, loading states)

### Component State
- Form inputs
- Modal visibility
- Loading indicators
- Error messages

## Data Flow Patterns

1. **Chat Flow**: User input → API call → Streaming response → Update UI
2. **Upload Flow**: File selection → Validation → Upload → Status updates → Document list refresh
3. **Settings Flow**: Form changes → Validation → Save to localStorage → UI update
4. **Search Flow**: Query input → Debounced API call → Filter results → Update list

## Performance Considerations

- Paginate chat messages (virtual scrolling for long conversations)
- Cache document metadata in localStorage
- Debounce search inputs
- Lazy load document previews
- Optimize re-renders with React.memo