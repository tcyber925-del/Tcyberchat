# Quickstart Validation: Build a Local First Chatbot

This document outlines the steps to validate that the core user stories work correctly. Run these tests after implementation to ensure the application meets requirements.

## Prerequisites
- Application is running locally (frontend on port 3000, backend on port 3001)
- Ollama is installed and running with llama3.2:8b model
- Test files: sample.txt (text file), sample.pdf (PDF document)

## Test Scenario 1: Modern Chat Interface

**Given** the application is loaded
**When** the user interacts with the UI
**Then** all interface components work correctly

### Steps:
1. Open web application in browser (http://localhost:3000)
2. **Expected**: Clean, modern interface with sidebar for documents/history, main chat area, and settings panel
3. Verify chat bubbles display properly with user/bot distinction
4. Check typing indicators appear during responses
5. Confirm streaming text appears character-by-character

## Test Scenario 2: General Chat (No Document)

**Given** no document is uploaded
**When** the user sends a chat message
**Then** the chatbot streams a relevant response

### Steps:
1. In the chat input, type: "Hello, how are you?"
2. Click Send or press Enter
3. **Expected**: Response streams in real-time within 2 seconds total
4. Verify message appears in chat history sidebar
5. Check conversation is saved and retrievable

## Test Scenario 2: Document Upload

**Given** user wants to upload a document
**When** user selects and uploads a file
**Then** document is accepted and processed

### Steps:
1. Click "Upload Document" button or drag-drop area
2. Select sample.txt or sample.pdf from file picker
3. Click upload
4. **Expected**: Document appears in document list with "processing" status
5. Status changes to "ready" within 30 seconds (text extraction complete)

## Test Scenario 3: Document Summarization

**Given** a document is uploaded and ready
**When** user requests summarization
**Then** AI generates and displays summary

### Steps:
1. From document list, click "Summarize" on an uploaded document
2. Wait for processing
3. **Expected**: Summary text appears within 10 seconds
4. Summary should be coherent and capture main points of document

## Test Scenario 4: Document-Specific Chat

**Given** a document is uploaded and ready
**When** user asks questions about the document content
**Then** chatbot responds using document context

### Steps:
1. Select uploaded document from list
2. In chat input, type: "What are the main topics discussed in this document?"
3. Send message
4. **Expected**: Response references specific content from the document
5. Verify response is document-aware, not generic

## Test Scenario 5: Document Management UI

**Given** documents are uploaded
**When** user manages documents via UI
**Then** all management features work

### Steps:
1. View document list in sidebar
2. **Expected**: Shows filename, size, status (ready/processing/error)
3. Click delete on a document
4. **Expected**: Document removed from list and storage
5. Upload new document via drag-drop
6. **Expected**: Progress indicator during upload/processing

## Test Scenario 6: Chat History and Navigation

**Given** multiple conversations exist
**When** user navigates chat history
**Then** interface updates correctly

### Steps:
1. Start new conversation (different from default)
2. Send a few messages
3. Switch to previous conversation via history sidebar
4. **Expected**: Chat area updates to show selected conversation
5. Verify conversation titles are auto-generated

## Test Scenario 7: Settings Panel

**Given** settings panel is accessible
**When** user configures options
**Then** settings persist and affect behavior

### Steps:
1. Open settings panel (gear icon)
2. **Expected**: Options for model selection, streaming toggle, theme, keyboard shortcuts
3. Change theme setting (dark/light toggle)
4. **Expected**: UI theme updates immediately and persists
5. Toggle streaming off
6. **Expected**: Responses appear all at once instead of streaming
7. Test keyboard shortcuts (Ctrl+Enter to send)
8. **Expected**: Shortcuts work as configured

## Test Scenario 9: Advanced RAG Features

**Given** documents are uploaded and indexed
**When** user queries with document context
**Then** responses include citations and source references

### Steps:
1. Upload multiple documents
2. Ask: "Compare the approaches in these documents"
3. **Expected**: Response includes clickable citations with document names and page references
4. Hover over citations
5. **Expected**: Snippet preview appears
6. Click citation link
7. **Expected**: Document viewer opens to relevant section

## Test Scenario 10: Image Analysis

**Given** image or diagram is uploaded
**When** user requests analysis or asks questions
**Then** AI understands and describes visual content

### Steps:
1. Upload a flowchart diagram image
2. Ask: "What does this flowchart represent?"
3. **Expected**: Detailed description of the diagram and its purpose
4. Upload a photo with text
5. Ask: "What text is visible in this image?"
6. **Expected**: Accurate OCR and text extraction
7. Ask: "Describe the main objects in this image"
8. **Expected**: Object detection and description

## Test Scenario 11: Audio Transcription

**Given** audio file is uploaded
**When** user requests transcription
**Then** audio is converted to searchable text

### Steps:
1. Upload a short audio recording (meeting clip)
2. Wait for processing
3. **Expected**: Transcription appears with timestamps
4. Search for a word mentioned in audio
5. **Expected**: Search results include the transcribed content
6. Ask questions about the audio content
7. **Expected**: Chat responses based on transcription

## Test Scenario 12: Rich Content Rendering

**Given** chat contains various content types
**When** content is displayed
**Then** rich formatting is properly rendered

### Steps:
1. Receive a response with code blocks
2. **Expected**: Syntax highlighting and proper formatting
3. Receive a response with tables
4. **Expected**: Properly formatted table display
5. Receive a response with images
6. **Expected**: Images display inline with appropriate sizing
7. Test markdown formatting
8. **Expected**: Headers, lists, and links render correctly

## Test Scenario 10: Data Management

**Given** conversations and documents exist
**When** user performs data operations
**Then** all operations work correctly

### Steps:
1. Export conversation history
2. **Expected**: JSON file downloaded with all messages and metadata
3. Search across all documents: "specific term"
4. **Expected**: Results show matching documents with snippets
5. Bulk delete multiple documents
6. **Expected**: Confirmation dialog and progress indicator
7. Import previously exported data
8. **Expected**: Data restored correctly

## Test Scenario 8: Error Handling

**Given** various error conditions
**When** errors occur
**Then** user receives appropriate feedback

### Steps:
1. Try uploading file >50MB → Should show error message
2. Try uploading unsupported format (e.g., .exe) → Should reject
3. Send empty message → Should show validation error
4. Request summary of non-existent document → Should show 404 error

## Performance Validation

- **Response Time**: General chat <2 seconds, summarization <10 seconds, search <1 second, image analysis <15 seconds, audio transcription <60 seconds per minute
- **Memory Usage**: Application should not exceed 2GB RAM during normal operation, 4GB during document processing, 6GB during multi-modal processing
- **File Processing**: PDF text extraction <30 seconds for 10MB file, embedding generation <60 seconds, image analysis <15 seconds, audio transcription <60 seconds per minute
- **Caching**: Frequent queries served from cache <500ms
- **Concurrent Users**: Support for 1-5 concurrent users without performance degradation
- **Resource Monitoring**: CPU usage <80%, disk I/O optimized for vector searches, GPU memory <4GB for multi-modal models

## Success Criteria

All test scenarios pass:
- [ ] Modern chat interface loads correctly
- [ ] General chat works with streaming
- [ ] Document upload succeeds with progress tracking
- [ ] Summarization generates useful output
- [ ] Document management UI works
- [ ] Chat history navigation works
- [ ] Settings panel functions properly with themes and shortcuts
- [ ] Document chat uses context
- [ ] Advanced RAG with citations works
- [ ] Data management (export/import/search) functions
- [ ] Image analysis understands diagrams and visual content
- [ ] Audio transcription converts speech to searchable text
- [ ] Rich content rendering displays tables, code, and images
- [ ] Multi-modal conversations work seamlessly
- [ ] Error recovery and graceful degradation
- [ ] Performance requirements met with caching
- [ ] Resource monitoring displays metrics
- [ ] Background processing doesn't block UI

## Cleanup
- Delete test documents after validation
- Clear chat history if needed