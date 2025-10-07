import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { SettingsProvider, useSettings, DEFAULT_SETTINGS } from '../../src/lib/context/settings-context';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Test component that uses the settings context
const TestComponent: React.FC = () => {
  const { settings, updateSettings, resetSettings, isLoading } = useSettings();

  if (isLoading) {
    return <div data-testid="loading">Loading...</div>;
  }

  return (
    <div>
      <div data-testid="selected-model">{settings.selectedModel}</div>
      <div data-testid="theme">{settings.theme}</div>
      <div data-testid="web-search-enabled">{settings.webSearchEnabled.toString()}</div>
      <div data-testid="multimodal-enabled">{settings.multimodalEnabled.toString()}</div>
      <div data-testid="version">{settings.version}</div>
      <button
        data-testid="update-model"
        onClick={() => updateSettings({ selectedModel: 'llama3.2:3b' })}
      >
        Update Model
      </button>
      <button
        data-testid="update-theme"
        onClick={() => updateSettings({ theme: 'dark' })}
      >
        Update Theme
      </button>
      <button
        data-testid="reset-settings"
        onClick={resetSettings}
      >
        Reset Settings
      </button>
    </div>
  );
};

describe('Settings Context', () => {
  beforeEach(() => {
    localStorageMock.clear();
  });

  it('should provide default settings when no stored settings exist', async () => {
    render(
      <SettingsProvider>
        <TestComponent />
      </SettingsProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('selected-model')).toHaveTextContent(DEFAULT_SETTINGS.selectedModel);
      expect(screen.getByTestId('theme')).toHaveTextContent(DEFAULT_SETTINGS.theme);
      expect(screen.getByTestId('web-search-enabled')).toHaveTextContent(DEFAULT_SETTINGS.webSearchEnabled.toString());
      expect(screen.getByTestId('multimodal-enabled')).toHaveTextContent(DEFAULT_SETTINGS.multimodalEnabled.toString());
      expect(screen.getByTestId('version')).toHaveTextContent(DEFAULT_SETTINGS.version.toString());
    });
  });

  it('should load settings from localStorage on mount', async () => {
    const storedSettings = {
      selectedModel: 'custom-model',
      theme: 'dark' as const,
      webSearchEnabled: false,
      multimodalEnabled: false,
      version: 1,
    };
    localStorageMock.setItem('tcyber-chatbot-settings', JSON.stringify(storedSettings));

    render(
      <SettingsProvider>
        <TestComponent />
      </SettingsProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('selected-model')).toHaveTextContent('custom-model');
      expect(screen.getByTestId('theme')).toHaveTextContent('dark');
      expect(screen.getByTestId('web-search-enabled')).toHaveTextContent('false');
      expect(screen.getByTestId('multimodal-enabled')).toHaveTextContent('false');
    });
  });

  it('should migrate settings with missing fields', async () => {
    const partialSettings = {
      selectedModel: 'partial-model',
      // Missing other fields
    };
    localStorageMock.setItem('tcyber-chatbot-settings', JSON.stringify(partialSettings));

    render(
      <SettingsProvider>
        <TestComponent />
      </SettingsProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('selected-model')).toHaveTextContent('partial-model');
      expect(screen.getByTestId('theme')).toHaveTextContent(DEFAULT_SETTINGS.theme);
      expect(screen.getByTestId('web-search-enabled')).toHaveTextContent(DEFAULT_SETTINGS.webSearchEnabled.toString());
    });
  });

  it('should update settings and persist to localStorage', async () => {
    render(
      <SettingsProvider>
        <TestComponent />
      </SettingsProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('selected-model')).toHaveTextContent(DEFAULT_SETTINGS.selectedModel);
    });

    // Update model
    screen.getByTestId('update-model').click();

    await waitFor(() => {
      expect(screen.getByTestId('selected-model')).toHaveTextContent('llama3.2:3b');
    });

    // Check localStorage
    const stored = localStorageMock.getItem('tcyber-chatbot-settings');
    expect(stored).toBeTruthy();
    const parsed = JSON.parse(stored!);
    expect(parsed.selectedModel).toBe('llama3.2:3b');
  });

  it('should reset settings to defaults', async () => {
    // Set some custom settings first
    render(
      <SettingsProvider>
        <TestComponent />
      </SettingsProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('selected-model')).toHaveTextContent(DEFAULT_SETTINGS.selectedModel);
    });

    // Update theme
    screen.getByTestId('update-theme').click();

    await waitFor(() => {
      expect(screen.getByTestId('theme')).toHaveTextContent('dark');
    });

    // Reset settings
    screen.getByTestId('reset-settings').click();

    await waitFor(() => {
      expect(screen.getByTestId('theme')).toHaveTextContent(DEFAULT_SETTINGS.theme);
      expect(screen.getByTestId('selected-model')).toHaveTextContent(DEFAULT_SETTINGS.selectedModel);
    });
  });

  it('should handle localStorage errors gracefully', async () => {
    // Mock localStorage to throw an error
    const originalGetItem = localStorageMock.getItem;
    localStorageMock.getItem = () => {
      throw new Error('localStorage error');
    };

    render(
      <SettingsProvider>
        <TestComponent />
      </SettingsProvider>
    );

    await waitFor(() => {
      // Should still load with defaults despite the error
      expect(screen.getByTestId('selected-model')).toHaveTextContent(DEFAULT_SETTINGS.selectedModel);
    });

    // Restore original function
    localStorageMock.getItem = originalGetItem;
  });

  it('should handle invalid JSON in localStorage', async () => {
    localStorageMock.setItem('tcyber-chatbot-settings', 'invalid json');

    render(
      <SettingsProvider>
        <TestComponent />
      </SettingsProvider>
    );

    await waitFor(() => {
      // Should fall back to defaults
      expect(screen.getByTestId('selected-model')).toHaveTextContent(DEFAULT_SETTINGS.selectedModel);
    });
  });

  it('should throw error when useSettings is used outside provider', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(<TestComponent />);
    }).toThrow('useSettings must be used within a SettingsProvider');

    consoleSpy.mockRestore();
  });
});</content>
<content lines="1-200">
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { SettingsProvider, useSettings, DEFAULT_SETTINGS } from '../../src/lib/context/settings-context';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Test component that uses the settings context
const TestComponent: React.FC = () => {
  const { settings, updateSettings, resetSettings, isLoading } = useSettings();

  if (isLoading) {
    return <div data-testid="loading">Loading...</div>;
  }

  return (
    <div>
      <div data-testid="selected-model">{settings.selectedModel}</div>
      <div data-testid="theme">{settings.theme}</div>
      <div data-testid="web-search-enabled">{settings.webSearchEnabled.toString()}</div>
      <div data-testid="multimodal-enabled">{settings.multimodalEnabled.toString()}</div>
      <div data-testid="version">{settings.version}</div>
      <button
        data-testid="update-model"
        onClick={() => updateSettings({ selectedModel: 'llama3.2:3b' })}
      >
        Update Model
      </button>
      <button
        data-testid="update-theme"
        onClick={() => updateSettings({ theme: 'dark' })}
      >
        Update Theme
      </button>
      <button
        data-testid="reset-settings"
        onClick={resetSettings}
      >
        Reset Settings
      </button>
    </div>
  );
};

