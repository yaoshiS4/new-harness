#!/usr/bin/env node
/* UI states on the key screens (anti-slop M-03): `/` with the auth modal open, /vi-tien,
 * /vip, /cua-hang and /bo-suu-tap at m375 and d1440. Captures default, hover,
 * focus-visible, active, disabled, loading, empty, error, plus "tạm dừng" (stale money).
 * A state the mock cannot reach is written to the manifest as `unreachable: <reason>`,
 * never skipped silently; a state that throws is `failed: <reason>` and fails the run.
 *
 * Usage: STATES_OUT=<dir> node scripts/with-dev-server.mjs --port <p> -- node .unlazy/yaobet-ds/checks/states.mjs
 * Writes <dir>/<viewport>-<route>-<state>.jpg, manifest.json and manifest.txt; prints `STATES DONE n`. */

import fs from "node:fs";
import path from "node:path";
import { chromium } from "playwright";

if (process.argv.length > 2) { console.error(`states: unknown argument ${process.argv[2]}`); process.exit(1); }
const BASE = (process.env.BASE ?? "").replace(/\/+$/, "");
if (!BASE) { console.error("states: BASE is not set (run under scripts/with-dev-server.mjs)"); process.exit(1); }
const OUT = process.env.STATES_OUT ?? "/tmp/yb-ds-states";
fs.mkdirSync(OUT, { recursive: true });

