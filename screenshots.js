const { chromium } = require('playwright');
const path = require('path');

const SCREENSHOTS_DIR = path.join(__dirname, 'screenshots');
const BASE_URL = 'http://127.0.0.1:8420';

async function takeScreenshots() {
    const browser = await chromium.launch();
    const context = await browser.newContext({
        viewport: { width: 1400, height: 900 },
        deviceScaleFactor: 2, // Retina quality
    });
    const page = await context.newPage();

    // Create screenshots directory
    const fs = require('fs');
    if (!fs.existsSync(SCREENSHOTS_DIR)) {
        fs.mkdirSync(SCREENSHOTS_DIR);
    }

    console.log('Loading app...');
    await page.goto(BASE_URL);
    await page.waitForSelector('.theme-card', { timeout: 10000 });
    await page.waitForTimeout(1000); // Let images load

    // Screenshot 1: Installed themes (main view)
    console.log('Capturing installed themes...');
    await page.screenshot({
        path: path.join(SCREENSHOTS_DIR, '01-installed-themes.png'),
        fullPage: false,
    });

    // Screenshot 2: Available themes
    console.log('Capturing available themes...');
    await page.click('[data-filter="available"]');
    await page.waitForTimeout(800);
    await page.screenshot({
        path: path.join(SCREENSHOTS_DIR, '02-available-themes.png'),
        fullPage: false,
    });

    // Screenshot 3: Dark mode filter
    console.log('Capturing dark mode filter...');
    await page.click('[data-filter="all"]');
    await page.waitForTimeout(300);
    await page.click('[data-mode="dark"]');
    await page.waitForTimeout(500);
    await page.screenshot({
        path: path.join(SCREENSHOTS_DIR, '03-dark-themes.png'),
        fullPage: false,
    });

    // Screenshot 4: Light mode filter
    console.log('Capturing light mode filter...');
    await page.click('[data-mode="light"]');
    await page.waitForTimeout(500);
    await page.screenshot({
        path: path.join(SCREENSHOTS_DIR, '04-light-themes.png'),
        fullPage: false,
    });

    // Screenshot 5: Search functionality
    console.log('Capturing search...');
    await page.click('[data-mode="all"]');
    await page.click('[data-filter="installed"]');
    await page.waitForTimeout(300);
    await page.fill('#search', 'tokyo');
    await page.waitForTimeout(500);
    await page.screenshot({
        path: path.join(SCREENSHOTS_DIR, '05-search.png'),
        fullPage: false,
    });

    // Screenshot 6: Install modal (trigger on available theme)
    console.log('Capturing install modal...');
    await page.fill('#search', '');
    await page.click('[data-filter="available"]');
    await page.waitForTimeout(800);

    // Show the install modal by injecting it directly (don't actually install)
    await page.evaluate(() => {
        const modal = document.getElementById('install-modal');
        document.getElementById('modal-title').textContent = 'Installing Theme';
        document.getElementById('modal-subtitle').textContent = 'dracula';
        document.getElementById('modal-icon').className = 'modal-icon installing';
        document.getElementById('modal-icon').textContent = '📦';
        document.getElementById('modal-close').disabled = true;
        document.getElementById('modal-error').style.display = 'none';

        // Set steps to show progress
        const steps = document.querySelectorAll('.step');
        steps[0].className = 'step complete';
        steps[0].querySelector('.step-icon').textContent = '✓';
        steps[1].className = 'step complete';
        steps[1].querySelector('.step-icon').textContent = '✓';
        steps[2].className = 'step active';
        steps[2].querySelector('.step-icon').textContent = '⟳';
        steps[3].className = 'step';

        modal.classList.add('show');
    });
    await page.waitForTimeout(500);
    await page.screenshot({
        path: path.join(SCREENSHOTS_DIR, '06-install-modal.png'),
        fullPage: false,
    });
    // Close modal
    await page.evaluate(() => {
        document.getElementById('install-modal').classList.remove('show');
    });
    await page.waitForTimeout(300);

    // Screenshot 7: Scrolled view with back-to-top button
    console.log('Capturing back-to-top button...');
    await page.click('[data-filter="installed"]');
    await page.waitForTimeout(500);
    await page.evaluate(() => window.scrollTo(0, 800));
    await page.waitForTimeout(500);
    await page.screenshot({
        path: path.join(SCREENSHOTS_DIR, '07-back-to-top.png'),
        fullPage: false,
    });

    await browser.close();
    console.log(`\nScreenshots saved to ${SCREENSHOTS_DIR}/`);
}

takeScreenshots().catch(console.error);