describe('Settings Context', () => {
  beforeEach(() => {
    localStorageMock.clear();
  });

  it('should provide default settings when no stored settings exist', async () => {
    render(
      <SettingsProvider>
        <TestComponent />
      </SettingsProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('selected-model')).toHaveTextContent(DEFAULT_SETTINGS.selectedModel);
      expect(screen.getByTestId('theme')).toHaveTextContent(DEFAULT_SETTINGS.theme);
      expect(screen.getByTestId('web-search-enabled')).toHaveTextContent(DEFAULT_SETTINGS.webSearchEnabled.toString());
      expect(screen.getByTestId('multimodal-enabled')).toHaveTextContent(DEFAULT_SETTINGS.multimodalEnabled.toString());
      expect(screen.getByTestId('version')).toHaveTextContent(DEFAULT_SETTINGS.version.toString());
    });
  });

  it('should load settings from localStorage on mount', async () => {
    const storedSettings = {
      selectedModel: 'custom-model',
      theme: 'dark' as const,
      webSearchEnabled: false,
      multimodalEnabled: false,
      version: 1,
    };
    localStorageMock.setItem('tcyber-chatbot-settings', JSON.stringify(storedSettings));

    render(
      <SettingsProvider>
        <TestComponent />
      </SettingsProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('selected-model')).toHaveTextContent('custom-model');
      expect(screen.getByTestId('theme')).toHaveTextContent('dark');
      expect(screen.getByTestId('web-search-enabled')).toHaveTextContent('false');
      expect(screen.getByTestId('multimodal-enabled')).toHaveTextContent('false');
    });
  });

  it('should migrate settings with missing fields', async () => {
    const partialSettings = {
      selectedModel: 'partial-model',
      // Missing other fields
    };
    localStorageMock.setItem('tcyber-chatbot-settings', JSON.stringify(partialSettings));

    render(
      <SettingsProvider>
        <TestComponent />
      </SettingsProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('selected-model')).toHaveTextContent('partial-model');
      expect(screen.getByTestId('theme')).toHaveTextContent(DEFAULT_SETTINGS.theme);
      expect(screen.getByTestId('web-search-enabled')).toHaveTextContent(DEFAULT_SETTINGS.webSearchEnabled.toString());
    });
  });

  it('should update settings and persist to localStorage', async () => {
    render(
      <SettingsProvider>
        <TestComponent />
      </SettingsProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('selected-model')).toHaveTextContent(DEFAULT_SETTINGS.selectedModel);
    });

    // Update model
    screen.getByTestId('update-model').click();

    await waitFor(() => {
      expect(screen.getByTestId('selected-model')).toHaveTextContent('llama3.2:3b');
    });

    // Check localStorage
    const stored = localStorageMock.getItem('tcyber-chatbot-settings');
    expect(stored).toBeTruthy();
    const parsed = JSON.parse(stored!);
    expect(parsed.selectedModel).toBe('llama3.2:3b');
  });

  it('should reset settings to defaults', async () => {
    // Set some custom settings first
    render(
      <SettingsProvider>
        <TestComponent />
      </SettingsProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('selected-model')).toHaveTextContent(DEFAULT_SETTINGS.selectedModel);
    });

    // Update theme
    screen.getByTestId('update-theme').click();

    await waitFor(() => {
      expect(screen.getByTestId('theme')).toHaveTextContent('dark');
    });

    // Reset settings
    screen.getByTestId('reset-settings').click();

    await waitFor(() => {
      expect(screen.getByTestId('theme')).toHaveTextContent(DEFAULT_SETTINGS.theme);
      expect(screen.getByTestId('selected-model')).toHaveTextContent(DEFAULT_SETTINGS.selectedModel);
    });
  });

  it('should handle localStorage errors gracefully', async () => {
    // Mock localStorage to throw an error
    const originalGetItem = localStorageMock.getItem;
    localStorageMock.getItem = () => {
      throw new Error('localStorage error');
    };

    render(
      <SettingsProvider>
        <TestComponent />
      </SettingsProvider>
    );

    await waitFor(() => {
      // Should still load with defaults despite the error
      expect(screen.getByTestId('selected-model')).toHaveTextContent(DEFAULT_SETTINGS.selectedModel);
    });

    // Restore original function
    localStorageMock.getItem = originalGetItem;
  });

  it('should handle invalid JSON in localStorage', async () => {
    localStorageMock.setItem('tcyber-chatbot-settings', 'invalid json');

    render(
      <SettingsProvider>
        <TestComponent />
      </SettingsProvider>
    );

    await waitFor(() => {
      // Should fall back to defaults
      expect(screen.getByTestId('selected-model')).toHaveTextContent(DEFAULT_SETTINGS.selectedModel);
    });
  });

  it('should throw error when useSettings is used outside provider', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(<TestComponent />);
    }).toThrow('useSettings must be used within a SettingsProvider');

    consoleSpy.mockRestore();
  });
});
</content>