const ROUTES = [
  { path: "/", modal: true },
  { path: "/vi-tien" },
  { path: "/vip" },
  { path: "/cua-hang" },
  { path: "/bo-suu-tap" },
];
const VIEWPORTS = [{ name: "m375", width: 375, height: 812 }, { name: "d1440", width: 1440, height: 900 }];
const STATES = ["default", "hover", "focus-visible", "active", "disabled", "loading", "empty", "error", "tam-dung"];
const slug = (r) => (r === "/" ? "home" : r.slice(1).replace(/\//g, "__"));
const INTERACTIVE = 'button:not([disabled]):not([aria-disabled="true"]), a[href], [role="tab"], input:not([disabled])';
const manifest = [];

async function goto(p, route) {
  await p.goto(BASE + route, { waitUntil: "networkidle", timeout: 120000 });
  await p.waitForTimeout(600);
}
/* The DEV toggle, driven as scripts/auth-flow.mjs drives it. */
async function setAuth(p, label) {
  await p.getByRole("button", { name: /chuyển trạng thái đăng nhập/ }).click();
  const cycle = p.locator('button[class*="cycle"]').first();
  const cur = cycle.locator('[class*="stateLabel"]');
  for (let i = 0; i < 4 && (await cur.innerText()).trim() !== label; i++) { await cycle.click(); await p.waitForTimeout(250); }
  const got = (await cur.innerText()).trim();
  await p.getByRole("group", { name: /Trạng thái đăng nhập/ }).getByRole("button", { name: "Đóng" }).click();
  await p.waitForTimeout(300);
  if (got !== label) throw new Error(`DEV toggle reads ${got}, expected ${label}`);
}
async function openModal(p) {
  await setAuth(p, "Khách");
  await p.locator("header").getByRole("button", { name: "Đăng nhập", exact: true }).first().evaluate((el) => el.click());
  const dialog = p.getByRole("dialog").first();
  await dialog.waitFor({ state: "visible", timeout: 10000 });
  return dialog;
}
/* Load the route; `/` opens the auth modal. Returns the locator the states act inside. */
async function prepare(p, r) {
  await goto(p, r.path);
  if (r.modal) return openModal(p);
  return p.locator("main").first();
}
async function firstVisible(loc) {
  const n = Math.min(await loc.count(), 60);
  for (let i = 0; i < n; i++) { const el = loc.nth(i); if (await el.isVisible()) return el; }
  return null;
}
async function shot(p, vp, r, state, detail) {
  const file = `${vp.name}-${slug(r.path)}-${state}.jpg`;
  await p.screenshot({ path: path.join(OUT, file), type: "jpeg", quality: 72 });
  manifest.push({ viewport: vp.name, route: r.path, state, file, detail: detail ?? "" });
}
const unreachable = (vp, r, state, reason) => manifest.push({ viewport: vp.name, route: r.path, state, unreachable: reason });
/* A transient state counts only when its locator is still visible after the screenshot; otherwise the file is removed. */
async function heldShot(p, vp, r, state, loc, detail) {
  const file = `${vp.name}-${slug(r.path)}-${state}.jpg`;
  await p.screenshot({ path: path.join(OUT, file), type: "jpeg", quality: 72 });
  if (await loc.isVisible().catch(() => false)) {
    manifest.push({ viewport: vp.name, route: r.path, state, file, detail: detail ?? "" });
    return true;
  }
  await (await import("node:fs/promises")).rm(path.join(OUT, file), { force: true });
  return false;
}
/* Fill the visible inputs of a form with demo values so its submit runs. */
async function fillVisible(scope) {
  const inputs = scope.locator("input:visible");
  const n = Math.min(await inputs.count(), 12);
  for (let i = 0; i < n; i++) {
    const el = inputs.nth(i);
    const t = (await el.getAttribute("type")) ?? "text";
    if (t === "checkbox") await el.check().catch(() => null);
    else if (t === "email") await el.fill("demo@example.com");
    else if (t === "tel") await el.fill("0900000000");
    else if (t === "password") await el.fill("Demo12345");
    else if (t !== "hidden" && t !== "submit") await el.fill("demo01");
  }
}

/* Hold every RSC request while a client navigation to the route renders its loading boundary. */
async function loadingState(p, vp, r) {
  const from = r.path === "/" ? "/vip" : "/";
  await goto(p, from);
  const held = [];
  let seen = false;
  await p.route("**/*", (route) => {
    const q = route.request();
    if (q.headers()["rsc"] === "1" || q.url().includes("_rsc=")) held.push(route);
    else route.continue();
  });
  try {
    await p.evaluate((to) => window.next.router.push(to), r.path);
    const busy = p.locator('[aria-busy="true"], .ui-skeleton').first();
    seen = await busy.waitFor({ state: "visible", timeout: 4000 }).then(() => true, () => false);
    if (seen) { await busy.scrollIntoViewIfNeeded(); await shot(p, vp, r, "loading", `client navigation from ${from}, RSC held`); }
  } finally {
    await p.unroute("**/*");
    for (const h of held) await h.continue().then(() => null, () => null);
  }
  if (seen) return;
  /* Client-side loaders render after mount, so a hard load is watched from its first commit. */
  for (let i = 0; i < 3; i++) {
    await p.goto(BASE + r.path, { waitUntil: "commit", timeout: 120000 });
    const mounted = p.locator('[aria-busy="true"], .ui-skeleton').or(p.getByText(/Đang tải/)).first();
    if (!(await mounted.waitFor({ state: "visible", timeout: 8000 }).then(() => true, () => false))) break;
    if (await heldShot(p, vp, r, "loading", mounted, "hard load, client loader before data")) return;
  }
  unreachable(vp, r, "loading", `no aria-busy, skeleton or "Đang tải" stayed on screen: client navigation from ${from} with the RSC payload held, then up to 3 hard loads`);
}

async function errorState(p, vp, r, scope) {
  const shown = await firstVisible(scope.locator('.ui-error, [role="alert"]'));
  if (shown) { await shown.scrollIntoViewIfNeeded(); return shot(p, vp, r, "error", "ErrorState or alert rendered by the mock"); }
  if (r.modal) {
    const submit = await firstVisible(scope.locator('button[type="submit"]'));
    if (submit) {
      await submit.click();
      await p.waitForTimeout(500);
      const invalid = await firstVisible(scope.locator('[aria-invalid="true"], [role="alert"]'));
      if (invalid) return shot(p, vp, r, "error", "empty-form submit, field validation");
    }
    /* Register mode: fill every required field, give a mismatched confirm password, submit. */
    const toRegister = await firstVisible(scope.locator(".auth-modal-switch-btn"));
    if (toRegister) {
      await toRegister.click();
      await p.waitForTimeout(400);
      const dlg = p.getByRole("dialog").first();
      const pw = dlg.locator('input[type="password"]');
      if ((await pw.count()) >= 2) {
        const req = dlg.locator('input[required]:not([type="password"])');
        for (let i = 0; i < Math.min(await req.count(), 10); i++) {
          const el = req.nth(i);
          if (!(await el.isVisible())) continue;
          const t = (await el.getAttribute("type")) ?? "text";
          if (t === "checkbox") await el.check();
          else await el.fill(t === "email" ? "demo@example.com" : t === "tel" ? "0900000000" : "demo01");
        }
        await pw.nth(0).fill("Demo12345");
        await pw.nth(1).fill("Demo12346");
        const send = await firstVisible(dlg.locator('button[type="submit"]'));
        if (send) {
          await send.click();
          await p.waitForTimeout(500);
          const bad = await firstVisible(dlg.locator('[aria-invalid="true"], [role="alert"]'));
          if (bad) { await bad.scrollIntoViewIfNeeded(); return shot(p, vp, r, "error", "register, mismatched confirm password"); }
        }
      }
    }
    return unreachable(vp, r, "error", "neither the empty-form submit nor a mismatched register confirm password raised an aria-invalid field or alert");
  }
  /* Amount fields: an amount above the balance raises the field error. */
  const withdrawTab = await firstVisible(scope.getByRole("tab", { name: "Rút tiền" }));
  if (withdrawTab) { await withdrawTab.click(); await p.waitForTimeout(400); }
  const amount = await firstVisible(scope.locator('input[inputmode="numeric"], input[inputmode="decimal"], input[type="number"]'));
  if (amount) {
    await amount.fill("999999999999");
    await p.waitForTimeout(400);
    const bad = await firstVisible(scope.locator('[aria-invalid="true"], [role="alert"]'));
    if (bad) { await bad.scrollIntoViewIfNeeded(); return shot(p, vp, r, "error", "amount above the balance, field validation"); }
  }
  return unreachable(vp, r, "error", `the mock has no failing fetch on ${r.path} and no amount field raised a validation error; no ErrorState rendered`);
}

/* Stale money: a fast-forwarded clock pushes live values past their freshness window. */
async function pausedState(browser, vp, r) {
  const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: 1, reducedMotion: "reduce" });
  try {
    const p = await ctx.newPage();
    await p.clock.install();
    await goto(p, r.path);
    await p.clock.fastForward(120000);
    await p.waitForTimeout(800);
    const staleLoc = () => p.locator('[data-stale="true"]').or(p.getByText(/tạm dừng/i));
    let stale = await firstVisible(staleLoc());
    let how = "clock fast-forwarded 120 s";
    if (!stale) {
      /* Staleness is computed on render, so a tab switch re-renders the values after the fast-forward. */
      const tab = await firstVisible(p.locator('[role="tab"][aria-selected="false"]'));
      if (tab) { await tab.click(); await p.waitForTimeout(600); stale = await firstVisible(staleLoc()); how += ", then a tab switch re-rendered the values"; }
    }
    if (stale) { await stale.scrollIntoViewIfNeeded(); await shot(p, vp, r, "tam-dung", how); }
    else unreachable(vp, r, "tam-dung", `no live money value on ${r.path} turned "tạm dừng" after a 120 s clock fast-forward and a tab switch`);
  } finally {
    await ctx.close();
  }
}

