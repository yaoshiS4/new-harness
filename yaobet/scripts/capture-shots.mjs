import fs from 'fs';
import { chromium } from 'playwright';

if (process.argv.length > 2) { console.error(`capture-shots: unknown argument ${process.argv[2]}`); process.exit(1); }

const BASE = 'http://localhost:3107';
const OUT = process.env.SHOTS_OUT ?? './.shots';
fs.mkdirSync(OUT, { recursive: true });
const MASKS = JSON.parse(fs.readFileSync(new URL('../.unlazy/yaobet-rebuild/checks/shot-masks.json', import.meta.url), 'utf8')).selectors;
const ALL = ['/', '/casino', '/slots', '/sports', '/khuyen-mai', '/khuyen-mai/pr1',
  '/tai-khoan', '/vi-tien', '/tin-nhan', '/gioi-thieu', '/dai-ly', '/bao-mat',
  '/vip', '/tier', '/cau-lac-bo', '/cua-hang', '/ve-so', '/bo-suu-tap', '/bo-suu-tap/cua-toi',
  '/cuoc-hop-le', '/game-han-che', '/hoan-tra', '/lich-su', '/ho-tro', '/tro-giup',
  '/tai-app', '/phong-cach', '/dev/collection-ports'];
const GUEST = ['/', '/khuyen-mai', '/tai-khoan', '/vi-tien', '/vip', '/cua-hang', '/ve-so', '/gioi-thieu'];
const PLAN = [{ state: 'tiered', label: 'Hội viên', routes: ALL }, { state: 'guest', label: 'Khách', routes: GUEST }];
const VIEWPORTS = [{ name: 'm375', width: 375, height: 812 }, { name: 'd1440', width: 1440, height: 900 }];
const slug = (r) => (r === '/' ? 'home' : r.slice(1).replace(/\//g, '__'));
const log = (...a) => console.log('[shots]', ...a);

async function setState(p, label) {
  await p.goto(BASE + '/', { waitUntil: 'networkidle', timeout: 60000 });
  await p.waitForTimeout(800);
  await p.getByRole('button', { name: /chuyển trạng thái đăng nhập/ }).click();
  const cycle = p.locator('button[class*="cycle"]').first();
  const cur = cycle.locator('[class*="stateLabel"]');
  for (let i = 0; i < 4 && (await cur.innerText()).trim() !== label; i++) { await cycle.click(); await p.waitForTimeout(250); }
  const got = (await cur.innerText()).trim();
  if (got !== label) throw new Error(`state ${got} != ${label}`);
  await p.getByRole('group', { name: /Trạng thái đăng nhập/ }).getByRole('button', { name: 'Đóng' }).click();
  await p.waitForTimeout(300);
  return got;
}

async function checkState(p, label) {
  await p.evaluate(() => window.next.router.push('/'));
  await p.waitForURL((u) => u.pathname === '/', { timeout: 30000 });
  await p.waitForTimeout(600);
  await p.getByRole('button', { name: /chuyển trạng thái đăng nhập/ }).click();
  const got = (await p.locator('[class*="stateLabel"]').first().innerText()).trim();
  await p.getByRole('group', { name: /Trạng thái đăng nhập/ }).getByRole('button', { name: 'Đóng' }).click();
  return got === label ? 'ok' : `DRIFT ${got}`;
}

/* A viewport point with nothing interactive under it, scanned on a coarse grid
 * from the bottom-right (away from the top nav). */
function idlePoint() {
  const interactive = ['a', 'button', 'input', 'select', 'textarea', 'label', 'summary', '[onclick]',
    '[tabindex]:not([tabindex="-1"])', '.shell-nav-dropdown-wrap',
    ...['button', 'link', 'tab', 'menuitem', 'option', 'checkbox', 'radio', 'switch', 'slider'].map((r) => `[role="${r}"]`)].join(', ');
  const w = window.innerWidth;
  const h = window.innerHeight;
  for (let fy = 0.9; fy >= 0.3; fy -= 0.1) {
    for (let fx = 0.98; fx >= 0.02; fx -= 0.04) {
      const x = Math.round(w * fx);
      const y = Math.round(h * fy);
      const el = document.elementFromPoint(x, y);
      if (el && !el.closest(interactive)) return { x, y };
    }
  }
  return { x: w - 1, y: h - 1 };
}

/* Park the pointer off every interactive element and drop focus from the nav,
 * then wait until no nav dropdown panel is open (they open on hover and focus). */
async function settlePointer(p) {
  await p.evaluate(() => {
    const a = document.activeElement;
    if (a && a.closest && a.closest('.shell-nav-dropdown-wrap') && a.blur) a.blur();
  });
  const pt = await p.evaluate(idlePoint);
  await p.mouse.move(pt.x, pt.y);
  await p.waitForFunction(() => document.querySelectorAll('.shell-nav-dropdown-panel').length === 0, null, { timeout: 5000 });
  await p.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))));
}

