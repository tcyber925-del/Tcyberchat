'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useSettings } from '@/lib/context/settings-context';
import { getAvailableModels, type AvailableModel } from '@/lib/api/models';
<<<<<<< HEAD
import { getMcpHealth, initMcpModel } from '@/lib/api/mcp';
=======
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
>>>>>>> aa2c529f261fabe2c2e39c5042ca04341943e25f

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
<<<<<<< HEAD
          if (!models.some(m => m.name === settings.selectedModel)) {
            setLocalSettings(prev => ({ ...prev, selectedModel: models[0].name }));
=======
          if (!models.some((m) => m.name === settings.selectedModel)) {
            setLocalSettings((prev) => ({ ...prev, selectedModel: models[0].name }));
>>>>>>> aa2c529f261fabe2c2e39c5042ca04341943e25f
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
<<<<<<< HEAD

    // Debounce initial fetch to avoid rapid open/close causing duplicate work
    timer = window.setTimeout(() => { fetchModels(); }, DEBOUNCE_MS);

    return () => {
      ac.abort();
      if (timer) clearTimeout(timer);
      if (pollTimer) clearTimeout(pollTimer);
    };
  }, []);
=======
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
>>>>>>> aa2c529f261fabe2c2e39c5042ca04341943e25f

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

<<<<<<< HEAD
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
=======
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
>>>>>>> aa2c529f261fabe2c2e39c5042ca04341943e25f

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
          <div className="flex items-center gap-2">
            <label className="text-sm w-56" htmlFor="deepResearchDefaultIterations">
              Deep Research default iterations
            </label>
            <input
              id="deepResearchDefaultIterations"
              name="deepResearchDefaultIterations"
              type="number"
              min={1}
              max={5}
              value={localSettings.deepResearchDefaultIterations ?? 2}
              onChange={handleChange}
              className="w-20 px-2 py-1 border border-input bg-background rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
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
                        {s.env_present && (
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
                  try {
                    const res = await testConnection(newServer);
                    if (res.ok) {
                      const toolNames = res.tools?.map((t: any) => t.name).join(', ') || 'none';
                      showToast({ variant: 'success', title: 'Connection Successful', description: `Found tools: ${toolNames}` });
                    } else {
                      showToast({ variant: 'error', title: 'Connection Failed', description: res.error });
                    }
                  } catch (e: any) {
                    showToast({ variant: 'error', title: 'Connection Error', description: e.message });
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
