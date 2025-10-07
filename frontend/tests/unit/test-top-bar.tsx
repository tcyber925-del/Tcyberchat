import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SettingsProvider } from '../../src/lib/context/settings-context';
import TopBar from '../../src/components/top-bar';

// Mock the data API functions
jest.mock('../../src/lib/api/data', () => ({
  exportData: jest.fn().mockResolvedValue(new Blob(['test data'], { type: 'application/json' })),
  importData: jest.fn().mockResolvedValue(undefined),
}));

// Mock URL.createObjectURL and URL.revokeObjectURL
Object.defineProperty(window.URL, 'createObjectURL', {
  writable: true,
  value: jest.fn(() => 'mock-url'),
});

Object.defineProperty(window.URL, 'revokeObjectURL', {
  writable: true,
  value: jest.fn(),
});

describe('TopBar Component', () => {
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
  });

  it('renders all buttons with proper accessibility', () => {
    render(
      <SettingsProvider>
        <TopBar />
      </SettingsProvider>
    );

    expect(screen.getByRole('button', { name: /export/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /settings/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/import/i)).toBeInTheDocument();
  });

  it('export button triggers download when clicked', async () => {
    // Mock document methods
    const createElementSpy = jest.spyOn(document, 'createElement');
    const appendChildSpy = jest.spyOn(document.body, 'appendChild').mockImplementation(() => {});
    const removeChildSpy = jest.spyOn(document.body, 'removeChild').mockImplementation(() => {});

    const mockAnchor = {
      href: '',
      download: '',
      click: jest.fn(),
    };
    createElementSpy.mockReturnValue(mockAnchor as any);

    render(
      <SettingsProvider>
        <TopBar />
      </SettingsProvider>
    );

    const exportButton = screen.getByRole('button', { name: /export/i });
    fireEvent.click(exportButton);

    await waitFor(() => {
      expect(mockAnchor.href).toBe('mock-url');
      expect(mockAnchor.download).toBe('chat-data.json');
      expect(mockAnchor.click).toHaveBeenCalled();
    });

    // Cleanup
    createElementSpy.mockRestore();
    appendChildSpy.mockRestore();
    removeChildSpy.mockRestore();
  });

  it('settings button is clickable and has proper accessibility attributes', () => {
    render(
      <SettingsProvider>
        <TopBar />
      </SettingsProvider>
    );

    const settingsButton = screen.getByRole('button', { name: /settings/i });
    expect(settingsButton).toHaveAttribute('aria-label', 'Settings');
    expect(settingsButton).toBeEnabled();
  });

  it('settings button opens settings panel when clicked', () => {
    render(
      <SettingsProvider>
        <TopBar />
      </SettingsProvider>
    );

    const settingsButton = screen.getByRole('button', { name: /settings/i });

    // Initially, settings panel should not be visible
    expect(screen.queryByText('Settings Panel')).not.toBeInTheDocument();

    fireEvent.click(settingsButton);

    // After clicking, settings panel should be visible
    expect(screen.getByText('Settings Panel')).toBeInTheDocument();
  });

  it('settings button supports keyboard activation', () => {
    render(
      <SettingsProvider>
        <TopBar />
      </SettingsProvider>
    );

    const settingsButton = screen.getByRole('button', { name: /settings/i });

    // Initially, settings panel should not be visible
    expect(screen.queryByText('Settings Panel')).not.toBeInTheDocument();

    // Press Enter key
    fireEvent.keyDown(settingsButton, { key: 'Enter', code: 'Enter' });
    expect(screen.getByText('Settings Panel')).toBeInTheDocument();

    // Close and try Space key
    fireEvent.keyDown(settingsButton, { key: 'Escape', code: 'Escape' });
    expect(screen.queryByText('Settings Panel')).not.toBeInTheDocument();

    fireEvent.keyDown(settingsButton, { key: ' ', code: 'Space' });
    expect(screen.getByText('Settings Panel')).toBeInTheDocument();
  });

  it('settings panel can be closed with Escape key', () => {
    render(
      <SettingsProvider>
        <TopBar />
      </SettingsProvider>
    );

    const settingsButton = screen.getByRole('button', { name: /settings/i });
    fireEvent.click(settingsButton);

    // Settings panel should be open
    expect(screen.getByText('Settings Panel')).toBeInTheDocument();

    // Press Escape to close
    fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' });

    // Settings panel should be closed
    expect(screen.queryByText('Settings Panel')).not.toBeInTheDocument();
  });

  it('handles import file selection', async () => {
    const mockFile = new File(['test'], 'test.json', { type: 'application/json' });

    render(
      <SettingsProvider>
        <TopBar />
      </SettingsProvider>
    );

    const importInput = screen.getByLabelText(/import/i);
    fireEvent.change(importInput, { target: { files: [mockFile] } });

    await waitFor(() => {
      expect(require('../../src/lib/api/data').importData).toHaveBeenCalledWith(mockFile);
    });
  });

  it('handles export errors gracefully', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    const { exportData } = require('../../src/lib/api/data');
    exportData.mockRejectedValue(new Error('Export failed'));

    render(
      <SettingsProvider>
        <TopBar />
      </SettingsProvider>
    );

    const exportButton = screen.getByRole('button', { name: /export/i });
    fireEvent.click(exportButton);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Export failed:', expect.any(Error));
    });

    consoleSpy.mockRestore();
  });

  it('handles import errors gracefully', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    const { importData } = require('../../src/lib/api/data');
    importData.mockRejectedValue(new Error('Import failed'));

    const mockFile = new File(['test'], 'test.json', { type: 'application/json' });

    render(
      <SettingsProvider>
        <TopBar />
      </SettingsProvider>
    );

    const importInput = screen.getByLabelText(/import/i);
    fireEvent.change(importInput, { target: { files: [mockFile] } });

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Import failed:', expect.any(Error));
    });

    consoleSpy.mockRestore();
  });
});</content>
<content lines="1-200">
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SettingsProvider } from '../../src/lib/context/settings-context';
import TopBar from '../../src/components/top-bar';

