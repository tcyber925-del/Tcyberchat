'use client';

import React, { useState, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';

interface ToastProps {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
  onClose: (id: string) => void;
  duration?: number; // in milliseconds
}

const Toast: React.FC<ToastProps> = ({ id, message, type, onClose, duration = 5000 }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose(id);
    }, duration);
    return () => clearTimeout(timer);
  }, [duration, id, onClose]);

  const bgColor = {
    success: 'bg-green-500',
    error: 'bg-red-500',
    info: 'bg-blue-500',
    warning: 'bg-yellow-500',
  }[type];

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 50, scale: 0.3 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.5, transition: { duration: 0.2 } }}
      className={`flex items-center justify-between p-4 rounded-lg shadow-lg text-white ${bgColor} mb-3`}
      role="alert"
    >
      <span>{message}</span>
      <button
        onClick={() => onClose(id)}
        className="ml-4 text-white opacity-75 hover:opacity-100"
        aria-label="Close toast"
      >
        ✕
      </button>
    </motion.div>
  );
};

export default Toast;
