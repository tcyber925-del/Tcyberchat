export const dynamic = 'force-dynamic';

// Proxy this API to the local backend stream endpoint which returns SSE.
export async function POST(req: Request) {
  // Determine backend URL with multiple fallbacks:
  // 1. BACKEND_CHAT_URL (explicit full URL, may include path)
  // 2. NEXT_PUBLIC_API_URL (frontend env commonly used for backend base URL)
  // 3. default to local backend used by this repo
  let backend = process.env.BACKEND_CHAT_URL ?? process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

  // If the provided backend does not include a /chat path, append the streaming path.
  // Allow callers to provide either the base URL (e.g. http://localhost:8000) or
  // the full streaming URL (e.g. http://localhost:8000/chat/stream).
  if (!backend.includes('/chat')) {
    backend = backend.replace(/\/$/, '');
    backend = `${backend}/chat/stream`;
  }

  // Forward the incoming request body to the backend streaming endpoint.
  let forwarded: Response;
  try {
    forwarded = await fetch(backend, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      // forward raw text so body types (SSE controls) are preserved
      body: await req.text(),
    });
  } catch (err: any) {
    // Network or connection error while contacting backend (e.g., ECONNREFUSED).
    // Return a helpful 502 response so the frontend UI can show a clear message.
    // eslint-disable-next-line no-console
    console.error('[proxy] failed to reach backend at', backend, err && err.message ? err.message : err);

    const msg = {
      error: 'backend_unreachable',
      message: `Unable to reach backend at ${backend}. Is the backend running?`,
      suggestion: 'Start the backend (default: port 8000) or set BACKEND_CHAT_URL / NEXT_PUBLIC_API_URL in frontend/.env to the correct URL.'
    };

    return new Response(JSON.stringify(msg), {
      status: 502,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  // Debug: log proxied response status and content-type (best-effort)
  try {
    // eslint-disable-next-line no-console
    console.log('[proxy] backend response status', forwarded.status);
    // eslint-disable-next-line no-console
    console.log('[proxy] backend content-type', forwarded.headers.get('content-type'));
  } catch (e) {
    // ignore
  }

  // Copy backend headers to preserve streaming behavior (content-type, transfer-encoding, etc.).
  const headers = new Headers(forwarded.headers as any);

  // Ensure the response is not buffered by proxies (helps SSE / chunked streaming).
  headers.set('Cache-Control', 'no-cache');
  headers.set('X-Accel-Buffering', 'no');

  // Remove content-length if present — streaming responses should not advertise a fixed length.
  if (headers.has('content-length')) headers.delete('content-length');

  // Stream backend response back to the client. This preserves SSE streaming.
  return new Response(forwarded.body, {
    status: forwarded.status,
    headers,
  });
}
