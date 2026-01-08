'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useSettings } from '@/lib/context/settings-context';
import { getAvailableModels, type AvailableModel } from '@/lib/api/models';
import { getMcpHealth, initMcpModel } from '@/lib/api/mcp';
import {
  listMcpServers,
  upsertMcpServer,
  disableMcpServer,
  warmConnect,
  fetchDocViaMcp,
  testConnection,
  getServerEnv,
  type McpServer,
  type McpServerUpsert,
} from '@/lib/api/integrations-mcp';
import { KeyValueEditor } from '@/components/ui/KeyValueEditor';
import { ToastProvider, useToast } from '@/components/ui/ToastProvider';
import { cn } from '@/lib/utils';


interface SettingsPanelProps {
  onClose?: () => void;
}

function formatModelSize(bytes: number): string {
  if (bytes === 0) return 'Size N/A';
  const gb = bytes / (1024 * 1024 * 1024);
  return gb >= 1 ? `${gb.toFixed(2)} GB` : `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

const SettingsPanelInner: React.FC<SettingsPanelProps> = ({ onClose }) => {
  const { settings, updateSettings } = useSettings();
  const { showToast } = useToast();
  const [localSettings, setLocalSettings] = useState(settings);
  const [availableModels, setAvailableModels] = useState<AvailableModel[]>([]);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mcpHealth, setMcpHealth] = useState<any | null>(null);
  const [initInProgress, setInitInProgress] = useState(false);

  // MCP state
  const [mcpServers, setMcpServers] = useState<McpServer[]>([]);
  const [mcpLoading, setMcpLoading] = useState(false);
  const [mcpError, setMcpError] = useState<string | null>(null);
  const [newServer, setNewServer] = useState<McpServerUpsert>({ id: '', transport: 'wss', enabled: true, headers: {} });
  const [editing, setEditing] = useState(false);
  const [mcpAdminToken, setMcpAdminToken] = useState<string>('');
  const [testConnLoading, setTestConnLoading] = useState(false);
  const [testFetchUrl, setTestFetchUrl] = useState('');
  const [testFetchServer, setTestFetchServer] = useState<string>('auto');
  const [testFetchTool, setTestFetchTool] = useState<string>('http.get');
  const [testFetchTags, setTestFetchTags] = useState<string>('');
  const [testFetchResult, setTestFetchResult] = useState<{ snippet?: string; error?: string; structuredContent?: any } | null>(null);
  const [testConnLog, setTestConnLog] = useState<string | null>(null);

  const isSettingsDirty = useMemo(
    () => JSON.stringify(localSettings) !== JSON.stringify(settings),
    [localSettings, settings]
  );

  const providerType = useMemo(() => {
    const currentModel = availableModels.find((m) => m.name === localSettings.selectedModel);
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
          if (!models.some((m) => m.name === settings.selectedModel)) {
            setLocalSettings((prev) => ({ ...prev, selectedModel: models[0].name }));
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
    const fetchMcp = async () => {
      setMcpLoading(true);
      setMcpError(null);
      try {
        const data = await listMcpServers();
        setMcpServers(data.servers || []);
      } catch (e: any) {
        setMcpError(e?.message || 'Failed to load MCP servers');
      } finally {
        setMcpLoading(false);
      }
    };
    fetchModels();
    fetchMcp();
  }, [settings.selectedModel]);

  // Poll MCP status periodically
  useEffect(() => {
    const id = setInterval(async () => {
      try {
        const data = await listMcpServers();
        setMcpServers(data.servers || []);
      } catch { }
    }, 15000);
    return () => clearInterval(id);
  }, []);

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
    showToast({ variant: 'success', title: 'Settings saved' });
  };

  const handleCancelChanges = () => {
    setLocalSettings(settings);
    setNewServer({ id: '', transport: 'wss', enabled: true, headers: {} });
    setEditing(false);
    showToast({ variant: 'warning', title: 'Changes discarded' });
  };

  const ollamaModels = availableModels.filter((m) => m.provider === 'ollama');
  const cloudModels = availableModels.filter(
    (m) => m.provider !== 'ollama' && m.provider !== 'none',
  );

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
      onSubmit={(e) => {
        e.preventDefault();
        handleSave();
      }}
      onKeyDown={(e) => e.key === 'Escape' && onClose?.()}
    >
      {/* Enhanced AI Model Selection */}
      <fieldset className="space-y-4">
        <legend className="block text-sm font-medium text-foreground mb-3">
          AI Model Configuration
        </legend>
        {error && <p className="text-sm text-destructive bg-destructive/10 p-2 rounded-md">⚠️ {error}</p>}

        <div className="space-y-3">
          {/* Provider Type Selection with Enhanced UI */}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => handleProviderChange('ollama')}
              disabled={modelsLoading || ollamaModels.length === 0}
              className={cn(
                'flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border-2 transition-all',
                'font-medium text-sm',
                providerType === 'ollama'
                  ? 'border-primary bg-primary/10 text-primary shadow-sm'
                  : 'border-border bg-background hover:bg-accent hover:border-accent-foreground/20',
                (modelsLoading || ollamaModels.length === 0) && 'opacity-50 cursor-not-allowed'
              )}
            >
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z" />
              </svg>
              <span>Local (Ollama)</span>
              {ollamaModels.length > 0 && (
                <span className="ml-auto text-xs bg-background px-2 py-0.5 rounded-full">
                  {ollamaModels.length}
                </span>
              )}
            </button>

            <button
              type="button"
              onClick={() => handleProviderChange('cloud')}
              disabled={modelsLoading || cloudModels.length === 0}
              className={cn(
                'flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border-2 transition-all',
                'font-medium text-sm',
                providerType === 'cloud'
                  ? 'border-primary bg-primary/10 text-primary shadow-sm'
                  : 'border-border bg-background hover:bg-accent hover:border-accent-foreground/20',
                (modelsLoading || cloudModels.length === 0) && 'opacity-50 cursor-not-allowed'
              )}
            >
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z" />
              </svg>
              <span>Cloud Models</span>
              {cloudModels.length > 0 && (
                <span className="ml-auto text-xs bg-background px-2 py-0.5 rounded-full">
                  {cloudModels.length}
                </span>
              )}
            </button>
          </div>

          {/* Enhanced Model Dropdown */}
          <div>
            <label htmlFor="selectedModel" className="block text-sm font-medium text-foreground mb-2">
              Select Model
            </label>
            <div className="relative">
              <select
                id="selectedModel"
                name="selectedModel"
                value={localSettings.selectedModel}
                onChange={handleChange}
                disabled={
                  modelsLoading ||
                  (providerType === 'ollama' ? ollamaModels.length === 0 : cloudModels.length === 0)
                }
                className={cn(
                  'w-full px-4 py-3 pr-10 border-2 border-input bg-background rounded-lg shadow-sm',
                  'text-sm font-medium',
                  'focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent',
                  'transition-all duration-200',
                  'appearance-none cursor-pointer',
                  'hover:border-primary/50',
                )}
              >
                {modelsLoading ? (
                  <option>⏳ Loading models...</option>
                ) : (
                  (providerType === 'ollama' ? ollamaModels : cloudModels).map((model) => {
                    const isReasoning = model.name.includes('reasoning') ||
                      model.name.includes('gpt-oss') ||
                      model.name.includes('o1') ||
                      model.name.includes('o3');
                    const isGroq = model.provider === 'groq';

                    let displayName = '';
                    if (model.provider === 'ollama') {
                      displayName = `${model.name} (${formatModelSize(model.size)})`;
                    } else {
                      const prefix = isGroq ? '⚡ Groq' : model.provider;
                      const suffix = isReasoning ? ' 🧠 Reasoning' : '';
                      displayName = `${prefix}: ${model.name}${suffix}`;
                    }

                    return (
                      <option key={model.name} value={model.name}>
                        {displayName}
                      </option>
                    );
                  })
                )}
              </select>
              {/* Custom dropdown arrow */}
              <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                <svg className="h-5 w-5 text-muted-foreground" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </div>
            </div>

            {/* Model Info Card */}
            {!modelsLoading && (
              <div className="mt-3 p-3 bg-muted/50 rounded-lg border border-border">
                <div className="flex items-start gap-2 text-xs">
                  <svg className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="space-y-1">
                    <p className="text-muted-foreground">
                      {providerType === 'ollama'
                        ? 'Local models run on your machine with full privacy.'
                        : 'Cloud models provide access to the latest AI capabilities.'}
                    </p>
                    {cloudModels.some(m => m.provider === 'groq' && m.name === localSettings.selectedModel) && (
                      <p className="text-violet-600 dark:text-violet-400 font-medium">
                        ⚡ Groq provides ultra-fast inference with LPU technology
                      </p>
                    )}
                    {(localSettings.selectedModel.includes('reasoning') ||
                      localSettings.selectedModel.includes('gpt-oss') ||
                      localSettings.selectedModel.includes('o1') ||
                      localSettings.selectedModel.includes('o3')) && (
                        <p className="text-indigo-600 dark:text-indigo-400 font-medium">
                          🧠 Reasoning model - optimized for complex problem-solving
                        </p>
                      )}
                  </div>
                </div>
              </div>
            )}
          </div>
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
                className={`relative flex-1 cursor-pointer rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${localSettings.theme === themeOption
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

      {/* Enhanced Features Section */}
      <fieldset className="space-y-4">
        <legend className="block text-sm font-medium text-foreground mb-3">Features</legend>
        <div className="space-y-4">
          <label className="flex items-center gap-2 cursor-pointer group">
            <input
              type="checkbox"
              name="showSourcesPanel"
              checked={localSettings.showSourcesPanel}
              onChange={handleChange}
              className="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary"
            />
            <span className="text-sm group-hover:text-foreground transition-colors">
              Show Sources panel under assistant messages
            </span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer group">
            <input
              type="checkbox"
              name="showWebDebugBadges"
              checked={localSettings.showWebDebugBadges}
              onChange={handleChange}
              className="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary"
            />
            <span className="text-sm group-hover:text-foreground transition-colors">
              Show web debug badges (dev-only)
            </span>
          </label>

          {/* Enhanced Deep Research Settings */}
          <div className="p-4 bg-gradient-to-br from-violet-50 to-indigo-50 dark:from-violet-950/20 dark:to-indigo-950/20 rounded-lg border-2 border-violet-200 dark:border-violet-800">
            <div className="flex items-start gap-3 mb-3">
              <div className="p-2 bg-violet-100 dark:bg-violet-900/50 rounded-lg">
                <svg className="h-5 w-5 text-violet-600 dark:text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-violet-900 dark:text-violet-100 mb-1">
                  Deep Research Settings
                </h4>
                <p className="text-xs text-violet-700 dark:text-violet-300">
                  Configure how the AI conducts multi-step research with web search and synthesis
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <label className="text-sm font-medium text-violet-900 dark:text-violet-100 min-w-[140px]" htmlFor="deepResearchDefaultIterations">
                Research Iterations
              </label>
              <div className="flex items-center gap-2 flex-1">
                <input
                  id="deepResearchDefaultIterations"
                  name="deepResearchDefaultIterations"
                  type="range"
                  min={1}
                  max={5}
                  value={localSettings.deepResearchDefaultIterations ?? 2}
                  onChange={handleChange}
                  className="flex-1 h-2 bg-violet-200 dark:bg-violet-800 rounded-lg appearance-none cursor-pointer accent-violet-600"
                />
                <div className="flex items-center justify-center w-12 h-8 bg-violet-600 text-white text-sm font-bold rounded-md">
                  {localSettings.deepResearchDefaultIterations ?? 2}
                </div>
              </div>
            </div>

            <div className="mt-3 p-2 bg-white/50 dark:bg-black/20 rounded border border-violet-200 dark:border-violet-800">
              <p className="text-xs text-violet-700 dark:text-violet-300">
                <strong>Tip:</strong> Higher iterations = more thorough research but slower response.
                {' '}
                {(localSettings.deepResearchDefaultIterations ?? 2) === 1 && 'Quick research (1 iteration)'}
                {(localSettings.deepResearchDefaultIterations ?? 2) === 2 && 'Balanced research (2 iterations) - Recommended'}
                {(localSettings.deepResearchDefaultIterations ?? 2) === 3 && 'Thorough research (3 iterations)'}
                {(localSettings.deepResearchDefaultIterations ?? 2) >= 4 && 'Deep dive research (4+ iterations)'}
              </p>
            </div>
          </div>
        </div>
      </fieldset>


      {/* Integrations: MCP */}
      <fieldset>
        <legend className="block text-sm font-medium text-foreground mb-2">Integrations: MCP</legend>
        {mcpError && <p className="text-sm text-destructive">Error: {mcpError}</p>}
        <div className="mb-2">
          <label className="block text-xs mb-1">Admin token (optional)</label>
          <input
            className="w-full px-2 py-1 border border-input bg-background rounded"
            value={mcpAdminToken}
            onChange={(e) => setMcpAdminToken(e.target.value)}
            placeholder="X-Admin-Token to reveal full env values"
          />
          <p className="text-xs text-muted-foreground mt-1">Provide an admin token to reveal full environment variables when editing a server. Token is sent only to the backend endpoint for verification.</p>
        </div>
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={async () => {
                setMcpLoading(true);
                try {
                  await warmConnect();
                  const data = await listMcpServers();
                  setMcpServers(data.servers || []);
                  showToast({ variant: 'success', title: 'Warm connect completed' });
                } catch (e: any) {
                  setMcpError(e?.message || 'Warm connect failed');
                  showToast({ variant: 'error', title: 'Warm connect failed', description: String(e?.message || '') });
                } finally {
                  setMcpLoading(false);
                }
              }}
              className="px-3 py-1.5 text-sm font-medium bg-primary text-primary-foreground rounded hover:bg-primary/90"
              disabled={mcpLoading}
            >
              {mcpLoading ? 'Connecting…' : 'Warm Connect'}
            </button>
            <div className="flex-1" />
            <button
              type="button"
              onClick={() => {
                const blob = new Blob([JSON.stringify({ servers: mcpServers }, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'mcp-config.json';
                a.click();
                URL.revokeObjectURL(url);
              }}
              className="px-2 py-1 text-xs rounded bg-secondary hover:bg-secondary/80"
            >
              Export Config
            </button>
            <label className="px-2 py-1 text-xs rounded bg-secondary hover:bg-secondary/80 cursor-pointer">
              Import Config
              <input
                type="file"
                className="hidden"
                accept=".json"
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  try {
                    const text = await file.text();
                    const json = JSON.parse(text);
                    if (Array.isArray(json.servers)) {
                      for (const s of json.servers) {
                        await upsertMcpServer(s);
                      }
                      const data = await listMcpServers();
                      setMcpServers(data.servers || []);
                      showToast({ variant: 'success', title: 'Config imported' });
                    } else {
                      throw new Error('Invalid config format');
                    }
                  } catch (err: any) {
                    showToast({ variant: 'error', title: 'Import failed', description: err.message });
                  }
                  e.target.value = '';
                }}
              />
            </label>
          </div>

          {/* Servers list */}
          <div className="border border-input rounded-md p-3">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium">Configured Servers</h4>
              <button
                type="button"
                onClick={async () => {
                  // reload
                  try {
                    const data = await listMcpServers();
                    setMcpServers(data.servers || []);
                  } catch (e: any) {
                    setMcpError(e?.message || 'Failed to load MCP servers');
                  }
                }}
                className="text-xs px-2 py-1 rounded bg-muted hover:bg-muted/80"
              >
                Refresh
              </button>
            </div>
            {mcpServers.length === 0 ? (
              <p className="text-sm text-muted-foreground">No servers configured.</p>
            ) : (
              <ul className="space-y-2">
                {mcpServers.map((s) => (
                  <li key={s.id} className="flex items-center justify-between border border-muted rounded px-2 py-2">
                    <div className="text-sm space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{s.id}</span>
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] bg-muted">
                          {s.transport}
                        </span>
                        {!s.enabled && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] bg-amber-200 text-amber-900">
                            disabled
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] ${s.connected ? 'bg-emerald-200 text-emerald-900' : 'bg-rose-200 text-rose-900'}`}>
                          {s.connected ? 'connected' : 'disconnected'}
                        </span>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] ${s.healthy ? 'bg-emerald-200 text-emerald-900' : 'bg-rose-200 text-rose-900'}`}>
                          {s.healthy ? 'healthy' : 'unhealthy'}
                        </span>
                        {s.tools && s.tools.length > 0 && (
                          <span className="text-xs text-muted-foreground">
                            tools:
                          </span>
                        )}
                        {s.tools && s.tools.slice(0, 6).map((t) => (
                          <span key={t} className="inline-flex items-center px-2 py-0.5 rounded text-[10px] bg-muted">
                            {t}
                          </span>
                        ))}
                        {s.tools && s.tools.length > 6 && (
                          <span className="text-[10px] text-muted-foreground">+{s.tools.length - 6} more</span>
                        )}
                        {s.last_error && (
                          <span className="text-[10px] text-rose-700">error: {s.last_error}</span>
                        )}
                        {(s as any).env_present && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] bg-indigo-100 text-indigo-800">env</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={async () => {
                          try {
                            await warmConnect();
                            const data = await listMcpServers();
                            setMcpServers(data.servers || []);
                            showToast({ variant: 'success', title: `Warm connected: ${s.id}` });
                          } catch (e: any) {
                            showToast({ variant: 'error', title: `Warm connect failed: ${s.id}`, description: String(e?.message || '') });
                          }
                        }}
                        className="text-xs px-2 py-1 rounded bg-muted hover:bg-muted/80"
                      >
                        Warm Connect
                      </button>
                      {!s.enabled ? (
                        <button
                          type="button"
                          onClick={async () => {
                            try {
                              await upsertMcpServer({ id: s.id, transport: s.transport as any, enabled: true });
                              const data = await listMcpServers();
                              setMcpServers(data.servers || []);
                              showToast({ variant: 'success', title: `Enabled ${s.id}` });
                            } catch (e: any) {
                              setMcpError(e?.message || 'Enable failed');
                              showToast({ variant: 'error', title: `Enable failed: ${s.id}` });
                            }
                          }}
                          className="text-xs px-2 py-1 rounded bg-emerald-200 text-emerald-900 hover:bg-emerald-300"
                        >
                          Enable
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={async () => {
                            try {
                              await disableMcpServer(s.id);
                              const data = await listMcpServers();
                              setMcpServers(data.servers || []);
                              showToast({ variant: 'success', title: `Disabled ${s.id}` });
                            } catch (e: any) {
                              setMcpError(e?.message || 'Disable failed');
                              showToast({ variant: 'error', title: `Disable failed: ${s.id}` });
                            }
                          }}
                          className="text-xs px-2 py-1 rounded bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        >
                          Disable
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={async () => {
                          try {
                            // fetch masked or full env if available (pass admin token if provided)
                            let envObj: Record<string, string> | undefined = undefined;
                            try {
                              const envRes = await getServerEnv(s.id, mcpAdminToken || undefined);
                              if (envRes?.ok) {
                                envObj = envRes.env || envRes.env_masked || undefined;
                              }
                            } catch (e) {
                              // ignore env fetch errors
                              envObj = undefined;
                            }
                            setNewServer({ id: s.id, transport: s.transport as any, enabled: s.enabled, tags: s.tags || [], headers: {}, env: envObj });
                            setEditing(true);
                          } catch (err) {
                            setMcpError('Failed to prepare edit');
                          }
                        }}
                        className="text-xs px-2 py-1 rounded bg-secondary hover:bg-secondary/80"
                      >
                        Edit
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Add / Update server */}
          <div className="border border-input rounded-md p-3 space-y-3">
            <h4 className="text-sm font-medium">Add / Update Server</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              <div>
                <label className="block text-xs mb-1">ID</label>
                <input
                  className="w-full px-2 py-1 border border-input bg-background rounded"
                  value={newServer.id}
                  onChange={(e) => setNewServer((p) => ({ ...p, id: e.target.value }))}
                  placeholder="context7"
                />
              </div>
              <div>
                <label className="block text-xs mb-1">Transport</label>
                <select
                  className="w-full px-2 py-1 border border-input bg-background rounded"
                  value={newServer.transport}
                  onChange={(e) => setNewServer((p) => ({ ...p, transport: e.target.value as any }))}
                >
                  <option value="wss">WebSocket (WSS)</option>
                  <option value="sse">SSE (HTTP)</option>
                  <option value="stdio">Stdio (Local)</option>
                </select>
              </div>
              <div>
                <label className="block text-xs mb-1">Enabled</label>
                <select
                  className="w-full px-2 py-1 border border-input bg-background rounded"
                  value={String(newServer.enabled ?? true)}
                  onChange={(e) => setNewServer((p) => ({ ...p, enabled: e.target.value === 'true' }))}
                >
                  <option value="true">true</option>
                  <option value="false">false</option>
                </select>
              </div>
              {newServer.transport === 'wss' || newServer.transport === 'sse' ? (
                <>
                  <div className="md:col-span-2">
                    <label className="block text-xs mb-1">
                      {newServer.transport === 'wss' ? 'WebSocket URL' : 'SSE Endpoint URL'}
                    </label>
                    <input
                      className="w-full px-2 py-1 border border-input bg-background rounded"
                      value={newServer.url || ''}
                      onChange={(e) => { setNewServer((p) => ({ ...p, url: e.target.value })); setEditing(true); }}
                      placeholder={newServer.transport === 'wss' ? "wss://api.example.com/mcp" : "http://localhost:8000/sse"}
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-xs mb-1">Headers</label>
                    <KeyValueEditor
                      value={(newServer.headers as Record<string, string>) || {}}
                      onChange={(next) => {
                        setNewServer((p) => ({ ...p, headers: next }));
                        setEditing(true);
                      }}
                      addLabel="Add header"
                    />
                    <div className="flex gap-2 mt-1">
                      <p className="text-xs text-muted-foreground flex-1">Sent as additional request headers.</p>
                      <select
                        className="text-[10px] px-1 py-0.5 border rounded bg-background"
                        onChange={(e) => {
                          if (!e.target.value) return;
                          setNewServer(p => ({ ...p, headers: { ...(p.headers || {}), [e.target.value]: '' } }));
                          setEditing(true);
                          e.target.value = '';
                        }}
                      >
                        <option value="">+ Preset</option>
                        <option value="Authorization">Authorization</option>
                        <option value="X-API-Key">X-API-Key</option>
                        <option value="User-Agent">User-Agent</option>
                      </select>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <label className="block text-xs mb-1">Command</label>
                    <input
                      className="w-full px-2 py-1 border border-input bg-background rounded"
                      value={newServer.command || ''}
                      onChange={(e) => { setNewServer((p) => ({ ...p, command: e.target.value })); setEditing(true); }}
                      placeholder="node"
                    />
                  </div>
                  <div>
                    <label className="block text-xs mb-1">Args (comma-separated)</label>
                    <input
                      className="w-full px-2 py-1 border border-input bg-background rounded"
                      value={(newServer.args || []).join(',')}
                      onChange={(e) => { setNewServer((p) => ({ ...p, args: (e.target.value || '').split(',').map((s) => s.trim()).filter(Boolean) })); setEditing(true); }}
                      placeholder="/path/to/server.js,--flag"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-xs mb-1">Env (key / value)</label>
                    <KeyValueEditor
                      value={(newServer.env as Record<string, string>) || {}}
                      onChange={(next) => {
                        setNewServer((p) => ({ ...p, env: next }));
                        setEditing(true);
                      }}
                      addLabel="Add env var"
                    />
                    <p className="text-xs text-muted-foreground mt-1">Environment variables passed to stdio servers when started.</p>
                  </div>
                </>
              )}
              <div className="md:col-span-2">
                <label className="block text-xs mb-1">Tags (comma-separated)</label>
                <input
                  className="w-full px-2 py-1 border border-input bg-background rounded"
                  value={(newServer.tags || []).join(',')}
                  onChange={(e) => { setNewServer((p) => ({ ...p, tags: (e.target.value || '').split(',').map((s) => s.trim()).filter(Boolean) })); setEditing(true); }}
                  placeholder="docs,official"
                />
              </div>
              <div>
                <label className="block text-xs mb-1">Connect Timeout (ms)</label>
                <input
                  type="number"
                  className="w-full px-2 py-1 border border-input bg-background rounded"
                  value={newServer.timeouts?.connectMs ?? ''}
                  onChange={(e) => { setNewServer((p) => ({ ...p, timeouts: { ...(p.timeouts || {}), connectMs: e.target.value ? Number(e.target.value) : undefined } })); setEditing(true); }}
                  placeholder="e.g. 5000"
                />
              </div>
              <div>
                <label className="block text-xs mb-1">Read Timeout (ms)</label>
                <input
                  type="number"
                  className="w-full px-2 py-1 border border-input bg-background rounded"
                  value={newServer.timeouts?.readMs ?? ''}
                  onChange={(e) => { setNewServer((p) => ({ ...p, timeouts: { ...(p.timeouts || {}), readMs: e.target.value ? Number(e.target.value) : undefined } })); setEditing(true); }}
                  placeholder="e.g. 15000"
                />
              </div>
            </div>
            <div className="flex items-center gap-2 pt-2">
              <button
                type="button"
                onClick={async () => {
                  setMcpError(null);
                  try {
                    if (!newServer.id) throw new Error('Server id is required');
                    const payload = { ...newServer };
                    await upsertMcpServer(payload);
                    const data = await listMcpServers();
                    setMcpServers(data.servers || []);
                    setEditing(false);
                    showToast({ variant: 'success', title: `Saved ${payload.id}` });
                  } catch (e: any) {
                    setMcpError(e?.message || 'Upsert failed');
                    showToast({ variant: 'error', title: 'Save failed', description: String(e?.message || '') });
                  }
                }}
                className="px-3 py-1.5 text-sm font-medium bg-primary text-primary-foreground rounded hover:bg-primary/90"
              >
                Save Server
              </button>
              <button
                type="button"
                onClick={async () => {
                  setTestConnLoading(true);
                  setTestConnLog(null);
                  try {
                    const res = await testConnection(newServer);
                    if (res.ok) {
                      const toolNames = res.tools?.map((t: any) => t.name).join(', ') || 'none';
                      showToast({ variant: 'success', title: 'Connection Successful', description: `Found tools: ${toolNames}` });
                      if ((res as any).log_tail) {
                          setTestConnLog((res as any).log_tail);
                      }
                    } else {
                      showToast({ variant: 'error', title: 'Connection Failed', description: res.error });
                      const details = [
                          res.error,
                          (res as any).stderr,
                          (res as any).error_trace,
                          (res as any).log_tail
                      ].filter(Boolean).join('\n\n---\n\n');
                      setTestConnLog(details);
                    }
                  } catch (e: any) {
                    showToast({ variant: 'error', title: 'Connection Error', description: e.message });
                    setTestConnLog(e.stack || e.message);
                  } finally {
                    setTestConnLoading(false);
                  }
                }}
                disabled={testConnLoading}
                className="px-3 py-1.5 text-sm font-medium bg-secondary text-secondary-foreground rounded hover:bg-secondary/80"
              >
                {testConnLoading ? 'Testing...' : 'Test Connection'}
              </button>
            </div>
            {testConnLog && (
                <div className="mt-2 p-2 bg-muted/50 rounded text-xs border border-muted">
                    <p className="font-semibold mb-1">Connection Log / Error Details:</p>
                    <pre className="whitespace-pre-wrap overflow-auto max-h-40">{testConnLog}</pre>
                </div>
            )}
          </div>

          {/* Test Fetch via MCP */}
          <div className="border border-input rounded-md p-3 space-y-2">
            <h4 className="text-sm font-medium">Test Fetch via MCP</h4>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
              <div className="md:col-span-2">
                <label className="block text-xs mb-1">URL</label>
                <input
                  className="w-full px-2 py-1 border border-input bg-background rounded"
                  value={testFetchUrl}
                  onChange={(e) => setTestFetchUrl(e.target.value)}
                  placeholder="https://example.com/docs/page"
                />
              </div>
              <div>
                <label className="block text-xs mb-1">Server</label>
                <select
                  className="w-full px-2 py-1 border border-input bg-background rounded"
                  value={testFetchServer}
                  onChange={(e) => setTestFetchServer(e.target.value)}
                >
                  <option value="auto">auto</option>
                  {mcpServers.map((s) => (
                    <option key={s.id} value={s.id}>{s.id}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs mb-1">Tool</label>
                <select
                  className="w-full px-2 py-1 border border-input bg-background rounded"
                  value={testFetchTool}
                  onChange={(e) => setTestFetchTool(e.target.value)}
                >
                  <option value="http.get">http.get</option>
                  <option value="fetch_url">fetch_url</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              <div className="md:col-span-2">
                <label className="block text-xs mb-1">preferredTags (comma-separated)</label>
                <input
                  className="w-full px-2 py-1 border border-input bg-background rounded"
                  value={testFetchTags}
                  onChange={(e) => setTestFetchTags(e.target.value)}
                  placeholder="docs,official"
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={async () => {
                  setTestFetchResult(null);
                  if (!testFetchUrl) {
                    setTestFetchResult({ error: 'URL is required' });
                    return;
                  }
                  try {
                    const preferredTags = (testFetchTags || '')
                      .split(',')
                      .map((s) => s.trim())
                      .filter(Boolean);
                    const res = await fetchDocViaMcp({ url: testFetchUrl, server: testFetchServer || 'auto', tool: testFetchTool, preferredTags });
                    if (res.error) {
                      setTestFetchResult({ error: res.error });
                    } else {
                      setTestFetchResult({
                        snippet: res.citation?.snippet || (res.content ? res.content.slice(0, 200) : ''),
                        structuredContent: res.structuredContent,
                      });
                    }
                  } catch (e: any) {
                    setTestFetchResult({ error: e?.message || 'Test fetch failed' });
                    showToast({ variant: 'error', title: 'Test fetch failed', description: String(e?.message || '') });
                  }
                }}
                className="px-3 py-1.5 text-sm font-medium bg-muted rounded hover:bg-muted/80"
              >
                Run Test Fetch
              </button>
            </div>
            {testFetchResult && (
              <div className="text-sm">
                {testFetchResult.error ? (
                  <p className="text-destructive">Error: {testFetchResult.error}</p>
                ) : (
                  <>
                    <p className="text-muted-foreground">Snippet: {testFetchResult.snippet || '(no preview)'}</p>
                    {testFetchResult.structuredContent && (
                      <div className="mt-2">
                        <label className="block text-xs mb-1">Structured Content</label>
                        <pre className="max-h-60 overflow-auto bg-surface p-2 rounded text-xs">{JSON.stringify(testFetchResult.structuredContent, null, 2)}</pre>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </fieldset>

      <div className="h-10" />
      {/* Sticky dirty-state footer */}
      {
        (isSettingsDirty || editing) && (
          <div className="sticky bottom-0 inset-x-0 bg-background/95 backdrop-blur border-t shadow-sm px-3 py-2 flex items-center gap-2 z-40">
            <div className="text-xs text-muted-foreground flex-1">
              You have unsaved changes{editing ? ' (MCP server form)' : ''}.
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                className="px-2 py-1 text-xs rounded bg-secondary hover:bg-secondary/80"
                onClick={handleCancelChanges}
              >
                Discard Changes
              </button>
              <button
                type="button"
                className="px-2 py-1 text-xs rounded bg-primary text-primary-foreground hover:bg-primary/90"
                onClick={handleSave}
                disabled={!isSettingsDirty}
              >
                Save Settings
              </button>
              {editing && (
                <button
                  type="button"
                  className="px-2 py-1 text-xs rounded bg-primary text-primary-foreground hover:bg-primary/90"
                  onClick={async () => {
                    try {
                      if (!newServer.id) throw new Error('Server id is required');
                      const payload = { ...newServer };
                      await upsertMcpServer(payload);
                      const data = await listMcpServers();
                      setMcpServers(data.servers || []);
                      setEditing(false);
                      showToast({ variant: 'success', title: `Saved ${payload.id}` });
                    } catch (e: any) {
                      setMcpError(e?.message || 'Upsert failed');
                      showToast({ variant: 'error', title: 'Save failed', description: String(e?.message || '') });
                    }
                  }}
                >
                  Save Server
                </button>
              )}
            </div>
          </div>
        )
      }
    </form >
  );
};

const SettingsPanel: React.FC<SettingsPanelProps> = (props) => (
  <ToastProvider>
    <SettingsPanelInner {...props} />
  </ToastProvider>
);

export default SettingsPanel;