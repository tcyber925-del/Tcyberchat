import { useSettings as useSettingsContext } from '../context/settings-context';

// Re-export the hook for convenience
export const useSettings = useSettingsContext;

// Additional hooks can be added here for specific settings operations
export const useTheme = () => {
  const { settings, updateSettings } = useSettingsContext();

  const setTheme = (theme: 'light' | 'dark' | 'system') => {
    updateSettings({ theme });
  };

  return {
    theme: settings.theme,
    setTheme,
  };
};

export const useModelSelection = () => {
  const { settings, updateSettings } = useSettingsContext();

  const setSelectedModel = (selectedModel: string) => {
    updateSettings({ selectedModel });
  };

  return {
    selectedModel: settings.selectedModel,
    setSelectedModel,
  };
};

export const useWebSearch = () => {
  const { settings, updateSettings } = useSettingsContext();

  const setWebSearchEnabled = (webSearchEnabled: boolean) => {
    updateSettings({ webSearchEnabled });
  };

  return {
    webSearchEnabled: settings.webSearchEnabled,
    setWebSearchEnabled,
  };
};

export const useMultimodal = () => {
  const { settings, updateSettings } = useSettingsContext();

  const setMultimodalEnabled = (multimodalEnabled: boolean) => {
    updateSettings({ multimodalEnabled });
  };

  return {
    multimodalEnabled: settings.multimodalEnabled,
    setMultimodalEnabled,
  };
};