// Mock the data API functions
jest.mock('../../src/lib/api/data', () => ({
  exportData: jest.fn().mockResolvedValue(new Blob(['test data'], { type: 'application/json' })),
  importData: jest.fn().mockResolvedValue(undefined),
}));

// Mock URL.createObjectURL and URL.revokeObjectURL
Object.defineProperty(window.URL, 'createObjectURL', {
  writable: true,
  value: jest.fn(() => 'mock-url'),
});

Object.defineProperty(window.URL, 'revokeObjectURL', {
  writable: true,
  value: jest.fn(),
});

describe('TopBar Component', () => {
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
  });

  it('renders all buttons with proper accessibility', () => {
    render(
      <SettingsProvider>
        <TopBar />
      </SettingsProvider>
    );

    expect(screen.getByRole('button', { name: /export/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /settings/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/import/i)).toBeInTheDocument();
  });

  it('export button triggers download when clicked', async () => {
    // Mock document methods
    const createElementSpy = jest.spyOn(document, 'createElement');
    const appendChildSpy = jest.spyOn(document.body, 'appendChild').mockImplementation(() => {});
    const removeChildSpy = jest.spyOn(document.body, 'removeChild').mockImplementation(() => {});

    const mockAnchor = {
      href: '',
      download: '',
      click: jest.fn(),
    };
    createElementSpy.mockReturnValue(mockAnchor as any);

    render(
      <SettingsProvider>
        <TopBar />
      </SettingsProvider>
    );

    const exportButton = screen.getByRole('button', { name: /export/i });
    fireEvent.click(exportButton);

    await waitFor(() => {
      expect(mockAnchor.href).toBe('mock-url');
      expect(mockAnchor.download).toBe('chat-data.json');
      expect(mockAnchor.click).toHaveBeenCalled();
    });

    // Cleanup
    createElementSpy.mockRestore();
    appendChildSpy.mockRestore();
    removeChildSpy.mockRestore();
  });

  it('settings button is clickable and has proper accessibility attributes', () => {
    render(
      <SettingsProvider>
        <TopBar />
      </SettingsProvider>
    );

    const settingsButton = screen.getByRole('button', { name: /settings/i });
    expect(settingsButton).toHaveAttribute('aria-label', 'Settings');
    expect(settingsButton).toBeEnabled();
  });

  it('settings button opens settings panel when clicked', () => {
    render(
      <SettingsProvider>
        <TopBar />
      </SettingsProvider>
    );

    const settingsButton = screen.getByRole('button', { name: /settings/i });

    // Initially, settings panel should not be visible
    expect(screen.queryByText('Settings Panel')).not.toBeInTheDocument();

    fireEvent.click(settingsButton);

    // After clicking, settings panel should be visible
    expect(screen.getByText('Settings Panel')).toBeInTheDocument();
  });

  it('settings button supports keyboard activation', () => {
    render(
      <SettingsProvider>
        <TopBar />
      </SettingsProvider>
    );

    const settingsButton = screen.getByRole('button', { name: /settings/i });

    // Initially, settings panel should not be visible
    expect(screen.queryByText('Settings Panel')).not.toBeInTheDocument();

    // Press Enter key
    fireEvent.keyDown(settingsButton, { key: 'Enter', code: 'Enter' });
    expect(screen.getByText('Settings Panel')).toBeInTheDocument();

    // Close and try Space key
    fireEvent.keyDown(settingsButton, { key: 'Escape', code: 'Escape' });
    expect(screen.queryByText('Settings Panel')).not.toBeInTheDocument();

    fireEvent.keyDown(settingsButton, { key: ' ', code: 'Space' });
    expect(screen.getByText('Settings Panel')).toBeInTheDocument();
  });

  it('settings panel can be closed with Escape key', () => {
    render(
      <SettingsProvider>
        <TopBar />
      </SettingsProvider>
    );

    const settingsButton = screen.getByRole('button', { name: /settings/i });
    fireEvent.click(settingsButton);

    // Settings panel should be open
    expect(screen.getByText('Settings Panel')).toBeInTheDocument();

    // Press Escape to close
    fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' });

    // Settings panel should be closed
    expect(screen.queryByText('Settings Panel')).not.toBeInTheDocument();
  });

  it('handles import file selection', async () => {
    const mockFile = new File(['test'], 'test.json', { type: 'application/json' });

    render(
      <SettingsProvider>
        <TopBar />
      </SettingsProvider>
    );

    const importInput = screen.getByLabelText(/import/i);
    fireEvent.change(importInput, { target: { files: [mockFile] } });

    await waitFor(() => {
      expect(require('../../src/lib/api/data').importData).toHaveBeenCalledWith(mockFile);
    });
  });

  it('handles export errors gracefully', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    const { exportData } = require('../../src/lib/api/data');
    exportData.mockRejectedValue(new Error('Export failed'));

    render(
      <SettingsProvider>
        <TopBar />
      </SettingsProvider>
    );

    const exportButton = screen.getByRole('button', { name: /export/i });
    fireEvent.click(exportButton);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Export failed:', expect.any(Error));
    });

    consoleSpy.mockRestore();
  });

  it('handles import errors gracefully', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    const { importData } = require('../../src/lib/api/data');
    importData.mockRejectedValue(new Error('Import failed'));

    const mockFile = new File(['test'], 'test.json', { type: 'application/json' });

    render(
      <SettingsProvider>
        <TopBar />
      </SettingsProvider>
    );

    const importInput = screen.getByLabelText(/import/i);
    fireEvent.change(importInput, { target: { files: [mockFile] } });

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Import failed:', expect.any(Error));
    });

    consoleSpy.mockRestore();
  });
});
</content>