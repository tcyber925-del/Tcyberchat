'use client';

import React, { lazy, Suspense } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import SettingsPanel from './settings-panel';

interface SettingsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

const LoadingFallback = () => (
  <div className="flex items-center justify-center p-4">
    <div className="animate-spin rounded-full h-6 w-6 border-2 border-primary border-t-transparent"></div>
  </div>
);

const SettingsDrawer: React.FC<SettingsDrawerProps> = ({ isOpen, onClose }) => {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 30, stiffness: 300 }}
          className="fixed right-0 top-0 h-full w-80 bg-card shadow-lg z-50 flex flex-col"
        >
          <div className="flex items-center justify-between p-4 border-b border-border">
            <h2 className="text-lg font-semibold">Settings</h2>
            <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
              ✕
            </button>
          </div>
          <div className="flex-grow overflow-y-auto p-4">
            <Suspense fallback={<LoadingFallback />}>
              <SettingsPanel onClose={onClose} />
            </Suspense>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default SettingsDrawer;
