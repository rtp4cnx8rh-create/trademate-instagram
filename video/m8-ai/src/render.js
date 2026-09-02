const { chromium } = require('playwright-core');
const path = require('path');
const fs = require('fs');

(async () => {
  const lang = process.argv[2] || 'en';
  const mode = process.argv[3] || 'frames';   // 'frames' | 'preview'
  const outDir = path.resolve(__dirname, 'frames_' + lang);
  const FPS = 30, DUR = 15.0;
  fs.rmSync(outDir, { recursive: true, force: true });
  fs.mkdirSync(outDir, { recursive: true });

  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium',
    args: ['--force-device-scale-factor=1', '--font-render-hinting=none', '--disable-lcd-text']
  });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(__dirname, 'story.html') + '?lang=' + lang);
  await page.waitForTimeout(900);

  if (mode === 'preview') {
    for (const t of (process.argv[4] || '0.8,2.4,4.2,5.0,7.0,8.6,10.2,11.4,12.2,13.6,14.6').split(',')) {
      await page.evaluate((tt) => window.render(parseFloat(tt)), t);
      await page.screenshot({ path: path.join(outDir, 'p_' + t + '.png') });
    }
    await browser.close(); return;
  }

  const total = Math.round(DUR * FPS);
  for (let i = 0; i < total; i++) {
    const t = i / FPS;
    await page.evaluate((tt) => window.render(tt), t);
    await page.screenshot({ path: path.join(outDir, String(i).padStart(4, '0') + '.png') });
    if (i % 60 === 0) process.stdout.write(i + '/' + total + ' ');
  }
  await browser.close();
  console.log('\ndone ' + total + ' frames -> ' + outDir);
})();