/* Boxes of the mask selectors in full-page coordinates. Fixed boxes anchored to
 * the bottom are placed where a full-page capture draws them (page bottom). */
function maskBoxes(selectors) {
  const docH = Math.max(document.documentElement.scrollHeight, document.body ? document.body.scrollHeight : 0);
  const fixedOf = (el) => {
    for (let n = el; n && n.nodeType === 1; n = n.parentElement || (n.getRootNode && n.getRootNode().host)) {
      const cs = getComputedStyle(n);
      if (cs.position === 'fixed') return cs;
    }
    return null;
  };
  const boxOf = (el) => {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return null;
    const fixed = fixedOf(el);
    let y = r.top + window.scrollY;
    if (fixed) y = fixed.bottom !== 'auto' && fixed.top === 'auto' ? docH - (window.innerHeight - r.top) : r.top;
    return { x: r.left + window.scrollX, y, width: r.width, height: r.height };
  };
  const out = [];
  for (const selector of selectors) {
    for (const el of document.querySelectorAll(selector)) {
      const targets = el.shadowRoot ? [...el.shadowRoot.querySelectorAll('*')] : [el];
      for (const t of targets) {
        const b = boxOf(t);
        if (b) out.push({ selector, ...b });
      }
    }
  }
  return out;
}

const b = await chromium.launch();
const manifest = [];
try {
  for (const vp of VIEWPORTS) {
    for (const plan of PLAN) {
      const ctx = await b.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: 1, reducedMotion: 'reduce' });
      const p = await ctx.newPage();
      log(vp.name, 'state set:', await setState(p, plan.label));
      for (const r of plan.routes) {
        try {
          await p.evaluate((route) => window.next.router.push(route), r);
          await p.waitForURL((u) => u.pathname === r, { timeout: 20000 }).catch(() => {});
          await p.waitForLoadState('networkidle', { timeout: 60000 });
          await p.waitForTimeout(1800);
          const file = `${vp.name}-${plan.state}-${slug(r)}.jpg`;
          await settlePointer(p);
          await p.screenshot({ path: `${OUT}/${file}`, fullPage: true, type: 'jpeg', quality: 72 });
          const masks = await p.evaluate(maskBoxes, MASKS);
          manifest.push({ route: r, state: plan.state, viewport: vp.name, file, landed: new URL(p.url()).pathname + new URL(p.url()).search, masks });
          log('saved', file, '->', p.url());
        } catch (e) { log('FAIL', vp.name, plan.state, r, e.message); }
      }
      log(vp.name, plan.state, 'final check:', await checkState(p, plan.label));
      await ctx.close();
    }
  }
} finally {
  await b.close();
  fs.writeFileSync(`${OUT}/manifest.json`, JSON.stringify(manifest, null, 2));
  log('DONE', manifest.length);
}
