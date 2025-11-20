'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useSettings } from '@/lib/context/settings-context';
import { getAvailableModels, type AvailableModel } from '@/lib/api/models';
import { getMcpHealth, initMcpModel } from '@/lib/api/mcp';

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
  const [mcpHealth, setMcpHealth] = useState<any | null>(null);
  const [initInProgress, setInitInProgress] = useState(false);

  const providerType = useMemo(() => {
    const currentModel = availableModels.find(m => m.name === localSettings.selectedModel);
    return currentModel?.provider === 'ollama' ? 'ollama' : 'cloud';
  }, [localSettings.selectedModel, availableModels]);

  useEffect(() => {
    setLocalSettings(settings);
  }, [settings]);

  useEffect(() => {
    const ac = new AbortController();
    let timer: number | undefined;
    let pollTimer: number | undefined;
    const DEBOUNCE_MS = 300;
    const POLL_INTERVAL_MS = 3000;

    const pollHealthUntilModels = async (signal: AbortSignal, maxMs = 30000) => {
      const start = Date.now();
      while (!signal.aborted && Date.now() - start < maxMs) {
        const h = await getMcpHealth(signal);
        setMcpHealth(h);
        if (h.ok && h.ai && (h.ai.available_models || (h.ai.models && h.ai.models.length > 0))) {
          // Models available now — refresh models list
          const models = await getAvailableModels({ signal });
          setAvailableModels(models);
          return;
        }
        // wait
        await new Promise(r => { pollTimer = window.setTimeout(r, POLL_INTERVAL_MS); });
      }
    };

    const fetchModels = async () => {
      setModelsLoading(true);
      setError(null);
      try {
        // If feature flag enabled, check MCP health first
        const useHealth = (process.env.NEXT_PUBLIC_MCP_HEALTH_FLOW || 'true') === 'true';
        if (useHealth) {
          console.debug('SettingsPanel: checking MCP health');
          const t0 = performance.now();
          const h = await getMcpHealth(ac.signal);
          console.debug('SettingsPanel: MCP health completed in', (performance.now() - t0).toFixed(1), 'ms');
          setMcpHealth(h);
          if (h.ok && h.ai && (h.ai.available_models || (h.ai.models && h.ai.models.length > 0))) {
            console.debug('SettingsPanel: models reported available by health; fetching list');
            const t1 = performance.now();
            const models = await getAvailableModels({ signal: ac.signal });
            console.debug('SettingsPanel: model list fetched in', (performance.now() - t1).toFixed(1), 'ms');
            if (models && models.length > 0) {
              setAvailableModels(models);
              if (!models.some(m => m.name === settings.selectedModel)) {
                setLocalSettings(prev => ({ ...prev, selectedModel: models[0].name }));
              }
            } else {
              setError('No models returned from the backend.');
            }
            setModelsLoading(false);
            return;
          }

          // If health says no models (initializing), poll for a short period
          await pollHealthUntilModels(ac.signal, 30000);
        }

        // Fallback: call getAvailableModels directly
        const models = await getAvailableModels({ signal: ac.signal });
        if (models && models.length > 0) {
          setAvailableModels(models);
          if (!models.some(m => m.name === settings.selectedModel)) {
            setLocalSettings(prev => ({ ...prev, selectedModel: models[0].name }));
          }
        } else {
          setError('No models returned from the backend.');
        }
      } catch (err) {
        if ((err as any)?.name === 'AbortError') {
          console.debug('Model fetch aborted');
        } else {
          setError(err instanceof Error ? err.message : 'An unknown error occurred');
          console.error('Failed to fetch models:', err);
        }
      } finally {
        setModelsLoading(false);
      }
    };

    // Debounce initial fetch to avoid rapid open/close causing duplicate work
    timer = window.setTimeout(() => { fetchModels(); }, DEBOUNCE_MS);

    return () => {
      ac.abort();
      if (timer) clearTimeout(timer);
      if (pollTimer) clearTimeout(pollTimer);
    };
  }, []);

  const handleProviderChange = (newProvider: 'ollama' | 'cloud') => {
    const newModelList = newProvider === 'ollama' ? ollamaModels : cloudModels;
    if (newModelList.length > 0) {
      setLocalSettings(prev => ({ ...prev, selectedModel: newModelList[0].name }));
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = type === 'checkbox' ? (e.target as HTMLInputElement).checked : undefined;
    setLocalSettings(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  };

  const handleSave = () => {
    updateSettings(localSettings);
    onClose?.();
  };

  const ollamaModels = availableModels.filter(m => m.provider === 'ollama');
  const cloudModels = availableModels.filter(m => m.provider !== 'ollama' && m.provider !== 'none');

  const handleInitModel = async () => {
    setInitInProgress(true);
    try {
      const resp = await initMcpModel(localSettings.selectedModel);
      if (!resp.ok) {
        setError(resp.error || 'Failed to start model init');
      } else {
        // Kick off a refresh of health and models (non-blocking)
        const h = await getMcpHealth();
        setMcpHealth(h);
        // Try to refresh model list (force)
        const models = await getAvailableModels({ forceRefresh: true });
        setAvailableModels(models);
      }
    } catch (e) {
      setError((e as any)?.message || 'Model init failed');
    } finally {
      setInitInProgress(false);
    }
  };

  const handleRefreshHealth = async () => {
    try {
      const h = await getMcpHealth();
      setMcpHealth(h);
    } catch (e) {
      setError((e as any)?.message || 'Failed to refresh health');
    }
  };

  return (
    <form
      className="space-y-6"
      onSubmit={(e) => { e.preventDefault(); handleSave(); }}
      onKeyDown={(e) => e.key === 'Escape' && onClose?.()}
    >
      {/* AI Model Selection */}
      <fieldset>
        <legend className="block text-sm font-medium text-foreground mb-2">AI Model Configuration</legend>
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
          <label htmlFor="selectedModel" className="block text-sm font-medium text-foreground">AI Model</label>
          <select
            id="selectedModel"
            name="selectedModel"
            value={localSettings.selectedModel}
            onChange={handleChange}
            disabled={modelsLoading || (providerType === 'ollama' ? ollamaModels.length === 0 : cloudModels.length === 0)}
            className="w-full px-3 py-2 border border-input bg-background rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            {modelsLoading ? (
              <option>Loading models...</option>
            ) : (
              (providerType === 'ollama' ? ollamaModels : cloudModels).map(model => (
                <option key={model.name} value={model.name}>
                  {model.provider === 'ollama' ? `${model.name} (${formatModelSize(model.size)})` : `${model.provider}: ${model.name}`}
                </option>
              ))
            )}
          </select>
        </div>
      </fieldset>

      {/* MCP Health / Init status */}
      <div>
        {mcpHealth && !mcpHealth.ok && (
          <div className="text-sm text-warning space-y-2">
            <p>MCP health check failed: {mcpHealth.error || 'unknown'}</p>
            <div className="flex space-x-2">
              <button type="button" onClick={handleRefreshHealth} className="px-3 py-1 text-sm bg-secondary rounded">Retry Health</button>
            </div>
          </div>
        )}

        {mcpHealth && mcpHealth.ok && mcpHealth.ai && (!mcpHealth.ai.available_models || mcpHealth.ai.available_models === 0) && (
          <div className="text-sm text-muted space-y-2">
            <p>Model appears to be initializing or not available yet.</p>
            <div className="flex items-center space-x-2">
              <button type="button" onClick={handleInitModel} disabled={initInProgress} className="px-3 py-1 text-sm bg-primary text-white rounded">
                {initInProgress ? 'Initializing…' : 'Warm Model'}
              </button>
              <button type="button" onClick={handleRefreshHealth} className="px-3 py-1 text-sm bg-secondary rounded">Check Status</button>
            </div>
          </div>
        )}
      </div>

      {/* Other settings fields... */}

      <div className="flex justify-end space-x-3 pt-4">
        <button type="button" onClick={onClose} className="px-4 py-2 text-sm font-medium text-secondary-foreground bg-secondary rounded-md hover:bg-secondary/80">Cancel</button>
        <button type="submit" className="px-4 py-2 text-sm font-medium text-primary-foreground bg-primary rounded-md hover:bg-primary/90">Save Settings</button>
      </div>
    </form>
  );
};

export default SettingsPanel;