async function run(browser, vp, r) {
  const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: 1, reducedMotion: "reduce" });
  const p = await ctx.newPage();
  const attempt = async (state, fn) => {
    try { await fn(); } catch (e) { manifest.push({ viewport: vp.name, route: r.path, state, failed: String(e.message).split("\n")[0] }); }
  };
  try {
    let scope = null;
    await attempt("default", async () => { scope = await prepare(p, r); await shot(p, vp, r, "default", r.modal ? "auth modal open (guest)" : ""); });
    if (!scope) { for (const s of STATES.slice(1, -1)) manifest.push({ viewport: vp.name, route: r.path, state: s, failed: "the route did not load" }); }
    else {
      await attempt("hover", async () => {
        const el = await firstVisible(scope.locator(INTERACTIVE));
        if (!el) return unreachable(vp, r, "hover", "no visible interactive element");
        await el.scrollIntoViewIfNeeded(); await el.hover(); await p.waitForTimeout(250);
        await shot(p, vp, r, "hover", (await el.innerText().catch(() => "")).slice(0, 40));
        await p.mouse.move(0, 0);
      });
      await attempt("focus-visible", async () => {
        let hit = false;
        for (let i = 0; i < 40 && !hit; i++) {
          await p.keyboard.press("Tab");
          hit = await scope.evaluate((root) => { const a = document.activeElement; return !!a && root.contains(a) && a.matches(":focus-visible"); });
        }
        if (!hit) return unreachable(vp, r, "focus-visible", "no :focus-visible element inside the screen after 40 Tab presses");
        await shot(p, vp, r, "focus-visible", await p.evaluate(() => document.activeElement?.tagName ?? ""));
      });
      await attempt("active", async () => {
        const el = await firstVisible(scope.locator('button:not([disabled]):not([aria-disabled="true"])'));
        if (!el) return unreachable(vp, r, "active", "no enabled button");
        await el.scrollIntoViewIfNeeded(); await el.hover(); await p.mouse.down(); await p.waitForTimeout(150);
        await shot(p, vp, r, "active", (await el.innerText().catch(() => "")).slice(0, 40));
        await p.mouse.move(0, 0); await p.mouse.up();
      });
      await attempt("disabled", async () => {
        const DIS = 'button[disabled], [aria-disabled="true"], input[disabled], select[disabled]';
        let el = await firstVisible(scope.locator(DIS));
        if (!el && !r.modal) {
          const tab = scope.getByRole("tab", { name: /Rút tiền/ });
          if (await tab.count()) { await tab.first().click(); await p.waitForTimeout(500); el = await firstVisible(scope.locator(DIS)); }
          if (el) { await el.scrollIntoViewIfNeeded(); return shot(p, vp, r, "disabled", "withdraw tab, " + (await el.innerText().catch(() => "")).slice(0, 40)); }
        }
        /* The auth modal's forgot-password submit is disabled while in flight. On `/` it runs in the open modal; a route
         * with no disabled control of its own opens the modal in a fresh context, so the guest toggle does not leak. */
        const forgotBusy = async (pg, dialog, detail) => {
          const forgot = dialog.getByRole("button", { name: /Quên mật khẩu/i }).or(dialog.getByRole("link", { name: /Quên mật khẩu/i })).first();
          if (!(await forgot.count())) return false;
          await forgot.click(); await pg.waitForTimeout(400);
          await fillVisible(dialog);
          await dialog.locator('button[type="submit"]').first().click({ noWaitAfter: true });
          const busy = dialog.locator(DIS).first();
          return (await busy.waitFor({ state: "visible", timeout: 400 }).then(() => true, () => false))
            && await heldShot(pg, vp, r, "disabled", busy, detail);
        };
        if (!el && r.modal && await forgotBusy(p, scope, "forgot-password submit in flight")) return;
        if (!el && !r.modal) {
          const c2 = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: 1, reducedMotion: "reduce" });
          try {
            const p2 = await c2.newPage();
            /* The DEV auth toggle lives on `/` and the session is in memory, so set guest there and reach the route by a client-side link. */
            await goto(p2, "/");
            await setAuth(p2, "Khách");
            await p2.locator(`a[href="${r.path}"]`).first().evaluate((el) => el.click());
            await p2.waitForURL((u) => u.pathname === r.path, { timeout: 30000 });
            await p2.waitForLoadState("networkidle"); await p2.waitForTimeout(600);
            await p2.locator("header").getByRole("button", { name: "Đăng nhập", exact: true }).first().evaluate((el) => el.click());
            const dialog = p2.getByRole("dialog").first();
            await dialog.waitFor({ state: "visible", timeout: 10000 });
            if (await forgotBusy(p2, dialog, `auth modal forgot-password submit in flight, opened from ${r.path} after a client-side visit as guest`)) return;
          } finally { await c2.close(); }
        }
        if (!el) return unreachable(vp, r, "disabled", `no disabled control on ${r.path}, after the withdraw tab and the forgot-password submit were tried`);
        await el.scrollIntoViewIfNeeded(); await shot(p, vp, r, "disabled", (await el.innerText().catch(() => "")).slice(0, 40));
      });
      await attempt("empty", async () => {
        const el = await firstVisible(scope.locator(".ui-empty"));
        if (!el) return unreachable(vp, r, "empty", `the mock returns data for every list on ${r.path}; no EmptyState rendered`);
        await el.scrollIntoViewIfNeeded(); await shot(p, vp, r, "empty", "");
      });
      /* The disabled probe can leave the auth modal mid-submit, so the error probe starts from a fresh modal. */
      await attempt("error", async () => { if (r.modal) scope = await prepare(p, r); return errorState(p, vp, r, scope); });
      await attempt("loading", () => loadingState(p, vp, r));
    }
    await attempt("tam-dung", () => pausedState(browser, vp, r));
  } finally {
    await ctx.close();
  }
}

