const { chromium } = require('@playwright/test');

(async () => {
  let browser;
  const launchErrors = [];

  // Try multiple launch strategies to be resilient in varied dev environments
  const tryLaunch = async (opts) => {
    try {
      // eslint-disable-next-line no-console
      console.log('[debug-stream] attempting browser launch with', opts);
      const b = await chromium.launch(opts);
      // eslint-disable-next-line no-console
      console.log('[debug-stream] browser launched');
      return b;
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error('[debug-stream] launch failed', e && e.message);
      launchErrors.push(e && (e.message || String(e)));
      return null;
    }
  };

  // 1) default headless
  browser = await tryLaunch({ headless: true, timeout: 120000 });
  // 2) try non-headless if headless failed
  if (!browser) browser = await tryLaunch({ headless: false, timeout: 120000 });
  // 3) try using system chrome if CHROME_PATH is provided
  if (!browser && process.env.CHROME_PATH) {
    browser = await tryLaunch({ headless: true, timeout: 120000, executablePath: process.env.CHROME_PATH });
  }

  if (!browser) {
    // eslint-disable-next-line no-console
    console.error('[debug-stream] all browser launch attempts failed:', launchErrors);
    throw new Error('Failed to launch Playwright Chromium in any mode');
  }

  const context = await browser.newContext();
  const page = await context.newPage();

  let screenshotTaken = false;
  const screenshotPath = 'frontend/debug-stream-screenshot.png';
  let finalScreenshotTaken = false;
  const finalScreenshotPath = 'frontend/debug-stream-final.png';
  const fs = require('fs');
  const consoleLogPath = 'frontend/debug-stream-console.log';
  // Clear old log
  try { if (fs.existsSync(consoleLogPath)) fs.unlinkSync(consoleLogPath); } catch {}
  page.on('console', async msg => {
    try {
      const text = msg.text();
      const line = `[page console] ${new Date().toISOString()} ${msg.type()} ${text}\n`;
      fs.appendFileSync(consoleLogPath, line);
      console.log(line.trim());
      // If we detect the chat-context onChunk debug message, capture a screenshot once
      if (!screenshotTaken && text.includes('[chat-context] onChunk')) {
        screenshotTaken = true;
        await page.waitForTimeout(250);
        await page.screenshot({ path: screenshotPath, fullPage: true });
        console.log('[debug-stream] screenshot saved to', screenshotPath);
      }
      // Capture final screenshot when onComplete appears
      if (!finalScreenshotTaken && text.includes('[chat-context] onComplete')) {
        finalScreenshotTaken = true;
        await page.waitForTimeout(250);
        await page.screenshot({ path: finalScreenshotPath, fullPage: true });
        console.log('[debug-stream] final screenshot saved to', finalScreenshotPath);
      }
    } catch (e) {
      console.error('[debug-stream] console handler error', e && e.message);
    }
  });
  page.on('request', req => console.log('[page request]', req.method(), req.url()));
  page.on('response', async res => {
    console.log('[page response]', res.status(), res.url(), res.headers()['content-type']);
    if (res.url().includes('/api/chat')) {
      try {
        const headers = res.headers();
        console.log('[page response headers]', headers);
        // Try to read streamed text - some responses may be SSE or chunked
        const text = await res.text();
        console.log('[page response body start]', text.slice(0, 2000));
      } catch (e) {
        console.error('[page response body] error reading body', e);
      }
    }
  });

  // Try multiple times in case the dev server is warming up
  const url = 'http://localhost:3000';
  for (let i = 0; i < 5; i++) {
    try {
      await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 });
      break;
    } catch (e) {
      console.log('[debug-stream] goto attempt', i, 'failed:', e.message);
      if (i === 4) throw e;
      await new Promise(r => setTimeout(r, 2000));
    }
  }
  // Fill the chat input. The app uses a ChatInput with placeholder "Type your message here..."
  const textareaSelector = 'textarea[placeholder="Type your message here..."]';
  try {
    await page.waitForSelector(textareaSelector, { timeout: 120000 });
    await page.fill(textareaSelector, 'hello from playwright');
    // Submit the form via the submit button
    await page.click('button[type="submit"]');
  } catch (e) {
    console.warn('[debug-stream] could not fill/submit input, continuing to wait for streaming (error)', e && e.message);
  }

  // Wait until we see the final onComplete console message or timeout after 2 minutes
  const maxWait = 120000; // 2 minutes
  const start = Date.now();
  while (!finalScreenshotTaken && Date.now() - start < maxWait) {
    await page.waitForTimeout(500);
  }
  if (!finalScreenshotTaken) console.log('[debug-stream] timed out waiting for final onComplete');

  // If final screenshot was taken in 'frontend/debug-stream-final.png', copy it into public for preview
  try {
    const fs = require('fs');
    const path = require('path');
    const finalSrc = path.resolve(finalScreenshotPath);
    const publicDest = path.resolve('frontend/public/debug-stream-final.png');
    if (fs.existsSync(finalSrc)) {
      // ensure public dir exists
      const pubDir = path.dirname(publicDest);
      if (!fs.existsSync(pubDir)) fs.mkdirSync(pubDir, { recursive: true });
      fs.copyFileSync(finalSrc, publicDest);
      console.log('[debug-stream] copied final screenshot to', publicDest);
    }
  } catch (e) {
    console.warn('[debug-stream] failed to copy final screenshot', e && e.message);
  }

  await browser.close();
})();
