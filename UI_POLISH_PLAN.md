# UI Polish Implementation Plan

## Overview
This document outlines the comprehensive plan to implement three UI/UX improvements:
1. Drag-and-drop document upload on chat input field
2. Selected document indicator in chat input area
3. Chat history persistence with metadata in SQL database

## Current State Analysis

### Existing Infrastructure
- **Database Models**: `Conversation` and `Message` models already exist in `backend/src/models/`
- **Chat Service**: `ChatService` in `backend/src/services/chat_service.py` handles conversation/message CRUD
- **API Endpoints**: `/chat/stream` endpoint already saves messages via `chat_service.add_message()`
- **Frontend Components**: 
  - `ChatInput` component in `frontend/src/components/ui/chat.tsx`
  - `prompt-input.tsx` has file attachment support
  - Main page uses simple textarea in `frontend/src/app/page.tsx`

### Current Gaps
1. **Drag-and-drop**: Not implemented on chat input field
2. **Document indicator**: No visual feedback when document is selected
3. **Chat persistence**: Messages are saved, but frontend doesn't load them on page refresh

---

## Feature 1: Drag-and-Drop Document Upload

### Requirements
- Allow users to drag files onto the chat input area
- Visual feedback during drag (highlight, border change)
- Support same file types as current upload (PDF, TXT, images, audio)
- Prevent default browser file open behavior
- Show upload progress/status

### Implementation Plan

#### Frontend Changes

**File: `frontend/src/app/page.tsx`**
- Add drag-and-drop event handlers to the form/input container
- Add state for drag-over visual feedback
- Integrate with existing `uploadDocument` function
- Add visual indicators (border highlight, background change)

**Changes:**
```typescript
// Add state
const [isDragging, setIsDragging] = useState(false);

// Add handlers
const handleDragEnter = (e: React.DragEvent) => {
  e.preventDefault();
  e.stopPropagation();
  setIsDragging(true);
};

const handleDragLeave = (e: React.DragEvent) => {
  e.preventDefault();
  e.stopPropagation();
  setIsDragging(false);
};

const handleDragOver = (e: React.DragEvent) => {
  e.preventDefault();
  e.stopPropagation();
};

const handleDrop = (e: React.DragEvent) => {
  e.preventDefault();
  e.stopPropagation();
  setIsDragging(false);
  
  const files = Array.from(e.dataTransfer.files);
  if (files.length > 0) {
    uploadDocument(files[0]);
  }
};
```

**Styling:**
- Add conditional classes: `border-2 border-dashed border-primary` when `isDragging`
- Add background color change: `bg-primary/5` when dragging
- Smooth transitions for visual feedback

#### Testing Checklist
- [ ] Drag file onto input area triggers upload
- [ ] Visual feedback appears during drag
- [ ] Multiple file types work (PDF, TXT, images)
- [ ] Drag-and-drop doesn't interfere with text input
- [ ] Error handling for invalid file types
- [ ] Upload progress/status is visible

---

## Feature 2: Selected Document Indicator

### Requirements
- Show selected document name/icon in chat input area
- Display when a document is selected for conversation
- Allow deselecting the document
- Visual indicator should be clear but not intrusive
- Show document metadata (filename, upload date)

### Implementation Plan

#### Frontend Changes

**File: `frontend/src/app/page.tsx`**
- Add document indicator component above or within input area
- Use `selectedDocumentId` from `chat-context`
- Fetch document details when selected
- Add close/remove button

**New Component: `frontend/src/components/document-indicator.tsx`**
```typescript
interface DocumentIndicatorProps {
  documentId: string;
  documentName: string;
  onRemove: () => void;
}
```

**Visual Design:**
- Badge/chip style indicator
- Document icon + filename
- Close (X) button to deselect
- Positioned above or integrated into input area
- Subtle background color to distinguish from input

**Integration:**
- Show when `selectedDocumentId` is not null
- Hide when no document selected
- Update when document selection changes

#### Backend Changes
- No changes needed (document info already available via existing API)

#### Testing Checklist
- [ ] Indicator appears when document is selected
- [ ] Shows correct document name
- [ ] Remove button deselects document
- [ ] Indicator updates when switching documents
- [ ] Doesn't interfere with input functionality
- [ ] Responsive design works on mobile

---

## Feature 3: Chat History Persistence

### Requirements
- Load conversation history on page load
- Save all messages with metadata (model used, document ID, timestamps)
- Persist conversation state (title, document association)
- Load messages when selecting a conversation from sidebar
- Ensure no data loss on page refresh

### Current State Analysis

**Backend:**
- ✅ `Conversation` model exists with all needed fields
- ✅ `Message` model exists with citations and metadata
- ✅ `ChatService` has methods: `create_conversation`, `get_conversation`, `get_conversations`, `add_message`
- ✅ API endpoint `/chat/stream` saves messages to database
- ✅ API endpoint `/chat/conversations` exists to list conversations

**Frontend:**
- ❌ Messages are only stored in React state (lost on refresh)
- ❌ Conversations are not loaded from database on page load
- ❌ Selecting a conversation doesn't load its messages

### Implementation Plan

#### Backend Changes