const browser = await chromium.launch();
try {
  for (const vp of VIEWPORTS) for (const r of ROUTES) { await run(browser, vp, r); console.log(`[states] ${vp.name} ${r.path} done`); }
} finally {
  await browser.close();
}

const line = (m) => `${m.viewport} ${m.route} ${m.state}: ${m.file ?? (m.unreachable ? `unreachable: ${m.unreachable}` : `failed: ${m.failed}`)}`;
fs.writeFileSync(path.join(OUT, "manifest.json"), JSON.stringify(manifest, null, 1) + "\n");
fs.writeFileSync(path.join(OUT, "manifest.txt"), manifest.map(line).join("\n") + "\n");
for (const m of manifest) console.log(line(m));
const expected = VIEWPORTS.length * ROUTES.length * STATES.length;
const captured = manifest.filter((m) => m.file).length;
const failed = manifest.filter((m) => m.failed).length;
const keys = new Set(manifest.map((m) => `${m.viewport} ${m.route} ${m.state}`));
if (failed || keys.size !== expected) {
  console.log(`Fail: states | Expected: ${expected} rows, none failed | Got: ${keys.size} rows, ${failed} failed`);
  console.log(`STATES FAILED ${captured}`);
  process.exit(1);
}
console.log(`STATES DONE ${captured}`);
