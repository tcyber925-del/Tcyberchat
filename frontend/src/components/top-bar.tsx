'use client';

import React, { useCallback, useEffect } from 'react';
import { exportData, importData } from '@/lib/api/data';
import { useChat } from '@/lib/context/chat-context';
import { useSettings } from '@/lib/context/settings-context';
import { useTheme } from '@/lib/context/theme-context';

interface TopBarProps {
  onToggleChatHistory: () => void;
  onToggleDocumentManager: () => void;
  isChatHistoryOpen: boolean;
  isDocumentManagerOpen: boolean;
  onNewChat: () => void; // Add onNewChat prop
}

const TopBar: React.FC<TopBarProps> = ({
  onToggleChatHistory,
  onToggleDocumentManager,
  isChatHistoryOpen,
  isDocumentManagerOpen,
  onNewChat, // Destructure onNewChat
}) => {
  const { toggleSettingsPanel, isSettingsOpen } = useSettings();
  const { theme, setTheme, resolvedTheme } = useTheme();

  const handleExport = useCallback(async () => {
    try {
      const blob = await exportData();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const filename =
        blob.type === 'application/zip'
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
    toggleSettingsPanel();
  }, [toggleSettingsPanel]);

  const handleSettingsKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        toggleSettingsPanel();
      }
    },
    [toggleSettingsPanel],
  );

  const handleThemeToggle = useCallback(() => {
    const themeOrder = ['light', 'dark', 'system'] as const;
    const currentIndex = themeOrder.indexOf(theme);
    const nextIndex = (currentIndex + 1) % themeOrder.length;
    setTheme(themeOrder[nextIndex]);
  }, [theme, setTheme]);

  const handleThemeKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        handleThemeToggle();
      }
    },
    [handleThemeToggle],
  );

  useEffect(() => {
    const handleEscapeKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isSettingsOpen) {
        toggleSettingsPanel();
      }
    };

    if (isSettingsOpen) {
      document.addEventListener('keydown', handleEscapeKey);
      return () => document.removeEventListener('keydown', handleEscapeKey);
    }
  }, [isSettingsOpen, toggleSettingsPanel]);

  return (
    <>
      <header className="flex items-center justify-between h-16 bg-card border-b border-border p-4">
        <div className="flex items-center gap-4">
          <button
            onClick={onToggleChatHistory}
            className="px-3 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 transition-colors"
            aria-label={isChatHistoryOpen ? 'Close chat history' : 'Open chat history'}
            aria-expanded={isChatHistoryOpen}
          >
            ☰ Chat History
          </button>
          <button
            onClick={onToggleDocumentManager}
            className="px-3 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 transition-colors"
            aria-label={isDocumentManagerOpen ? 'Close document manager' : 'Open document manager'}
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
            onClick={onNewChat}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 transition-all duration-200 shadow-sm hover:shadow-md"
            aria-label="Start a new chat"
          >
            ✨ New Chat
          </button>
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
            {resolvedTheme === 'dark' ? '🌙' : '☀️'}{' '}
            {theme === 'system' ? 'Auto' : theme === 'light' ? 'Light' : 'Dark'}
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
    </>
  );
};

export default TopBar;
