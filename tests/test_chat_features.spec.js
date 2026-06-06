const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:5009';

test.describe('Chat UI Features', () => {
  test.use({ viewport: { width: 1280, height: 800 } });

  test('no raw tool log shown to user after agent query', async ({ page }) => {
    await page.goto(`${BASE_URL}/app`);
    await page.waitForTimeout(1000);

    const chatInput = page.locator('#chat-input');
    await chatInput.fill('market: top selling artists');
    await page.locator('#send-btn').click();

    // Wait for response to complete
    await page.waitForTimeout(8000);

    // No tool-log div should be visible (appendToolLog removed)
    const toolLog = page.locator('.tool-log');
    await expect(toolLog).toHaveCount(0);
  });

  test('response does not contain raw SQL', async ({ page }) => {
    await page.goto(`${BASE_URL}/app`);
    await page.waitForTimeout(1000);

    const chatInput = page.locator('#chat-input');
    await chatInput.fill('market: top selling artists');
    await page.locator('#send-btn').click();

    // Wait for full response
    await page.waitForTimeout(15000);

    // Check that no SQL keywords leak into the response
    const messages = page.locator('.msg-assistant .msg-bubble');
    const count = await messages.count();
    expect(count).toBeGreaterThan(0);

    const lastMsg = messages.last();
    const text = await lastMsg.textContent();
    expect(text).not.toContain('SELECT ');
    expect(text).not.toContain('FROM kanvas.');
    expect(text).not.toContain('SQL used:');
  });

  test('assistant response renders for basic query', async ({ page }) => {
    await page.goto(`${BASE_URL}/app`);
    await page.waitForTimeout(1000);

    const chatInput = page.locator('#chat-input');
    await chatInput.fill('Hello, what can you do?');
    await page.locator('#send-btn').click();

    // Wait for response
    const assistantMsg = page.locator('.msg-assistant');
    await expect(assistantMsg).toBeVisible({ timeout: 30000 });
  });
});

test.describe('Art Guru Game', () => {
  test.use({ viewport: { width: 1280, height: 800 } });

  test('Art Guru responds with character selection', async ({ page }) => {
    await page.goto(`${BASE_URL}/app/art-guru`);
    await page.waitForTimeout(1000);

    const chatInput = page.locator('#chat-input');
    await chatInput.fill('start');
    await page.locator('#send-btn').click();

    // Should get a response with character info
    const assistantMsg = page.locator('.msg-assistant');
    await expect(assistantMsg).toBeVisible({ timeout: 15000 });

    const text = await assistantMsg.textContent();
    expect(text).toContain('Art Guru');
  });
});
