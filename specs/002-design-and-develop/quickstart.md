# Quick Start Guide: Responsive Frontend UI

## Prerequisites
- Node.js 18+ installed
- Backend API running on `http://localhost:3001`
- Basic knowledge of React and TypeScript

## Setup Instructions

### 1. Install Dependencies
```bash
cd frontend
npm install
# or
pnpm install
```

### 2. Environment Configuration
Create `.env.local` file:
```env
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_APP_NAME=Local Chatbot
```

### 3. Start Development Server
```bash
npm run dev
# or
pnpm dev
```

Open `http://localhost:5173` in your browser.

## Basic Usage

### Starting a Chat
1. Click the "New Chat" button in the sidebar
2. Type your message in the input area
3. Press Enter or click Send

### Uploading Documents
1. Drag files to the input area, or click the attachment button
2. Wait for upload progress indicator
3. Reference documents in your chat messages

### Managing Settings
1. Click the settings icon in the top bar
2. Select your preferred AI model
3. Toggle theme (light/dark/system)
4. Configure other preferences

### Exporting Conversations
1. Click the export button in the top bar
2. Choose format (JSON/PDF/TXT)
3. Download the file

## Testing Checklist

### Manual Testing Steps
- [ ] Sidebar toggles smoothly on desktop and mobile
- [ ] New chat clears previous conversation
- [ ] Chat search filters history correctly
- [ ] File upload shows progress and preview
- [ ] AI responses display with citations
- [ ] Citations link to document sections
- [ ] Settings persist across sessions
- [ ] Export includes all conversation data
- [ ] Interface works on mobile devices
- [ ] Keyboard navigation works for accessibility

### Performance Validation
- [ ] Initial page load < 2 seconds
- [ ] Chat message response < 1 second
- [ ] File upload progress updates smoothly
- [ ] No UI freezing during streaming responses

## Troubleshooting

### Common Issues
- **API Connection Failed**: Ensure backend is running on port 3001
- **Upload Stuck**: Check file size limits and network connection
- **Citations Not Loading**: Verify document processing completed
- **Theme Not Switching**: Clear browser cache and reload

### Debug Mode
Set `NEXT_PUBLIC_DEBUG=true` in environment to enable debug logging.

## Next Steps
- Run automated tests: `npm test`
- Build for production: `npm run build`
- Deploy to hosting platform