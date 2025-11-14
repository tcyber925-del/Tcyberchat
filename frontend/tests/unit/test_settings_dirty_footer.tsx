import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from '@jest/globals';
import { SettingsProvider } from '../../src/lib/context/settings-context';
import SettingsPanel from '../../src/components/settings-panel';

vi.mock('../../src/lib/api/models', async () => {
  return {
    getAvailableModels: vi.fn(async () => [
      { name: 'llama3.2:1b', provider: 'ollama', size: 1024 * 1024 * 1024 },
      { name: 'openai/gpt-4o-mini', provider: 'openai', size: 0 },
    ]),
  };
});

vi.mock('../../src/lib/api/integrations-mcp', async () => {
  return {
    listMcpServers: vi.fn(async () => ({ servers: [] })),
    upsertMcpServer: vi.fn(async () => ({ ok: true })),
    disableMcpServer: vi.fn(async () => ({ ok: true })),
    warmConnect: vi.fn(async () => ({ ok: true, servers: [] })),
    fetchDocViaMcp: vi.fn(async () => ({ url: 'https://example.com', content: 'hello', citation: { snippet: 'hello' } })),
  };
});

function renderSettings() {
  return render(
    <SettingsProvider>
      <SettingsPanel />
    </SettingsProvider>
  );
}

describe('SettingsPanel dirty-state footer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows sticky footer when settings change and supports discard/save', async () => {
    renderSettings();

    // Wait for models to load and the form to render
    await screen.findByText(/AI Model Configuration/i);

    // Change Deep Research iterations
    const iterInput = screen.getByLabelText(/Deep Research default iterations/i) as HTMLInputElement;
    fireEvent.change(iterInput, { target: { value: '3' } });

    // Sticky footer appears
    await screen.findByText(/You have unsaved changes/i);

    // Discard changes hides footer
    fireEvent.click(screen.getByRole('button', { name: /Discard Changes/i }));
    await waitFor(() => {
      expect(screen.queryByText(/You have unsaved changes/i)).toBeNull();
    });

    // Change again and Save Settings
    fireEvent.change(iterInput, { target: { value: '4' } });
    await screen.findByText(/You have unsaved changes/i);
    fireEvent.click(screen.getByRole('button', { name: /Save Settings/i }));

    await waitFor(() => {
      expect(screen.queryByText(/You have unsaved changes/i)).toBeNull();
    });
  });

  it('shows Save Server button in sticky footer when MCP form is dirty', async () => {
    renderSettings();

    await screen.findByText(/Integrations: MCP/i);

    const idInput = screen.getByLabelText('ID', { selector: 'input' });
    fireEvent.change(idInput, { target: { value: 'context7' } });

    // Save Server button should be visible in sticky footer
    await screen.findByRole('button', { name: /Save Server/i });
  });
});
