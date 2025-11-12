import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SettingsPanel from '../../src/components/settings-panel';
import { SettingsProvider, UserSettings } from '../../src/lib/context/settings-context';

// Mock the settings context hook
jest.mock('../../src/lib/context/settings-context', () => ({
  ...jest.requireActual('../../src/lib/context/settings-context'),
  useSettings: jest.fn(),
}));

const mockUseSettings = require('../../src/lib/context/settings-context').useSettings;

describe('SettingsPanel', () => {
  const mockOnClose = jest.fn();

  const defaultSettings: UserSettings = {
    theme: 'light',
    selectedModel: 'llama3.2:1b',
    webSearchEnabled: false,
    multimodalEnabled: true,
    version: 1,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseSettings.mockReturnValue({
      settings: defaultSettings,
      updateSettings: jest.fn(),
      isLoading: false,
    });
  });

  const renderWithProvider = (component: React.ReactElement) => {
    return render(<SettingsProvider>{component}</SettingsProvider>);
  };

  it('renders all settings sections', () => {
    renderWithProvider(<SettingsPanel onClose={mockOnClose} />);

    expect(screen.getByText('AI Model')).toBeInTheDocument();
    expect(screen.getByText('Enable Web Search')).toBeInTheDocument();
    expect(screen.getByText('Enable Multimodal Chat')).toBeInTheDocument();
    expect(screen.getByText('Theme')).toBeInTheDocument();
  });

  it('displays current settings values', () => {
    renderWithProvider(<SettingsPanel onClose={mockOnClose} />);

    const modelSelect = screen.getByDisplayValue('Llama 3.2 1B (Local)');
    expect(modelSelect).toBeInTheDocument();

    const themeSelect = screen.getByDisplayValue('Light');
    expect(themeSelect).toBeInTheDocument();
  });

  it('calls onClose when cancel button is clicked', () => {
    renderWithProvider(<SettingsPanel onClose={mockOnClose} />);

    const cancelButton = screen.getByRole('button', { name: 'Cancel changes and close settings' });
    fireEvent.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('updates model selection', () => {
    const mockUpdateSettings = jest.fn();
    mockUseSettings.mockReturnValue({
      settings: defaultSettings,
      updateSettings: mockUpdateSettings,
      isLoading: false,
    });

    renderWithProvider(<SettingsPanel onClose={mockOnClose} />);

    const modelSelect = screen.getByDisplayValue('Llama 3.2 1B (Local)');
    fireEvent.change(modelSelect, { target: { value: 'gemini-2.0-flash-exp' } });

    expect(mockUpdateSettings).toHaveBeenCalledWith({
      selectedModel: 'gemini-2.0-flash-exp',
    });
  });

  it('toggles web search setting', () => {
    const mockUpdateSettings = jest.fn();
    mockUseSettings.mockReturnValue({
      settings: defaultSettings,
      updateSettings: mockUpdateSettings,
      isLoading: false,
    });

    renderWithProvider(<SettingsPanel onClose={mockOnClose} />);

    const webSearchToggle = screen.getByRole('checkbox', { name: /web search/i });
    fireEvent.click(webSearchToggle);

    expect(mockUpdateSettings).toHaveBeenCalledWith({
      webSearchEnabled: true,
    });
  });

  it('toggles multimodal setting', () => {
    const mockUpdateSettings = jest.fn();
    mockUseSettings.mockReturnValue({
      settings: defaultSettings,
      updateSettings: mockUpdateSettings,
      isLoading: false,
    });

    renderWithProvider(<SettingsPanel onClose={mockOnClose} />);

    const multimodalToggle = screen.getByRole('checkbox', { name: /multimodal/i });
    fireEvent.click(multimodalToggle);

    expect(mockUpdateSettings).toHaveBeenCalledWith({
      multimodalEnabled: false,
    });
  });

  it('updates theme selection', () => {
    const mockUpdateSettings = jest.fn();
    mockUseSettings.mockReturnValue({
      settings: defaultSettings,
      updateSettings: mockUpdateSettings,
      isLoading: false,
    });

    renderWithProvider(<SettingsPanel onClose={mockOnClose} />);

    const themeSelect = screen.getByDisplayValue('light');
    fireEvent.change(themeSelect, { target: { value: 'dark' } });

    expect(mockUpdateSettings).toHaveBeenCalledWith({
      theme: 'dark',
    });
  });

  it('shows loading state', () => {
    mockUseSettings.mockReturnValue({
      settings: defaultSettings,
      updateSettings: jest.fn(),
      isLoading: true,
    });

    renderWithProvider(<SettingsPanel onClose={mockOnClose} />);

    // Check that inputs are disabled during loading
    const modelSelect = screen.getByDisplayValue('llama3.2:1b');
    expect(modelSelect).toBeDisabled();
  });

  it('has proper accessibility attributes', () => {
    renderWithProvider(<SettingsPanel onClose={mockOnClose} />);

    // Check form structure
    const form = screen.getByRole('form', { name: 'Chatbot Settings' });
    expect(form).toBeInTheDocument();

    // Check fieldsets and legends
    expect(screen.getByText('AI Model Configuration')).toBeInTheDocument();
    expect(screen.getByText('Feature Settings')).toBeInTheDocument();
    expect(screen.getByText('Appearance')).toBeInTheDocument();

    // Check form inputs have proper labels
    expect(screen.getByLabelText('AI Model')).toBeInTheDocument();
    expect(screen.getByLabelText('Theme')).toBeInTheDocument();

    // Check checkbox labels are properly associated
    const webSearchCheckbox = screen.getByRole('checkbox', { name: 'Enable Web Search' });
    const multimodalCheckbox = screen.getByRole('checkbox', { name: 'Enable Multimodal Chat' });
    expect(webSearchCheckbox).toBeInTheDocument();
    expect(multimodalCheckbox).toBeInTheDocument();

    // Check ARIA descriptions
    const modelSelect = screen.getByLabelText('AI Model');
    const themeSelect = screen.getByLabelText('Theme');
    expect(modelSelect).toHaveAttribute('aria-describedby', 'selectedModel-description');
    expect(themeSelect).toHaveAttribute('aria-describedby', 'theme-description');

    // Check buttons have proper labels
    expect(
      screen.getByRole('button', { name: 'Cancel changes and close settings' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Save settings and close panel' }),
    ).toBeInTheDocument();
  });

  it('handles keyboard navigation properly', () => {
    renderWithProvider(<SettingsPanel onClose={mockOnClose} />);

    const form = screen.getByRole('form');

    // Test Escape key closes the panel
    fireEvent.keyDown(form, { key: 'Escape' });
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('supports form submission with Enter key', () => {
    const mockUpdateSettings = jest.fn();
    mockUseSettings.mockReturnValue({
      settings: defaultSettings,
      updateSettings: mockUpdateSettings,
      isLoading: false,
    });

    renderWithProvider(<SettingsPanel onClose={mockOnClose} />);

    const form = screen.getByRole('form');

    // Test form submission
    fireEvent.submit(form);
    expect(mockUpdateSettings).toHaveBeenCalledWith(defaultSettings);
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('provides proper focus management', () => {
    renderWithProvider(<SettingsPanel onClose={mockOnClose} />);

    // Check that interactive elements are focusable
    const modelSelect = screen.getByLabelText('AI Model');
    const themeSelect = screen.getByLabelText('Theme');
    const webSearchCheckbox = screen.getByRole('checkbox', { name: 'Enable Web Search' });
    const multimodalCheckbox = screen.getByRole('checkbox', { name: 'Enable Multimodal Chat' });
    const cancelButton = screen.getByRole('button', { name: 'Cancel changes and close settings' });
    const saveButton = screen.getByRole('button', { name: 'Save settings and close panel' });

    // All interactive elements should be in the document and focusable
    expect(modelSelect).toBeInTheDocument();
    expect(themeSelect).toBeInTheDocument();
    expect(webSearchCheckbox).toBeInTheDocument();
    expect(multimodalCheckbox).toBeInTheDocument();
    expect(cancelButton).toBeInTheDocument();
    expect(saveButton).toBeInTheDocument();
  });

  it('announces version information with aria-live', () => {
    renderWithProvider(<SettingsPanel onClose={mockOnClose} />);

    const versionDiv = screen.getByText(`Settings Version: ${defaultSettings.version}`);
    expect(versionDiv).toHaveAttribute('aria-live', 'polite');
  });

  it('groups related controls with fieldsets', () => {
    renderWithProvider(<SettingsPanel onClose={mockOnClose} />);

    // Should have 3 fieldsets
    const fieldsets = screen.getAllByRole('group');
    expect(fieldsets).toHaveLength(4); // 3 fieldsets + 1 button group

    // Check fieldset legends
    expect(screen.getByText('AI Model Configuration')).toBeInTheDocument();
    expect(screen.getByText('Feature Settings')).toBeInTheDocument();
    expect(screen.getByText('Appearance')).toBeInTheDocument();
  });
});
