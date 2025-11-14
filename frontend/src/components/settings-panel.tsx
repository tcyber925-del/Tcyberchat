'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useSettings } from '@/lib/context/settings-context';
import { getAvailableModels, type AvailableModel } from '@/lib/api/models';
import {
  listMcpServers,
  upsertMcpServer,
  disableMcpServer,
  warmConnect,
  fetchDocViaMcp,
  type McpServer,
  type McpServerUpsert,
} from '@/lib/api/integrations-mcp';

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

  // MCP state
  const [mcpServers, setMcpServers] = useState<McpServer[]>([]);
  const [mcpLoading, setMcpLoading] = useState(false);
  const [mcpError, setMcpError] = useState<string | null>(null);
  const [newServer, setNewServer] = useState<McpServerUpsert>({ id: '', transport: 'wss', enabled: true });
  const [testFetchUrl, setTestFetchUrl] = useState('');
  const [testFetchServer, setTestFetchServer] = useState<string>('auto');
  const [testFetchTool, setTestFetchTool] = useState<string>('http.get');
  const [testFetchTags, setTestFetchTags] = useState<string>('');
  const [testFetchResult, setTestFetchResult] = useState<{ snippet?: string; error?: string } | null>(null);

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
                } catch (e: any) {
                  setMcpError(e?.message || 'Warm connect failed');
                } finally {
                  setMcpLoading(false);
                }
              }}
              className="px-3 py-1.5 text-sm font-medium bg-primary text-primary-foreground rounded hover:bg-primary/90"
              disabled={mcpLoading}
            >
              {mcpLoading ? 'Connecting…' : 'Warm Connect'}
            </button>
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
                  <li key={s.id} className="flex items-center justify-between border border-muted rounded px-2 py-1">
                    <div className="text-sm">
                      <div>
                        <span className="font-medium">{s.id}</span> — {s.transport}
                        {s.enabled ? '' : ' (disabled)'}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {s.connected ? 'connected' : 'disconnected'} • {s.healthy ? 'healthy' : 'unhealthy'}
                        {s.tools && s.tools.length > 0 ? ` • tools: ${s.tools.join(', ')}` : ''}
                        {s.last_error ? ` • error: ${s.last_error}` : ''}
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={async () => {
                        try {
                          await disableMcpServer(s.id);
                          const data = await listMcpServers();
                          setMcpServers(data.servers || []);
                        } catch (e: any) {
                          setMcpError(e?.message || 'Disable failed');
                        }
                      }}
                      className="text-xs px-2 py-1 rounded bg-destructive text-destructive-foreground hover:bg-destructive/90"
                    >
                      Disable
                    </button>
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
                  <option value="wss">wss</option>
                  <option value="stdio">stdio</option>
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
              {newServer.transport === 'wss' ? (
                <>
                  <div className="md:col-span-2">
                    <label className="block text-xs mb-1">WSS URL</label>
                    <input
                      className="w-full px-2 py-1 border border-input bg-background rounded"
                      value={newServer.url || ''}
                      onChange={(e) => setNewServer((p) => ({ ...p, url: e.target.value }))}
                      placeholder="wss://..."
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-xs mb-1">Headers (JSON object)</label>
                    <input
                      className="w-full px-2 py-1 border border-input bg-background rounded font-mono"
                      value={JSON.stringify(newServer.headers || {})}
                      onChange={(e) => {
                        try {
                          const val = JSON.parse(e.target.value || '{}');
                          setNewServer((p) => ({ ...p, headers: val }));
                        } catch {
                          // ignore JSON parse errors in UI
                        }
                      }}
                      placeholder='{"Authorization":"Bearer ..."}'
                    />
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <label className="block text-xs mb-1">Command</label>
                    <input
                      className="w-full px-2 py-1 border border-input bg-background rounded"
                      value={newServer.command || ''}
                      onChange={(e) => setNewServer((p) => ({ ...p, command: e.target.value }))}
                      placeholder="node"
                    />
                  </div>
                  <div>
                    <label className="block text-xs mb-1">Args (comma-separated)</label>
                    <input
                      className="w-full px-2 py-1 border border-input bg-background rounded"
                      value={(newServer.args || []).join(',')}
                      onChange={(e) => setNewServer((p) => ({ ...p, args: (e.target.value || '').split(',').map((s) => s.trim()).filter(Boolean) }))}
                      placeholder="/path/to/server.js,--flag"
                    />
                  </div>
                </>
              )}
              <div className="md:col-span-2">
                <label className="block text-xs mb-1">Tags (comma-separated)</label>
                <input
                  className="w-full px-2 py-1 border border-input bg-background rounded"
                  value={(newServer.tags || []).join(',')}
                  onChange={(e) => setNewServer((p) => ({ ...p, tags: (e.target.value || '').split(',').map((s) => s.trim()).filter(Boolean) }))}
                  placeholder="docs,official"
                />
              </div>
              <div>
                <label className="block text-xs mb-1">Connect Timeout (ms)</label>
                <input
                  type="number"
                  className="w-full px-2 py-1 border border-input bg-background rounded"
                  value={newServer.timeouts?.connectMs ?? ''}
                  onChange={(e) => setNewServer((p) => ({ ...p, timeouts: { ...(p.timeouts || {}), connectMs: e.target.value ? Number(e.target.value) : undefined } }))}
                  placeholder="e.g. 5000"
                />
              </div>
              <div>
                <label className="block text-xs mb-1">Read Timeout (ms)</label>
                <input
                  type="number"
                  className="w-full px-2 py-1 border border-input bg-background rounded"
                  value={newServer.timeouts?.readMs ?? ''}
                  onChange={(e) => setNewServer((p) => ({ ...p, timeouts: { ...(p.timeouts || {}), readMs: e.target.value ? Number(e.target.value) : undefined } }))}
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
                    await upsertMcpServer({ ...newServer });
                    const data = await listMcpServers();
                    setMcpServers(data.servers || []);
                  } catch (e: any) {
                    setMcpError(e?.message || 'Upsert failed');
                  }
                }}
                className="px-3 py-1.5 text-sm font-medium bg-primary text-primary-foreground rounded hover:bg-primary/90"
              >
                Save Server
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
                      setTestFetchResult({ snippet: res.citation?.snippet || (res.content ? res.content.slice(0, 200) : '') });
                    }
                  } catch (e: any) {
                    setTestFetchResult({ error: e?.message || 'Test fetch failed' });
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
                  <p className="text-muted-foreground">Snippet: {testFetchResult.snippet || '(no preview)'}</p>
                )}
              </div>
            )}
          </div>
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