**File: `backend/src/api/chat.py`**
- Verify `/chat/conversations/:id` endpoint exists and returns messages
- Ensure message metadata includes:
  - `model_used`: The AI model that generated the response
  - `document_id`: Associated document if any
  - `processing_time`: Response generation time
  - `token_count`: If available

**Enhancement: Add metadata to messages**
```python
# In chat_stream endpoint, when saving messages:
processing_metadata = {
    "model_used": request.model,
    "document_id": str(request.documentId) if request.documentId else None,
    "timestamp": datetime.now(timezone.utc).isoformat(),
}
```

#### Frontend Changes

**File: `frontend/src/lib/context/chat-context.tsx`**
- Add `loadConversations()` function to fetch from `/api/chat/conversations`
- Add `loadConversationMessages(conversationId)` to fetch messages
- Update `selectSession()` to load messages when session is selected
- Add `useEffect` to load conversations on mount
- Persist current conversation ID in localStorage (optional)

**New API Functions: `frontend/src/lib/api/chat.ts`**
```typescript
export async function getConversations(): Promise<ChatSession[]>
export async function getConversationMessages(conversationId: string): Promise<Message[]>
```

**State Management:**
- Load conversations on `ChatProvider` mount
- Load messages when `currentSession` changes
- Save conversation ID when creating new conversation
- Update conversation title based on first message

**File: `frontend/src/app/page.tsx`**
- Ensure messages are loaded when session is selected
- Handle loading states during data fetch

#### Database Schema Verification

**Verify existing fields in `Message` model:**
- ✅ `content`: Text content
- ✅ `timestamp`: When message was created
- ✅ `type`: 'user' or 'bot'
- ✅ `conversation_id`: Foreign key to conversation
- ✅ `citations`: JSON field for RAG citations
- ✅ `processing_metadata`: JSON field for model, document_id, etc.

**Verify existing fields in `Conversation` model:**
- ✅ `id`: Primary key
- ✅ `title`: Conversation title
- ✅ `started_at`: Creation timestamp
- ✅ `last_activity`: Last message timestamp
- ✅ `document_id`: Optional document association
- ✅ `metrics`: JSON for token counts, etc.

#### Migration Strategy
- No database migration needed (schema already supports all requirements)
- Ensure existing messages have proper metadata structure
- Add default values for missing metadata fields if needed

#### Testing Checklist
- [ ] Conversations load on page refresh
- [ ] Messages load when selecting a conversation
- [ ] New messages are saved with metadata
- [ ] Document association is preserved
- [ ] Model used is recorded in metadata
- [ ] Citations are saved and loaded correctly
- [ ] Conversation titles are generated/updated
- [ ] No duplicate messages on reload
- [ ] Performance is acceptable with large conversation history

---

## Implementation Order

### Phase 1: Chat History Persistence (Foundation)
1. Implement backend metadata enhancement
2. Add frontend API functions for loading conversations/messages
3. Update chat context to load and persist data
4. Test data persistence across page refreshes

### Phase 2: Document Indicator (Visual Feedback)
1. Create document indicator component
2. Integrate with chat input area
3. Add remove/deselect functionality
4. Test visual feedback and interactions

### Phase 3: Drag-and-Drop (UX Enhancement)
1. Add drag-and-drop handlers to input area
2. Implement visual feedback during drag
3. Integrate with existing upload flow
4. Test file upload via drag-and-drop

---

## Risk Mitigation

### Breaking Changes Prevention
1. **Backward Compatibility**: Ensure existing API endpoints continue to work
2. **State Management**: Don't break existing message/conversation state
3. **Component Isolation**: New components don't affect existing UI
4. **Database**: No schema changes, only use existing fields

### Testing Strategy
1. **Unit Tests**: Test new functions/components in isolation
2. **Integration Tests**: Test API endpoints with database
3. **E2E Tests**: Test full user flows (upload, chat, reload)
4. **Regression Tests**: Verify existing functionality still works

### Rollback Plan
1. Each feature is independent and can be disabled via feature flags
2. Database changes are additive only (no destructive changes)
3. Frontend changes are component-based (easy to revert)

---

## Success Criteria

### Feature 1: Drag-and-Drop
- ✅ Users can drag files onto input area
- ✅ Visual feedback is clear and responsive
- ✅ Upload works same as button-based upload
- ✅ No interference with text input

### Feature 2: Document Indicator
- ✅ Selected document is clearly visible
- ✅ Easy to deselect document
- ✅ Indicator updates correctly
- ✅ Doesn't clutter the UI

### Feature 3: Chat History
- ✅ Conversations persist across page refreshes
- ✅ Messages load correctly when selecting conversation
- ✅ Metadata is preserved (model, document, citations)
- ✅ Performance is acceptable with large histories

---

## Timeline Estimate

- **Phase 1 (Chat History)**: 2-3 hours
- **Phase 2 (Document Indicator)**: 1-2 hours
- **Phase 3 (Drag-and-Drop)**: 1-2 hours
- **Testing & Polish**: 1-2 hours

**Total**: 5-9 hours

---

## Notes

- All changes maintain backward compatibility
- No database migrations required
- Existing functionality remains intact
- Features can be implemented incrementally
- Each feature is independently testable








