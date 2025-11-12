'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';

// Settings interfaces
export interface UserSettings {
  // AI Settings
  selectedModel: string;
  webSearchEnabled: boolean;

  // UI Settings
  theme: 'light' | 'dark' | 'system';

  // Feature flags
  multimodalEnabled: boolean;
  showWebDebugBadges: boolean; // Dev-only inline badge toggle
  showSourcesPanel: boolean; // Show Sources cards under assistant messages

  // Version for migrations
  version: number;
}

export interface SettingsContextType {
  settings: UserSettings;
  updateSettings: (updates: Partial<UserSettings>) => void;
  resetSettings: () => void;
  isLoading: boolean;
  isSettingsOpen: boolean;
  toggleSettingsPanel: () => void;
}

// Default settings
const DEFAULT_SETTINGS: UserSettings = {
  selectedModel: 'llama3.2:1b',
  webSearchEnabled: true,
  theme: 'system',
  multimodalEnabled: true,
  showWebDebugBadges: false,
  showSourcesPanel: true,
  version: 3,
};

// Storage key
const SETTINGS_STORAGE_KEY = 'tcyber-chatbot-settings';

// Migration functions
const migrateSettings = (stored: any): UserSettings => {
  const currentVersion = 3;

  if (!stored || typeof stored !== 'object') {
    return DEFAULT_SETTINGS;
  }

  // v1 -> v2: add showWebDebugBadges default false
  if (!stored.version || stored.version < 2) {
    stored.showWebDebugBadges = false;
  }
  // v2 -> v3: add showSourcesPanel default true
  if (!stored.version || stored.version < 3) {
    stored.showSourcesPanel = true;
  }

  return { ...DEFAULT_SETTINGS, ...stored, version: currentVersion };
};

// Settings context
const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

// Settings provider component
export const SettingsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [settings, setSettings] = useState<UserSettings>(DEFAULT_SETTINGS);
  const [isLoading, setIsLoading] = useState(true);
  const [isSettingsOpen, setSettingsOpen] = useState(false);

  // Load settings from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(SETTINGS_STORAGE_KEY);
      if (stored) {
        const parsedSettings = JSON.parse(stored);
        const migratedSettings = migrateSettings(parsedSettings);
        setSettings(migratedSettings);
      }
    } catch (error) {
      console.warn('Failed to load settings from localStorage:', error);
      // Use defaults if parsing fails
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Save settings to localStorage whenever they change
  useEffect(() => {
    if (!isLoading) {
      try {
        localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings));
      } catch (error) {
        console.error('Failed to save settings to localStorage:', error);
      }
    }
  }, [settings, isLoading]);

  // Update settings function
  const updateSettings = (updates: Partial<UserSettings>) => {
    setSettings((prev) => ({ ...prev, ...updates }));
  };

  // Reset settings to defaults
  const resetSettings = () => {
    setSettings(DEFAULT_SETTINGS);
  };

  const toggleSettingsPanel = () => {
    setSettingsOpen((prev) => !prev);
  };

  const value: SettingsContextType = {
    settings,
    updateSettings,
    resetSettings,
    isLoading,
    isSettingsOpen,
    toggleSettingsPanel,
  };

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
};

// Hook to use settings context
export const useSettings = (): SettingsContextType => {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};

// Export defaults for testing
export { DEFAULT_SETTINGS };
