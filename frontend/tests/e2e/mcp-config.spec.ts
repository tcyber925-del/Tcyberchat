import { test, expect } from '@playwright/test';

test('MCP Configuration Test', async ({ page }) => {
    // 1. Navigate to the app
    await page.goto('/');

    // 2. Open Settings
    // Wait for the settings button to be visible and click it
    const settingsButton = page.getByRole('button', { name: 'Settings' });
    await expect(settingsButton).toBeVisible();
    await settingsButton.click();

    // 3. Verify Settings Panel is open
    const mcpLegend = page.getByText('Integrations: MCP');
    await expect(mcpLegend).toBeVisible();

    // 4. Fill in MCP Server details for SSE
    const addServerSection = page.locator('.border', { hasText: 'Add / Update Server' });

    // ID
    const idInput = addServerSection.locator('input').first(); // Assuming ID is the first input
    await idInput.fill('test-sse-server');

    // Transport
    // Select "SSE (HTTP)"
    await addServerSection.locator('select').first().selectOption('sse');

    // URL
    // The placeholder changes when SSE is selected
    const urlInput = addServerSection.getByPlaceholder('http://localhost:8000/sse');
    await expect(urlInput).toBeVisible();
    await urlInput.fill('https://mcp.context7.com/mcp');

    // 5. Test Connection
    const testConnButton = addServerSection.getByRole('button', { name: 'Test Connection' });
    await testConnButton.click();

    // Wait for success toast or message
    // The toast might take a moment.
    await expect(page.getByText('Connection Successful')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('Found tools:')).toBeVisible();

    // 6. Save
    const saveButton = addServerSection.getByRole('button', { name: 'Save Server' });
    await saveButton.click();

    // 7. Verify it appears in the list
    const configuredSection = page.locator('.border', { hasText: 'Configured Servers' });
    await expect(configuredSection.getByText('test-sse-server')).toBeVisible();
    await expect(configuredSection.getByText('sse')).toBeVisible();

    // 8. Take a screenshot
    await page.screenshot({ path: 'mcp-config-test.png' });
});
