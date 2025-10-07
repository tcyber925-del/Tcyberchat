'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { exportData, importData } from '@/lib/api/data';
import { useChat } from '@/lib/context/chat-context';
import { useTheme } from '@/lib/context/theme-context';
import SettingsPanel from './settings-panel';

interface TopBarProps {
  onToggleChatHistory: () => void;
  onToggleDocumentManager: () => void;
  isChatHistoryOpen: boolean;
  isDocumentManagerOpen: boolean;
}

const TopBar: React.FC<TopBarProps> = ({
  onToggleChatHistory,
  onToggleDocumentManager,
  isChatHistoryOpen,
  isDocumentManagerOpen,
}) => {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const { theme, setTheme, resolvedTheme } = useTheme();

  const handleExport = useCallback(async () => {
    try {
      const blob = await exportData();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const filename = blob.type === 'application/zip'
        ? `chatbot_export_${new Date().toISOString().split('T')[0]}.zip`
        : 'chat-data.zip';
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      console.log('Export completed successfully');
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed. Please check the console for details.');
    }
  }, []);

  const handleImport = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      try {
        const result = await importData(file);
        console.log('Import completed successfully:', result);
        alert(`Import completed successfully!\n${JSON.stringify(result, null, 2)}`);
      } catch (error) {
        console.error('Import failed:', error);
        alert('Import failed. Please check the console for details.');
      }
    }
    event.target.value = '';
  }, []);

  const handleSettingsClick = useCallback(() => {
    setIsSettingsOpen(true);
  }, []);

  const handleSettingsClose = useCallback(() => {
    setIsSettingsOpen(false);
  }, []);

  const handleSettingsKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      setIsSettingsOpen(true);
    }
  }, []);

  const handleThemeToggle = useCallback(() => {
    const themeOrder = ['light', 'dark', 'system'] as const;
    const currentIndex = themeOrder.indexOf(theme);
    const nextIndex = (currentIndex + 1) % themeOrder.length;
    setTheme(themeOrder[nextIndex]);
  }, [theme, setTheme]);

  const handleThemeKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleThemeToggle();
    }
  }, [handleThemeToggle]);

  useEffect(() => {
    const handleEscapeKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isSettingsOpen) {
        setIsSettingsOpen(false);
      }
    };

    if (isSettingsOpen) {
      document.addEventListener('keydown', handleEscapeKey);
      return () => document.removeEventListener('keydown', handleEscapeKey);
    }
  }, [isSettingsOpen]);

  return (
    <>
      <header className="flex items-center justify-between h-16 bg-card border-b border-border p-4">
        <div className="flex items-center gap-4">
          <button
            onClick={onToggleChatHistory}
            className="px-3 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 transition-colors"
            aria-label={isChatHistoryOpen ? "Close chat history" : "Open chat history"}
            aria-expanded={isChatHistoryOpen}
          >
            ☰ Chat History
          </button>
          <button
            onClick={onToggleDocumentManager}
            className="px-3 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 transition-colors"
            aria-label={isDocumentManagerOpen ? "Close document manager" : "Open document manager"}
            aria-expanded={isDocumentManagerOpen}
          >
            📄 Documents
          </button>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-sm">TC</span>
            </div>
            <div>
              <h1 className="text-lg font-semibold text-foreground">TcyberChatbot</h1>
              <p className="text-xs text-muted-foreground">Local First AI Assistant</p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleExport}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 transition-all duration-200 shadow-sm hover:shadow-md"
            aria-label="Export chat data"
          >
            📤 Export
          </button>
          <button
            onClick={handleThemeToggle}
            onKeyDown={handleThemeKeyDown}
            className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 transition-all duration-200 shadow-sm hover:shadow-md"
            aria-label={`Switch to ${theme === 'light' ? 'dark' : theme === 'dark' ? 'system' : 'light'} theme`}
          >
            {resolvedTheme === 'dark' ? '🌙' : '☀️'} {theme === 'system' ? 'Auto' : theme === 'light' ? 'Light' : 'Dark'}
          </button>
          <label htmlFor="import-file" className="inline-block">
            <input
              id="import-file"
              type="file"
              accept=".zip"
              onChange={handleImport}
              className="hidden"
            />
            <span
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 cursor-pointer focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 transition-all duration-200 shadow-sm hover:shadow-md inline-block"
              tabIndex={0}
              role="button"
              aria-label="Import chat data from ZIP file"
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  document.getElementById('import-file')?.click();
                }
              }}
            >
              📥 Import
            </span>
          </label>
          <button
            onClick={handleSettingsClick}
            onKeyDown={handleSettingsKeyDown}
            className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 transition-all duration-200 shadow-sm hover:shadow-md"
            aria-label="Open settings panel"
            aria-expanded={isSettingsOpen}
            aria-haspopup="dialog"
          >
            ⚙️ Settings
          </button>
        </div>
      </header>

      {/* Settings Modal */}
      {isSettingsOpen && (
        <div
          className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50"
          role="dialog"
          aria-modal="true"
          aria-labelledby="settings-title"
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              handleSettingsClose();
            }
          }}
        >
          <div
            className="bg-card border border-border rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center p-4 border-b border-border">
              <h2 id="settings-title" className="text-xl font-bold text-card-foreground">Settings</h2>
              <button
                onClick={handleSettingsClose}
                className="text-muted-foreground hover:text-foreground focus:outline-none focus:ring-2 focus:ring-ring rounded"
                aria-label="Close settings"
              >
                ✕
              </button>
            </div>
            <div className="p-4">
              <SettingsPanel onClose={handleSettingsClose} />
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default TopBar;
