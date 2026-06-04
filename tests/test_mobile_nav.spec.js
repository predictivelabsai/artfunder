const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:5009';

const EXPECTED_MOBILE_NAV_ITEMS = [
  { key: 'home', href: '/', label: 'Home' },
  { key: 'advisory', href: '/app', label: 'Advisory' },
  { key: 'investors', href: '/investors', label: 'Collection' },
  { key: 'artists', href: '/artists', label: 'Artists' },
  { key: 'galleries', href: '/galleries', label: 'Galleries' },
  { key: 'about', href: '/about', label: 'About' },
  { key: 'art-index', href: '/app/market-map', label: 'Art Index' },
  { key: 'contact', href: '/contact', label: 'Contact' },
];

test.describe('Mobile Navigation', () => {
  test.use({ viewport: { width: 375, height: 812 } }); // iPhone viewport

  test('hamburger menu button is visible on mobile', async ({ page }) => {
    await page.goto(BASE_URL);
    const hamburger = page.getByTestId('mobile-menu-btn');
    await expect(hamburger).toBeVisible();
  });

  test('desktop nav links are hidden on mobile', async ({ page }) => {
    await page.goto(BASE_URL);
    const desktopNav = page.locator('ul.hidden.lg\\:flex');
    await expect(desktopNav).toBeHidden();
  });

  test('mobile menu is hidden by default', async ({ page }) => {
    await page.goto(BASE_URL);
    const mobileMenu = page.getByTestId('mobile-menu');
    await expect(mobileMenu).toBeHidden();
  });

  test('clicking hamburger opens mobile menu', async ({ page }) => {
    await page.goto(BASE_URL);
    const hamburger = page.getByTestId('mobile-menu-btn');
    const mobileMenu = page.getByTestId('mobile-menu');

    await hamburger.click();
    await expect(mobileMenu).toBeVisible();
  });

  test('mobile menu contains all navigation items', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.getByTestId('mobile-menu-btn').click();

    const mobileMenu = page.getByTestId('mobile-menu');
    await expect(mobileMenu).toBeVisible();

    for (const item of EXPECTED_MOBILE_NAV_ITEMS) {
      const link = page.getByTestId(`mobile-nav-${item.key}`);
      await expect(link).toBeVisible();
      await expect(link).toHaveAttribute('href', item.href);
      await expect(link).toContainText(item.label);
    }
  });

  test('clicking hamburger again closes mobile menu', async ({ page }) => {
    await page.goto(BASE_URL);
    const hamburger = page.getByTestId('mobile-menu-btn');
    const mobileMenu = page.getByTestId('mobile-menu');

    await hamburger.click();
    await expect(mobileMenu).toBeVisible();

    await hamburger.click();
    await expect(mobileMenu).toBeHidden();
  });

  test('mobile menu links navigate correctly', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.getByTestId('mobile-menu-btn').click();

    const aboutLink = page.getByTestId('mobile-nav-about');
    await aboutLink.click();
    await expect(page).toHaveURL(`${BASE_URL}/about`);
  });
});

test.describe('Desktop Navigation', () => {
  test.use({ viewport: { width: 1280, height: 800 } });

  test('hamburger is hidden on desktop', async ({ page }) => {
    await page.goto(BASE_URL);
    const hamburger = page.getByTestId('mobile-menu-btn');
    await expect(hamburger).toBeHidden();
  });

  test('desktop nav links are visible', async ({ page }) => {
    await page.goto(BASE_URL);
    const desktopNav = page.locator('nav ul');
    await expect(desktopNav).toBeVisible();

    for (const item of EXPECTED_MOBILE_NAV_ITEMS) {
      const link = desktopNav.locator(`a[href="${item.href}"]`);
      await expect(link).toBeVisible();
    }
  });
});
