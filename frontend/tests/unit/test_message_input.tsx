import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import MessageInput from '../../src/components/message-input';
import { SettingsProvider } from '../../src/lib/context/settings-context';

// Mock the settings hooks
const mockUseSettings = jest.fn();
jest.mock('../../src/lib/hooks/use-settings', () => ({
  useSettings: () => mockUseSettings(),
}));

// Mock File API
global.File = class MockFile {
  constructor(parts, filename, options = {}) {
    this.name = filename;
    this.size = options.size || 0;
    this.type = options.type || '';
    this.lastModified = Date.now();
  }
};

// Mock URL.createObjectURL
global.URL.createObjectURL = jest.fn(() => 'mock-url');
global.URL.revokeObjectURL = jest.fn();

// Mock MediaRecorder
global.MediaRecorder = class MockMediaRecorder {
  static isTypeSupported = jest.fn(() => true);

  constructor(stream) {
    this.stream = stream;
    this.state = 'inactive';
    this.ondataavailable = null;
    this.onstop = null;
  }

  start() {
    this.state = 'recording';
  }

  stop() {
    this.state = 'inactive';
    if (this.ondataavailable) {
      const mockBlob = new Blob(['mock audio data'], { type: 'audio/wav' });
      this.ondataavailable({ data: mockBlob });
    }
    if (this.onstop) {
      this.onstop();
    }
  }
};

// Mock getUserMedia
global.navigator.mediaDevices = {
  getUserMedia: jest.fn(() =>
    Promise.resolve({
      getTracks: () => [{ stop: jest.fn() }]
    })
  )
};

const renderWithProvider = (component, settings = {}) => {
  mockUseSettings.mockReturnValue(settings);
  return render(
    <SettingsProvider>
      {component}
    </SettingsProvider>
  );
};

describe('MessageInput Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders input field and send button', () => {
    renderWithProvider(<MessageInput />);
    expect(screen.getByRole('textbox', { name: /message input/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
  });

  it('allows typing in the input field', () => {
    renderWithProvider(<MessageInput />);
    const input = screen.getByRole('textbox', { name: /message input/i });
    fireEvent.change(input, { target: { value: 'Hello World' } });
    expect(input).toHaveValue('Hello World');
  });

  it('disables send button when input is empty', () => {
    renderWithProvider(<MessageInput />);
    const sendButton = screen.getByRole('button', { name: /send/i });
    expect(sendButton).toBeDisabled();
  });

  it('enables send button when there is input', () => {
    renderWithProvider(<MessageInput />);
    const input = screen.getByRole('textbox', { name: /message input/i });
    const sendButton = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'Test message' } });
    expect(sendButton).not.toBeDisabled();
  });

  describe('Multimodal Features', () => {
    it('shows multimodal buttons when enabled', () => {
      renderWithProvider(<MessageInput />, { multimodalEnabled: true });

      expect(screen.getByRole('button', { name: /record voice/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /attach image/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /attach audio file/i })).toBeInTheDocument();
    });

    it('hides multimodal buttons when disabled', () => {
      renderWithProvider(<MessageInput />, { multimodalEnabled: false });

      expect(screen.queryByRole('button', { name: /record voice/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /attach image/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /attach audio file/i })).not.toBeInTheDocument();
    });

    it('starts voice recording when record button is clicked', async () => {
      renderWithProvider(<MessageInput />, { multimodalEnabled: true });

      const recordButton = screen.getByRole('button', { name: /record voice/i });
      fireEvent.click(recordButton);

      await waitFor(() => {
        expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith({
          audio: { echoCancellation: true, noiseSuppression: true }
        });
      });

      expect(recordButton).toHaveAttribute('aria-pressed', 'true');
    });

    it('stops voice recording when record button is clicked again', async () => {
      renderWithProvider(<MessageInput />, { multimodalEnabled: true });

      const recordButton = screen.getByRole('button', { name: /record voice/i });

      // Start recording
      fireEvent.click(recordButton);
      await waitFor(() => {
        expect(recordButton).toHaveAttribute('aria-pressed', 'true');
      });

      // Stop recording
      fireEvent.click(recordButton);
      await waitFor(() => {
        expect(recordButton).toHaveAttribute('aria-pressed', 'false');
      });
    });

    it('handles image file selection', async () => {
      renderWithProvider(<MessageInput />, { multimodalEnabled: true });

      const imageButton = screen.getByRole('button', { name: /attach image/i });
      const fileInput = imageButton.querySelector('input[type="file"]');

      expect(fileInput).toBeInTheDocument();
      expect(fileInput).toHaveAttribute('accept', 'image/*');

      const testFile = new File(['test'], 'test.png', { type: 'image/png' });
      fireEvent.change(fileInput, { target: { files: [testFile] } });

      await waitFor(() => {
        expect(screen.getByText('test.png')).toBeInTheDocument();
      });
    });

    it('handles audio file selection', async () => {
      renderWithProvider(<MessageInput />, { multimodalEnabled: true });

      const audioButton = screen.getByRole('button', { name: /attach audio file/i });
      const fileInput = audioButton.querySelector('input[type="file"]');

      expect(fileInput).toBeInTheDocument();
      expect(fileInput).toHaveAttribute('accept', 'audio/*');

      const testFile = new File(['test'], 'test.mp3', { type: 'audio/mpeg' });
      fireEvent.change(fileInput, { target: { files: [testFile] } });

      await waitFor(() => {
        expect(screen.getByText('test.mp3')).toBeInTheDocument();
      });
    });

    it('shows recording status with timer', async () => {
      jest.useFakeTimers();

      renderWithProvider(<MessageInput />, { multimodalEnabled: true });

      const recordButton = screen.getByRole('button', { name: /record voice/i });
      fireEvent.click(recordButton);

      await waitFor(() => {
        expect(screen.getByText('Recording... 00:01')).toBeInTheDocument();
      });

      jest.advanceTimersByTime(1000);
      await waitFor(() => {
        expect(screen.getByText('Recording... 00:02')).toBeInTheDocument();
      });

      jest.useRealTimers();
    });

    it('displays attached files with remove buttons', async () => {
      renderWithProvider(<MessageInput />, { multimodalEnabled: true });

      const imageButton = screen.getByRole('button', { name: /attach image/i });
      const fileInput = imageButton.querySelector('input[type="file"]');

      const testFile = new File(['test'], 'test.png', { type: 'image/png' });
      fireEvent.change(fileInput, { target: { files: [testFile] } });

      await waitFor(() => {
        expect(screen.getByText('test.png')).toBeInTheDocument();
      });

      const removeButton = screen.getByRole('button', { name: /remove test\.png/i });
      expect(removeButton).toBeInTheDocument();

      fireEvent.click(removeButton);
      await waitFor(() => {
        expect(screen.queryByText('test.png')).not.toBeInTheDocument();
      });
    });
  });
});