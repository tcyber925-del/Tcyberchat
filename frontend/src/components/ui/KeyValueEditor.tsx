"use client";

import React from "react";

export type KVPair = { key: string; value: string };

export function KeyValueEditor({
  value,
  onChange,
  addLabel = "Add header",
  placeholderKey = "Header name",
  placeholderValue = "Header value",
}: {
  value: Record<string, string>;
  onChange: (next: Record<string, string>) => void;
  addLabel?: string;
  placeholderKey?: string;
  placeholderValue?: string;
}) {
  const entries: KVPair[] = React.useMemo(
    () => Object.entries(value || {}).map(([k, v]) => ({ key: k, value: String(v ?? "") })),
    [value]
  );

  const updateAt = (idx: number, next: KVPair) => {
    const out: Record<string, string> = {};
    entries.forEach((e, i) => {
      const k = i === idx ? next.key : e.key;
      const v = i === idx ? next.value : e.value;
      if (k) out[k] = v;
    });
    onChange(out);
  };

  const removeAt = (idx: number) => {
    const out: Record<string, string> = {};
    entries.forEach((e, i) => {
      if (i !== idx && e.key) out[e.key] = e.value;
    });
    onChange(out);
  };

  const add = () => {
    const out = { ...(value || {}) } as Record<string, string>;
    let base = "X-Header";
    let k = base;
    let n = 1;
    while (out[k]) {
      k = base + "-" + n++;
    }
    out[k] = "";
    onChange(out);
  };

  return (
    <div className="space-y-2">
      {entries.length === 0 && (
        <div className="text-xs text-muted-foreground">No entries yet.</div>
      )}
      <div className="space-y-2">
        {entries.map((e, idx) => (
          <div key={idx} className="grid grid-cols-12 gap-2 items-center">
            <input
              className="col-span-5 px-2 py-1 border border-input bg-background rounded text-xs"
              placeholder={placeholderKey}
              value={e.key}
              onChange={(ev) => updateAt(idx, { key: ev.target.value, value: e.value })}
            />
            <input
              className="col-span-6 px-2 py-1 border border-input bg-background rounded text-xs"
              placeholder={placeholderValue}
              value={e.value}
              onChange={(ev) => updateAt(idx, { key: e.key, value: ev.target.value })}
            />
            <button
              type="button"
              className="col-span-1 text-xs px-2 py-1 rounded bg-rose-100 text-rose-900 hover:bg-rose-200"
              onClick={() => removeAt(idx)}
              aria-label="Remove row"
            >
              ✕
            </button>
          </div>
        ))}
      </div>
      <button
        type="button"
        className="text-xs px-2 py-1 rounded bg-muted hover:bg-muted/80"
        onClick={add}
      >
        {addLabel}
      </button>
    </div>
  );
}
