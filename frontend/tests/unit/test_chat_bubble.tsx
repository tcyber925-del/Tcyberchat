import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from '@jest/globals';
import ChatBubble from '../../src/components/chat-bubble';
import { Message } from '../../src/types/message';

const mockMessage: Message = {
  id: '1',
  content: 'Hello, world!',
  timestamp: new Date(),
  type: 'user',
  conversationId: 'conv-1',
};

const mockAIMessage: Message = {
  id: '2',
  content: 'Hi there!',
  timestamp: new Date(),
  type: 'ai',
  conversationId: 'conv-1',
};

describe('ChatBubble Component', () => {
  it('renders user message correctly', () => {
    render(<ChatBubble message={mockMessage} />);
    expect(screen.getByText('Hello, world!')).toBeInTheDocument();
    // User messages should be on the right (justify-end)
    const bubble = screen.getByText('Hello, world!').closest('div');
    expect(bubble).toHaveClass('self-end');
  });

  it('renders AI message correctly', () => {
    render(<ChatBubble message={mockAIMessage} />);
    expect(screen.getByText('Hi there!')).toBeInTheDocument();
    // AI messages should be on the left (justify-start)
    const bubble = screen.getByText('Hi there!').closest('div');
    expect(bubble).toHaveClass('self-start');
  });

  it('renders citations when available', () => {
    const messageWithCitations: Message = {
      ...mockAIMessage,
      citations: [
        { id: 1, docId: 'doc-1', snippet: 'Test snippet' },
        { id: 2, docId: 'doc-2', snippet: 'Another snippet' },
      ],
    };

    render(<ChatBubble message={messageWithCitations} />);
    expect(screen.getByText('[1]')).toBeInTheDocument();
    expect(screen.getByText('[2]')).toBeInTheDocument();
  });

  it('shows copy button for AI messages', () => {
    render(<ChatBubble message={mockAIMessage} />);
    expect(screen.getByTitle('Copy message')).toBeInTheDocument();
  });

  it('does not show interactive buttons for user messages', () => {
    render(<ChatBubble message={mockMessage} />);
    expect(screen.queryByTitle('Copy message')).not.toBeInTheDocument();
  });

  it('shows regenerate button for AI messages', () => {
    render(<ChatBubble message={mockAIMessage} />);
    expect(screen.getByTitle('Regenerate response')).toBeInTheDocument();
  });

  it('handles copy functionality', async () => {
    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: jest.fn(() => Promise.resolve()),
      },
    });

    render(<ChatBubble message={mockAIMessage} />);
    const copyButton = screen.getByTitle('Copy message');

    fireEvent.click(copyButton);

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('Hi there!');
  });
});