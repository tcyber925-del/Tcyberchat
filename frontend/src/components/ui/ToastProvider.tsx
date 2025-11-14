"use client";

import React, { createContext, useCallback, useContext, useMemo, useState } from "react";

export type Toast = {
  id: string;
  title?: string;
  description?: string;
  variant?: "default" | "success" | "error" | "warning";
  durationMs?: number;
};

type ToastContextValue = {
  toasts: Toast[];
  showToast: (t: Omit<Toast, "id">) => void;
  removeToast: (id: string) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback((t: Omit<Toast, "id">) => {
    const id = Math.random().toString(36).slice(2);
    const toast: Toast = { id, durationMs: 4000, variant: "default", ...t };
    setToasts((prev) => [...prev, toast]);
    const timeout = setTimeout(() => removeToast(id), toast.durationMs);
    return () => clearTimeout(timeout);
  }, [removeToast]);

  const value = useMemo(() => ({ toasts, showToast, removeToast }), [toasts, showToast, removeToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      {/* Toast viewport */}
      <div className="fixed z-50 right-4 bottom-4 space-y-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={
              `min-w-[260px] max-w-[380px] rounded-md px-3 py-2 shadow-lg border text-sm ` +
              (t.variant === "success"
                ? "bg-emerald-100 border-emerald-300 text-emerald-900"
                : t.variant === "error"
                ? "bg-rose-100 border-rose-300 text-rose-900"
                : t.variant === "warning"
                ? "bg-amber-100 border-amber-300 text-amber-900"
                : "bg-muted border-input text-foreground")
            }
          >
            {t.title && <div className="font-medium mb-0.5">{t.title}</div>}
            {t.description && <div className="text-xs opacity-90">{t.description}</div>}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return ctx;
}
