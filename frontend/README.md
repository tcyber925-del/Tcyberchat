# Frontend - Local Chatbot UI

A responsive React frontend for the local chatbot application built with Next.js 14+, TypeScript, and shadcn/UI.

## Features

- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Real-time Chat**: Streaming AI responses with message bubbles
- **Document Management**: Upload, organize, and reference documents in conversations
- **Theme Switching**: Light, dark, and system preference themes
- **Accessibility**: WCAG 2.1 AA compliant with keyboard navigation and screen reader support
- **Type-Safe**: Full TypeScript implementation with strict type checking

## Quick Start

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Architecture

### Components

#### ChatBubble
Displays individual messages with support for citations and interactive elements.

```tsx
import ChatBubble from '@/components/chat-bubble';

<ChatBubble
  message={{
    id: '1',
    content: 'Hello, world!',
    timestamp: new Date(),
    type: 'ai',
    conversationId: 'conv-1',
    citations: [{
      id: 1,
      docId: 'doc-1',
      snippet: 'Source text...',
      page: 1
    }]
  }}
  onRegenerate={() => console.log('Regenerate response')}
/>
```

#### MessageInput
Multi-line input with drag-and-drop file upload.

```tsx
import MessageInput from '@/components/message-input';

<MessageInput onSendMessage={(message, files) => {
  console.log('Send:', message, files);
}} />
```

#### Sidebar
Collapsible navigation with chat history and document management.

```tsx
import Sidebar from '@/components/sidebar';

<Sidebar />
```

#### SettingsPanel
User preferences including theme, model selection, and notifications.

```tsx
import SettingsPanel from '@/components/settings-panel';

<SettingsPanel />
```

### Context API

#### ChatContext
Global state management for chat sessions, messages, documents, and UI state.

```tsx
import { useChat } from '@/lib/context/chat-context';

function MyComponent() {
  const {
    messages,
    addMessage,
    isLoading,
    userSettings,
    setUserSettings
  } = useChat();

  // Use chat state...
}
```

#### ThemeContext
Theme management with system preference detection.

```tsx
import { useTheme } from '@/lib/context/theme-context';

function MyComponent() {
  const { theme, setTheme, resolvedTheme } = useTheme();

  return (
    <div className={resolvedTheme === 'dark' ? 'dark' : ''}>
      {/* Your content */}
    </div>
  );
}
```

### API Clients

Type-safe API interactions with automatic error handling.

```tsx
import { sendMessage, getConversations } from '@/lib/api/chat';
import { uploadDocument } from '@/lib/api/documents';

// Send a message
const response = await sendMessage('Hello, AI!', 'session-1');

// Upload a document
const doc = await uploadDocument(file);

// Get conversations
const conversations = await getConversations();
```

## Testing

```bash
# Run all tests
npm test

# Run unit tests only
npm run test:unit

# Run integration tests
npm run test:integration
```

## Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_APP_NAME=Local Chatbot
```

## Build & Deployment

```bash
# Build for production
npm run build

# Start production server
npm start
```

## Accessibility

The application follows WCAG 2.1 AA guidelines:

- Semantic HTML structure
- ARIA labels and descriptions
- Keyboard navigation support
- Screen reader compatibility
- Sufficient color contrast
- Focus management

## Performance

- Code splitting with dynamic imports
- Lazy loading for heavy components
- Optimized re-renders with React.memo
- Efficient API caching
- Bundle size optimization

## Development

### Adding New Components

1. Create component in `src/components/`
2. Add TypeScript interfaces in `src/types/`
3. Write unit tests in `tests/unit/`
4. Update this README with usage examples

### API Integration

1. Define types in `src/types/`
2. Create API client in `src/lib/api/`
3. Add error handling and loading states
4. Write contract tests

### Styling

Uses Tailwind CSS with shadcn/UI design system:

- Consistent spacing and colors
- Responsive breakpoints
- Dark mode support
- Accessible focus states

## Contributing

1. Follow the existing code style
2. Write tests for new features
3. Update documentation
4. Ensure accessibility compliance
