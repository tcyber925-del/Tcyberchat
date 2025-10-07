Design and develop a responsive frontend UI, incorporating the following detailed components and functionalities:

**1. Collapsible Sidebar:**
    *   **Toggle Mechanism:** Implement a smooth, animated collapse/expand functionality.
    *   **New Chat Button:** Clearly visible button to initiate a new conversation, clearing the current chat context.
    *   **Chat Search:** An input field with real-time filtering capabilities to search through chat history by keywords.
    *   **Chat History:** A scrollable list displaying recent and saved chat sessions, each with a title/summary and timestamp, allowing users to resume conversations.
    *   **Document Management:** A section or dedicated tab within the sidebar to view, upload, organize, and manage documents previously uploaded or referenced in chats, with options for filtering and sorting.

**2. Top Bar (Right-aligned):**
    *   **Export/Import Functionality:** Buttons to export chat transcripts (e.g., JSON, PDF, TXT) and import previously exported chat data or settings.
    *   **Settings Panel:** A modal or dropdown accessible via an icon, containing:
        *   **Model Selection:** A dropdown or radio button group to choose between different AI models (e.g., GPT-4, Gemini, custom models).
        *   **Theme Toggle:** A switch or button for dark/light mode selection.
        *   **Other Configurations:** Placeholder for additional user preferences such as notification settings, language selection, API key management, or default behaviors.

**3. Main Chat Interface Area:**
    *   **Chat Bubbles:**
        *   **User Messages:** Distinctly styled bubbles for user input.
        *   **AI Responses:** Distinctly styled bubbles for AI output, potentially with a different background color or avatar.
        *   **Citations:** Integrate a mechanism to display citations (e.g., numbered links) within AI responses, linking to relevant sections of uploaded documents or web search results.
        *   **Document Chat Integration:** Clearly indicate when AI responses are directly referencing or summarizing content from uploaded documents.
        *   **Interactive Elements:** Consider adding copy-to-clipboard, regenerate response, or feedback (thumbs up/down) options on AI messages.
    *   **Chat Message Input Area:**
        *   **Text Input Field:** A multi-line, resizable text area for typing messages.
        *   **Drag and Drop File/Document Upload:** Implement a visual indicator and functionality for users to drag and drop files directly into the input area for upload.
        *   **Send Button:** A prominent button to submit the message, active only when there is input.
        *   **Web Search Button:** An icon/button that, when toggled or clicked, instructs the AI to perform a web search as part of its response generation.
        *   **Attachment Button:** An icon/button to open a file browser for selecting and uploading multiple files/documents, with a preview of attached files before sending.

**General UI/UX Considerations:**
*   Ensure a clean, intuitive, and modern design aesthetic.
*   Implement responsive design principles for optimal viewing across various screen sizes (desktop, tablet, mobile).
*   Prioritize accessibility (ARIA attributes, keyboard navigation).
*   Provide clear visual feedback for user actions (e.g., loading states, successful uploads, error messages).
*   Utilize consistent typography, color schemes, and iconography.