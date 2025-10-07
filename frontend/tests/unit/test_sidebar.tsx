import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, jest } from '@jest/globals';
import Sidebar from '../../src/components/sidebar';

// Mock the chat context
jest.mock('@/lib/context/chat-context', () => ({
  useChat: () => ({
    selectSession: jest.fn(),
    selectDocument: jest.fn(),
    documents: [],
    sessions: [],
  }),
}));

describe('Sidebar Component', () => {
  it('renders the sidebar with expected elements', () => {
    render(<Sidebar />);
    expect(screen.getByLabelText('Toggle Sidebar')).toBeInTheDocument();
    expect(screen.getByText('Chat History')).toBeInTheDocument();
    expect(screen.getByText('New Chat')).toBeInTheDocument();
  });

  it('toggles sidebar visibility when toggle button is clicked', async () => {
    render(<Sidebar />);

    const toggleButton = screen.getByLabelText('Toggle Sidebar');
    const sidebar = screen.getByRole('complementary');

    // Initially sidebar should be open
    expect(toggleButton).toHaveAttribute('aria-expanded', 'true');
    expect(sidebar).toHaveAttribute('aria-hidden', 'false');

    // Click to close sidebar
    fireEvent.click(toggleButton);

    await waitFor(() => {
      expect(toggleButton).toHaveAttribute('aria-expanded', 'false');
      expect(sidebar).toHaveAttribute('aria-hidden', 'true');
    });

    // Click to open sidebar again
    fireEvent.click(toggleButton);

    await waitFor(() => {
      expect(toggleButton).toHaveAttribute('aria-expanded', 'true');
      expect(sidebar).toHaveAttribute('aria-hidden', 'false');
    });
  });

  it('uses external toggle state when provided', () => {
    const mockOnToggle = jest.fn();
    const { rerender } = render(<Sidebar isOpen={true} onToggle={mockOnToggle} />);

    const toggleButton = screen.getByLabelText('Toggle Sidebar');

    // Click should call external toggle function
    fireEvent.click(toggleButton);
    expect(mockOnToggle).toHaveBeenCalledTimes(1);

    // Re-render with closed state
    rerender(<Sidebar isOpen={false} onToggle={mockOnToggle} />);

    expect(toggleButton).toHaveAttribute('aria-expanded', 'false');
  });

  it('applies correct CSS classes for open/closed states', async () => {
    render(<Sidebar />);

    const sidebar = screen.getByRole('complementary');

    // Initially open
    expect(sidebar).toHaveClass('translate-x-0');
    expect(sidebar).not.toHaveClass('-translate-x-full');

    // Click to close
    const toggleButton = screen.getByLabelText('Toggle Sidebar');
    fireEvent.click(toggleButton);

    await waitFor(() => {
      expect(sidebar).toHaveClass('-translate-x-full');
      expect(sidebar).not.toHaveClass('translate-x-0');
    });
  });

  it('has proper accessibility attributes', () => {
    render(<Sidebar />);

    const toggleButton = screen.getByLabelText('Toggle Sidebar');
    const sidebar = screen.getByRole('complementary');

    expect(toggleButton).toHaveAttribute('aria-expanded', 'true');
    expect(sidebar).toHaveAttribute('aria-label', 'Chat sidebar');
    expect(sidebar).toHaveAttribute('aria-hidden', 'false');
    expect(sidebar).toHaveAttribute('role', 'complementary');
  });
});
