import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SCREENSHOT_DIR = path.join(__dirname, 'screenshots');
const BASE_URL = 'http://localhost:5173';

// Ensure screenshot dir exists
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

const PAGES = [
  { path: '/',           name: 'Home' },
  { path: '/search',     name: 'SmartQuery' },
  { path: '/contacts',   name: 'Contacts' },
  { path: '/programs',   name: 'Programs' },
  { path: '/jobs',       name: 'Jobs_Kanban' },
  { path: '/outreach',   name: 'Outreach' },
  { path: '/analytics',  name: 'Analytics' },
  { path: '/org-chart',  name: 'OrgChart' },
  { path: '/agents',     name: 'Agents' },
];

const results = [];

function log(msg) {
  console.log(`[${new Date().toISOString().slice(11,19)}] ${msg}`);
}

async function testPage(page, { path: pagePath, name }) {
  const url = `${BASE_URL}${pagePath}`;
  const errors = [];
  const consoleErrors = [];

  // Collect console errors
  const consoleHandler = (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text().slice(0, 200));
    }
  };
  page.on('console', consoleHandler);

  // Collect JS exceptions
  const errorHandler = (err) => {
    errors.push(err.message.slice(0, 200));
  };
  page.on('pageerror', errorHandler);

  try {
    log(`Navigating to ${name} (${url})`);
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 15000 });

    // Wait for content to render
    await new Promise(r => setTimeout(r, 3000));

    // Check body text length
    const bodyText = await page.evaluate(() => document.body?.innerText || '');
    const textLength = bodyText.length;
    const isBlank = textLength < 20;

    // Check for React error boundaries
    const hasErrorBoundary = await page.evaluate(() => {
      const text = document.body?.innerText || '';
      return text.includes('Something went wrong') ||
             text.includes('Error boundary') ||
             text.includes('An error occurred');
    });

    // Take screenshot
    const screenshotPath = path.join(SCREENSHOT_DIR, `${name}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: false });

    const status = (!isBlank && !hasErrorBoundary && errors.length === 0) ? 'PASS' : 'FAIL';
    const details = [];
    if (isBlank) details.push(`Page blank (${textLength} chars)`);
    if (hasErrorBoundary) details.push('React error boundary detected');
    if (errors.length > 0) details.push(`JS errors: ${errors.join('; ')}`);
    if (consoleErrors.length > 0) details.push(`Console errors: ${consoleErrors.length}`);

    const result = {
      name,
      path: pagePath,
      status,
      textLength,
      jsErrors: errors.length,
      consoleErrors: consoleErrors.length,
      details: details.length > 0 ? details.join(' | ') : `OK (${textLength} chars)`,
      screenshot: `${name}.png`,
    };

    results.push(result);
    log(`  ${status}: ${result.details}`);
  } catch (err) {
    results.push({
      name,
      path: pagePath,
      status: 'FAIL',
      textLength: 0,
      jsErrors: 0,
      consoleErrors: 0,
      details: `Navigation error: ${err.message.slice(0, 200)}`,
      screenshot: null,
    });
    log(`  FAIL: ${err.message.slice(0, 100)}`);
  } finally {
    page.off('console', consoleHandler);
    page.off('pageerror', errorHandler);
  }
}

async function testDarkMode(page) {
  log('Testing dark mode toggle...');
  try {
    await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle2', timeout: 15000 });
    await new Promise(r => setTimeout(r, 2000));

    // Look for dark mode toggle button
    const toggleFound = await page.evaluate(() => {
      // Try common selectors for dark mode toggle
      const selectors = [
        'button[aria-label*="dark"]',
        'button[aria-label*="theme"]',
        'button[aria-label*="mode"]',
        '[data-testid="dark-mode"]',
        '[data-testid="theme-toggle"]',
      ];
      for (const sel of selectors) {
        const el = document.querySelector(sel);
        if (el) { el.click(); return { found: true, selector: sel }; }
      }
      // Try finding by icon (sun/moon)
      const buttons = document.querySelectorAll('button');
      for (const btn of buttons) {
        const svg = btn.querySelector('svg');
        if (svg && (btn.innerHTML.includes('moon') || btn.innerHTML.includes('sun') || btn.innerHTML.includes('Moon') || btn.innerHTML.includes('Sun'))) {
          btn.click();
          return { found: true, selector: 'svg-icon-button' };
        }
      }
      return { found: false };
    });

    if (!toggleFound.found) {
      results.push({ name: 'DarkMode', path: '-', status: 'FAIL', textLength: 0, jsErrors: 0, consoleErrors: 0, details: 'Dark mode toggle not found', screenshot: null });
      log('  FAIL: Dark mode toggle not found');
      return;
    }

    await new Promise(r => setTimeout(r, 500));

    const hasDarkClass = await page.evaluate(() => {
      return document.documentElement.classList.contains('dark') ||
             document.body.classList.contains('dark') ||
             document.documentElement.getAttribute('data-theme') === 'dark';
    });

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'DarkMode.png') });

    results.push({
      name: 'DarkMode',
      path: '-',
      status: hasDarkClass ? 'PASS' : 'FAIL',
      textLength: 0,
      jsErrors: 0,
      consoleErrors: 0,
      details: hasDarkClass ? `Dark class applied (toggle: ${toggleFound.selector})` : `Toggle clicked but no dark class found (toggle: ${toggleFound.selector})`,
      screenshot: 'DarkMode.png',
    });
    log(`  ${hasDarkClass ? 'PASS' : 'FAIL'}: Dark mode ${hasDarkClass ? 'activated' : 'not activated'}`);
  } catch (err) {
    results.push({ name: 'DarkMode', path: '-', status: 'FAIL', textLength: 0, jsErrors: 0, consoleErrors: 0, details: `Error: ${err.message.slice(0, 200)}`, screenshot: null });
    log(`  FAIL: ${err.message.slice(0, 100)}`);
  }
}

async function testKeyboard(page) {
  log('Testing Ctrl+K command palette...');
  try {
    await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle2', timeout: 15000 });
    await new Promise(r => setTimeout(r, 2000));

    await page.keyboard.down('Control');
    await page.keyboard.press('k');
    await page.keyboard.up('Control');

    await new Promise(r => setTimeout(r, 1000));

    const paletteVisible = await page.evaluate(() => {
      // Check for dialog/modal
      const dialogs = document.querySelectorAll('dialog, [role="dialog"], [data-state="open"], .cmdk-dialog');
      if (dialogs.length > 0) return true;
      // Check for command palette specific elements
      const cmdk = document.querySelector('[cmdk-root], [data-cmdk-root]');
      if (cmdk) return true;
      // Check for any new overlay/modal
      const overlays = document.querySelectorAll('[class*="overlay"], [class*="modal"], [class*="command"]');
      for (const o of overlays) {
        const style = window.getComputedStyle(o);
        if (style.display !== 'none' && style.visibility !== 'hidden') return true;
      }
      return false;
    });

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'CommandPalette.png') });

    results.push({
      name: 'Keyboard_CtrlK',
      path: '-',
      status: paletteVisible ? 'PASS' : 'FAIL',
      textLength: 0,
      jsErrors: 0,
      consoleErrors: 0,
      details: paletteVisible ? 'Command palette opened' : 'Command palette not detected after Ctrl+K',
      screenshot: 'CommandPalette.png',
    });
    log(`  ${paletteVisible ? 'PASS' : 'FAIL'}: Command palette ${paletteVisible ? 'opened' : 'not detected'}`);
  } catch (err) {
    results.push({ name: 'Keyboard_CtrlK', path: '-', status: 'FAIL', textLength: 0, jsErrors: 0, consoleErrors: 0, details: `Error: ${err.message.slice(0, 200)}`, screenshot: null });
    log(`  FAIL: ${err.message.slice(0, 100)}`);
  }
}

async function testResponsive(page) {
  log('Testing responsive layout (1024x768)...');
  try {
    await page.setViewport({ width: 1024, height: 768 });
    await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle2', timeout: 15000 });
    await new Promise(r => setTimeout(r, 3000));

    const bodyText = await page.evaluate(() => document.body?.innerText || '');
    const rendered = bodyText.length > 20;

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'Responsive_1024x768.png') });

    results.push({
      name: 'Responsive_1024x768',
      path: '-',
      status: rendered ? 'PASS' : 'FAIL',
      textLength: bodyText.length,
      jsErrors: 0,
      consoleErrors: 0,
      details: rendered ? `Renders at 1024x768 (${bodyText.length} chars)` : 'Page blank at 1024x768',
      screenshot: 'Responsive_1024x768.png',
    });
    log(`  ${rendered ? 'PASS' : 'FAIL'}: ${bodyText.length} chars at 1024x768`);

    // Reset viewport
    await page.setViewport({ width: 1280, height: 720 });
  } catch (err) {
    results.push({ name: 'Responsive_1024x768', path: '-', status: 'FAIL', textLength: 0, jsErrors: 0, consoleErrors: 0, details: `Error: ${err.message.slice(0, 200)}`, screenshot: null });
    log(`  FAIL: ${err.message.slice(0, 100)}`);
  }
}

async function main() {
  log('Starting Dashboard V6 Browser Tests');
  log('====================================');

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 720 });

  // Test all pages
  for (const pageInfo of PAGES) {
    await testPage(page, pageInfo);
  }

  // Additional tests
  await testDarkMode(page);
  await testKeyboard(page);
  await testResponsive(page);

  await browser.close();

  // Summary
  log('');
  log('====================================');
  log('RESULTS SUMMARY');
  log('====================================');

  const passed = results.filter(r => r.status === 'PASS').length;
  const failed = results.filter(r => r.status === 'FAIL').length;

  for (const r of results) {
    log(`${r.status === 'PASS' ? '✅' : '❌'} ${r.name.padEnd(20)} ${r.details}`);
  }

  log('');
  log(`Total: ${results.length} | PASS: ${passed} | FAIL: ${failed}`);

  // Write JSON results for report generation
  fs.writeFileSync(
    path.join(__dirname, 'browser_results.json'),
    JSON.stringify(results, null, 2)
  );
  log(`Results saved to tests/browser_results.json`);
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
