export const dynamic = 'force-dynamic';

// Proxy this API to the local backend stream endpoint which returns SSE.
export async function POST(req: Request) {
  // Forward the incoming request body to the backend /chat/stream endpoint.
  const backendUrl = process.env.BACKEND_CHAT_URL ?? 'http://localhost:3001/chat/stream';

  const forwarded = await fetch(backendUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: await req.text(),
  });

  // Debug: log proxied response status and content-type
  try {
    // eslint-disable-next-line no-console
    console.log('[proxy] backend response status', forwarded.status);
    // eslint-disable-next-line no-console
    console.log('[proxy] backend content-type', forwarded.headers.get('content-type'));
  } catch (e) {
    // ignore
  }

  // Copy backend headers to preserve streaming behavior (content-type, transfer-encoding, etc.).
  // Use a fresh Headers object so we can adjust buffering headers as needed.
  const headers = new Headers(forwarded.headers as any);

  // Ensure the response is not buffered by proxies (helps SSE / chunked streaming).
  // Set conservative cache-control and disable upstream buffering where supported.
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
