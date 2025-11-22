MCP Health Flow and Init Flags

This document describes the environment variables and endpoints used to control the MCP health/init flow and basic instrumentation.

Environment variables

- `MCP_HEALTH_FLOW` (backend): if set to `false`, the MCP health/init flow is disabled. Default: `true`.
- `MCP_INIT_COOLDOWN` (backend): cooldown in seconds between allowed `init-model` calls. Default: `30`.
- `NEXT_PUBLIC_MCP_HEALTH_FLOW` (frontend): feature flag exposed to the frontend. If set to `false`, the SettingsPanel will skip the MCP health/polling flow and fallback to direct model fetch. Default: `true`.

Endpoints

- `GET /api/integrations/mcp/health` — returns AI/model availability details and increments a health check counter.
- `POST /api/integrations/mcp/init-model` — starts a non-blocking background warm-init of the AI providers/models. Protected by cooldown and the `MCP_HEALTH_FLOW` flag.
- `GET /api/integrations/mcp/metrics` — lightweight in-memory metrics for quick inspection (health check count, init requests/started/failed).

Notes

- Metrics are in-memory and reset on process restart. For production, forward metrics to a monitoring backend (Prometheus, OpenTelemetry, Application Insights, etc.).
- The feature-flag approach allows a controlled rollout. If issues are found, set both `MCP_HEALTH_FLOW=false` and `NEXT_PUBLIC_MCP_HEALTH_FLOW=false` to revert the new behavior.
