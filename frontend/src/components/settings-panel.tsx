'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useSettings } from '@/lib/context/settings-context';
import { getAvailableModels, type AvailableModel } from '@/lib/api/models';

interface SettingsPanelProps {
  onClose?: () => void;
}

function formatModelSize(bytes: number): string {
  if (bytes === 0) return 'Size N/A';
  const gb = bytes / (1024 * 1024 * 1024);
  return gb >= 1 ? `${gb.toFixed(2)} GB` : `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

const SettingsPanel: React.FC<SettingsPanelProps> = ({ onClose }) => {
  const { settings, updateSettings } = useSettings();
  const [localSettings, setLocalSettings] = useState(settings);
  const [availableModels, setAvailableModels] = useState<AvailableModel[]>([]);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const providerType = useMemo(() => {
    const currentModel = availableModels.find((m) => m.name === localSettings.selectedModel);
    return currentModel?.provider === 'ollama' ? 'ollama' : 'cloud';
  }, [localSettings.selectedModel, availableModels]);

  useEffect(() => {
    setLocalSettings(settings);
  }, [settings]);

  useEffect(() => {
    const fetchModels = async () => {
      setModelsLoading(true);
      setError(null);
      try {
        const models = await getAvailableModels();
        if (models && models.length > 0) {
          setAvailableModels(models);
          // If the currently saved model isn't in the available list, select the first available model.
          if (!models.some((m) => m.name === settings.selectedModel)) {
            setLocalSettings((prev) => ({ ...prev, selectedModel: models[0].name }));
          }
        } else {
          setError('No models returned from the backend.');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
        console.error('Failed to fetch models:', err);
      } finally {
        setModelsLoading(false);
      }
    };
    fetchModels();
  }, [settings.selectedModel]);

  const handleProviderChange = (newProvider: 'ollama' | 'cloud') => {
    const newModelList = newProvider === 'ollama' ? ollamaModels : cloudModels;
    if (newModelList.length > 0) {
      setLocalSettings((prev) => ({ ...prev, selectedModel: newModelList[0].name }));
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = type === 'checkbox' ? (e.target as HTMLInputElement).checked : undefined;
    setLocalSettings((prev) => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  };

  const handleSave = () => {
    updateSettings(localSettings);
    onClose?.();
  };

  const ollamaModels = availableModels.filter((m) => m.provider === 'ollama');
  const cloudModels = availableModels.filter(
    (m) => m.provider !== 'ollama' && m.provider !== 'none',
  );

  return (
    <form
      className="space-y-6"
      onSubmit={(e) => {
        e.preventDefault();
        handleSave();
      }}
      onKeyDown={(e) => e.key === 'Escape' && onClose?.()}
    >
      {/* AI Model Selection */}
      <fieldset>
        <legend className="block text-sm font-medium text-foreground mb-2">
          AI Model Configuration
        </legend>
        {error && <p className="text-sm text-destructive">Error: {error}</p>}
        <div className="space-y-2">
          <div className="flex space-x-4">
            <label className="flex items-center">
              <input
                type="radio"
                name="providerType"
                value="ollama"
                checked={providerType === 'ollama'}
                onChange={() => handleProviderChange('ollama')}
                disabled={modelsLoading || ollamaModels.length === 0}
              />
              <span className="ml-2">Local (Ollama)</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                name="providerType"
                value="cloud"
                checked={providerType === 'cloud'}
                onChange={() => handleProviderChange('cloud')}
                disabled={modelsLoading || cloudModels.length === 0}
              />
              <span className="ml-2">Cloud Models</span>
            </label>
          </div>
          <label htmlFor="selectedModel" className="block text-sm font-medium text-foreground">
            AI Model
          </label>
          <select
            id="selectedModel"
            name="selectedModel"
            value={localSettings.selectedModel}
            onChange={handleChange}
            disabled={
              modelsLoading ||
              (providerType === 'ollama' ? ollamaModels.length === 0 : cloudModels.length === 0)
            }
            className="w-full px-3 py-2 border border-input bg-background rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            {modelsLoading ? (
              <option>Loading models...</option>
            ) : (
              (providerType === 'ollama' ? ollamaModels : cloudModels).map((model) => (
                <option key={model.name} value={model.name}>
                  {model.provider === 'ollama'
                    ? `${model.name} (${formatModelSize(model.size)})`
                    : `${model.provider}: ${model.name}`}
                </option>
              ))
            )}
          </select>
        </div>
      </fieldset>

      {/* Appearance Settings */}
      <fieldset>
        <legend className="block text-sm font-medium text-foreground mb-2">Appearance</legend>
        <div className="space-y-2">
          <label htmlFor="theme" className="block text-sm font-medium text-foreground">
            Theme
          </label>
          <div className="flex space-x-4 rounded-md bg-muted p-1">
            {(['light', 'dark', 'system'] as const).map((themeOption) => (
              <label
                key={themeOption}
                className={`relative flex-1 cursor-pointer rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  localSettings.theme === themeOption
                    ? 'bg-background text-foreground shadow-sm'
                    : 'text-muted-foreground hover:bg-background/50'
                }`}
              >
                <input
                  type="radio"
                  name="theme"
                  value={themeOption}
                  checked={localSettings.theme === themeOption}
                  onChange={handleChange}
                  className="sr-only"
                />
                <span className="capitalize">{themeOption}</span>
              </label>
            ))}
          </div>
        </div>
      </fieldset>

      {/* Feature Flags */}
      <fieldset>
        <legend className="block text-sm font-medium text-foreground mb-2">Features</legend>
        <div className="space-y-3">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              name="showSourcesPanel"
              checked={localSettings.showSourcesPanel}
              onChange={handleChange}
            />
            <span className="text-sm">Show Sources panel under assistant messages</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              name="showWebDebugBadges"
              checked={localSettings.showWebDebugBadges}
              onChange={handleChange}
            />
            <span className="text-sm">Show web debug badges (dev-only)</span>
          </label>
        </div>
      </fieldset>

      <div className="flex justify-end space-x-3 pt-4">
        <button
          type="button"
          onClick={onClose}
          className="px-4 py-2 text-sm font-medium text-secondary-foreground bg-secondary rounded-md hover:bg-secondary/80"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 text-sm font-medium text-primary-foreground bg-primary rounded-md hover:bg-primary/90"
        >
          Save Settings
        </button>
      </div>
    </form>
  );
};

export default SettingsPanel;
