'use client';

import React, { useState, useEffect } from 'react';
import { useSettings } from '@/lib/context/settings-context';

interface SettingsPanelProps {
  onClose?: () => void;
}

const SettingsPanel: React.FC<SettingsPanelProps> = ({ onClose }) => {
  const { settings, updateSettings } = useSettings();
  const [localSettings, setLocalSettings] = useState(settings);

  // Update local settings when settings change
  useEffect(() => {
    setLocalSettings(settings);
  }, [settings]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;

    setLocalSettings((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSave = () => {
    updateSettings(localSettings);
    onClose?.();
  };

  const handleCancel = () => {
    setLocalSettings(settings); // Reset to original
    onClose?.();
  };

  return (
    <form
      className="space-y-6"
      onSubmit={(e) => {
        e.preventDefault();
        handleSave();
      }}
      onKeyDown={(e) => {
        if (e.key === 'Escape') {
          handleCancel();
        }
      }}
      role="form"
      aria-labelledby="settings-form-title"
    >
      <h2 id="settings-form-title" className="sr-only">Chatbot Settings</h2>

      {/* AI Model Selection */}
      <fieldset>
        <legend className="block text-sm font-medium text-foreground mb-2">
          AI Model Configuration
        </legend>
        <div className="space-y-2">
          <label htmlFor="selectedModel" className="block text-sm font-medium text-foreground">
            AI Model
          </label>
          <select
            id="selectedModel"
            name="selectedModel"
            value={localSettings.selectedModel}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-input bg-background rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring"
            aria-describedby="selectedModel-description"
          >
            <option value="llama3.2:1b">Llama 3.2 1B (Local)</option>
            <option value="llama3.2:3b">Llama 3.2 3B (Local)</option>
            <option value="gemini-2.0-flash-exp">Gemini 2.0 Flash (Cloud)</option>
            <option value="grok-2-1212">Grok 2 (Cloud)</option>
          </select>
          <p id="selectedModel-description" className="text-xs text-muted-foreground">
            Choose the AI model for generating responses
          </p>
        </div>
      </fieldset>

      {/* Feature Toggles */}
      <fieldset>
        <legend className="block text-sm font-medium text-foreground mb-2">
          Feature Settings
        </legend>
        <div className="space-y-4">
          {/* Web Search Toggle */}
          <div>
            <div className="flex items-center">
              <input
                id="webSearchEnabled"
                type="checkbox"
                name="webSearchEnabled"
                checked={localSettings.webSearchEnabled}
                onChange={handleChange}
                className="h-4 w-4 text-primary focus:ring-ring border-input rounded"
                aria-describedby="webSearch-description"
              />
              <label htmlFor="webSearchEnabled" className="ml-2 text-sm text-foreground cursor-pointer">
                Enable Web Search
              </label>
            </div>
            <p id="webSearch-description" className="text-xs text-muted-foreground mt-1 ml-6">
              Allow the AI to search the web for current information using DuckDuckGo
            </p>
          </div>

          {/* Multimodal Chat Toggle */}
          <div>
            <div className="flex items-center">
              <input
                id="multimodalEnabled"
                type="checkbox"
                name="multimodalEnabled"
                checked={localSettings.multimodalEnabled}
                onChange={handleChange}
                className="h-4 w-4 text-primary focus:ring-ring border-input rounded"
                aria-describedby="multimodal-description"
              />
              <label htmlFor="multimodalEnabled" className="ml-2 text-sm text-foreground cursor-pointer">
                Enable Multimodal Chat
              </label>
            </div>
            <p id="multimodal-description" className="text-xs text-muted-foreground mt-1 ml-6">
              Allow voice input and multimodal responses from compatible AI models
            </p>
          </div>
        </div>
      </fieldset>

      {/* Theme Selection */}
      <fieldset>
        <legend className="block text-sm font-medium text-foreground mb-2">
          Appearance
        </legend>
        <div className="space-y-2">
          <label htmlFor="theme" className="block text-sm font-medium text-foreground">
            Theme
          </label>
          <select
            id="theme"
            name="theme"
            value={localSettings.theme}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-input bg-background rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring"
            aria-describedby="theme-description"
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
            <option value="system">System (Auto)</option>
          </select>
          <p id="theme-description" className="text-xs text-muted-foreground">
            Choose the visual theme for the application
          </p>
        </div>
      </fieldset>

      {/* Version Info */}
      <div className="text-xs text-muted-foreground" aria-live="polite">
        Settings Version: {localSettings.version}
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end space-x-3 pt-4" role="group" aria-label="Settings actions">
        <button
          type="button"
          onClick={handleCancel}
          className="px-4 py-2 text-sm font-medium text-secondary-foreground bg-secondary border border-border rounded-md shadow-sm hover:bg-secondary/80 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
          aria-label="Cancel changes and close settings"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 text-sm font-medium text-primary-foreground bg-primary border border-transparent rounded-md shadow-sm hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
          aria-label="Save settings and close panel"
        >
          Save Settings
        </button>
      </div>
    </form>
  );
};

export default SettingsPanel;