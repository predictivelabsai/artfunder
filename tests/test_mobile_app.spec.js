const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:5009';

test.describe('Mobile App View - News Panel', () => {
  test.use({ viewport: { width: 375, height: 812 } });

  test('news panel is hidden by default on mobile', async ({ page }) => {
    await page.goto(`${BASE_URL}/app`);
    await page.waitForTimeout(1000);
    const rightPane = page.locator('#right-pane');
    await expect(rightPane).not.toHaveClass(/\bopen\b/);
  });

  test('news toggle icon is visible on mobile', async ({ page }) => {
    await page.goto(`${BASE_URL}/app`);
    const newsBtn = page.locator('#news-toggle-btn');
    await expect(newsBtn).toBeVisible();
  });

  test('canvas button is hidden on mobile', async ({ page }) => {
    await page.goto(`${BASE_URL}/app`);
    const canvasBtn = page.locator('#artifact-btn');
    await expect(canvasBtn).toBeHidden();
  });

  test('tapping news icon opens news panel', async ({ page }) => {
    await page.goto(`${BASE_URL}/app`);
    await page.waitForTimeout(500);
    await page.locator('#news-toggle-btn').click();
    await page.waitForTimeout(500);
    const rightPane = page.locator('#right-pane');
    await expect(rightPane).toHaveClass(/\bopen\b/);
  });

  test('news panel has close button on mobile', async ({ page }) => {
    await page.goto(`${BASE_URL}/app`);
    await page.waitForTimeout(500);
    await page.locator('#news-toggle-btn').click();
    await page.waitForTimeout(500);
    const closeBtn = page.locator('.right-close');
    await expect(closeBtn).toBeVisible();
  });

  test('close button closes news panel', async ({ page }) => {
    await page.goto(`${BASE_URL}/app`);
    await page.waitForTimeout(500);
    await page.locator('#news-toggle-btn').click();
    await page.waitForTimeout(500);
    await page.locator('.right-close').click();
    await page.waitForTimeout(500);
    const rightPane = page.locator('#right-pane');
    await expect(rightPane).not.toHaveClass(/\bopen\b/);
  });

  test('chat input is visible and usable on mobile', async ({ page }) => {
    await page.goto(`${BASE_URL}/app`);
    const chatInput = page.locator('#chat-input');
    await expect(chatInput).toBeVisible();
    const sendBtn = page.locator('#send-btn');
    await expect(sendBtn).toBeVisible();
  });

  test('hamburger menu opens left sidebar', async ({ page }) => {
    await page.goto(`${BASE_URL}/app`);
    await page.locator('.mobile-menu-btn').click();
    await page.waitForTimeout(300);
    const leftPane = page.locator('.left-pane');
    await expect(leftPane).toHaveClass(/\bopen\b/);
  });
});

test.describe('Desktop App View - News Panel', () => {
  test.use({ viewport: { width: 1280, height: 800 } });

  test('news panel is visible by default on desktop', async ({ page }) => {
    await page.goto(`${BASE_URL}/app`);
    await page.waitForTimeout(1000);
    const rightPane = page.locator('#right-pane');
    await expect(rightPane).toHaveClass(/\bopen\b/);
  });

  test('news toggle icon is hidden on desktop', async ({ page }) => {
    await page.goto(`${BASE_URL}/app`);
    const newsBtn = page.locator('#news-toggle-btn');
    await expect(newsBtn).toBeHidden();
  });

  test('canvas button is visible on desktop', async ({ page }) => {
    await page.goto(`${BASE_URL}/app`);
    const canvasBtn = page.locator('#artifact-btn');
    await expect(canvasBtn).toBeVisible();
  });

  test('close button is hidden on desktop', async ({ page }) => {
    await page.goto(`${BASE_URL}/app`);
    const closeBtn = page.locator('.right-close');
    await expect(closeBtn).toBeHidden();
  });
});
