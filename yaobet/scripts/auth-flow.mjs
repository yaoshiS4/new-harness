#!/usr/bin/env node
/* auth-flow: the mock-auth journey on $BASE.
 *
 * Usage:  BASE=http://localhost:<p> node scripts/auth-flow.mjs
 *
 * 1. a fresh load is tiered (MemberMenu meta "Bạch Kim · YB-880066");
 * 2. DEV toggle to guest, "Đăng ký", submit -> level-0 ("Tân thủ · YB-668812");
 * 3. guest, "Đăng nhập", submit -> tiered;
 * 4. reload -> tiered;
 * 5. Escape closes the auth modal and focus returns to its trigger.
 * Prints `AUTH FLOW OK 5/5`. */

import { chromium } from "playwright";

const TIERED = "Bạch Kim · YB-880066";
const LEVEL0 = "Tân thủ · YB-668812";

if (process.argv.length > 2) {
  console.error(`auth-flow: unknown argument ${process.argv[2]}`);
  process.exit(1);
}
const BASE = (process.env.BASE ?? "").replace(/\/+$/, "");
if (!BASE) {
  console.error("auth-flow: BASE is not set (run under scripts/with-dev-server.mjs)");
  process.exit(1);
}

/* The DEV toggle, driven exactly as the screenshot recipe drives it. */
async function setState(p, label) {
  await p.getByRole("button", { name: /chuyển trạng thái đăng nhập/ }).click();
  const cycle = p.locator('button[class*="cycle"]').first();
  const cur = cycle.locator('[class*="stateLabel"]');
  for (let i = 0; i < 4 && (await cur.innerText()).trim() !== label; i++) {
    await cycle.click();
    await p.waitForTimeout(250);
  }
  const got = (await cur.innerText()).trim();
  await p.getByRole("group", { name: /Trạng thái đăng nhập/ }).getByRole("button", { name: "Đóng" }).click();
  await p.waitForTimeout(300);
  if (got !== label) throw new Error(`DEV toggle reads ${got}, expected ${label}`);
}

/* The MemberMenu meta line ("<tier> · <member id>"), or null for guest chrome. */
async function memberMeta(p) {
  const trigger = p.locator('header button[aria-haspopup="menu"]').first();
  if ((await trigger.count()) === 0) return null;
  await trigger.evaluate((el) => el.click());
  const menu = p.locator('[role="menu"]').first();
  await menu.waitFor({ state: "attached", timeout: 5000 });
  const text = (await menu.innerText()).replace(/\s+/g, " ");
  await p.keyboard.press("Escape");
  const m = text.match(/[^\s·]+(?: [^\s·]+)? · YB-\d+/);
  return m ? m[0] : text.slice(0, 80);
}

async function openAuth(p, name) {
  const trigger = p.locator("header").getByRole("button", { name, exact: true }).first();
  await trigger.evaluate((el) => el.click());
  const dialog = p.getByRole("dialog").first();
  await dialog.waitFor({ state: "visible", timeout: 10000 });
  return { trigger, dialog };
}

async function fillAndSubmit(dialog, submitName) {
  for (const input of await dialog.locator("input[required]").all()) {
    const type = (await input.getAttribute("type")) ?? "text";
    await input.fill(type === "password" ? "matkhau123" : type === "tel" ? "0901234567" : "thanhvien01");
  }
  await dialog.locator('button[type="submit"]').filter({ hasText: submitName }).first().click();
  await dialog.waitFor({ state: "hidden", timeout: 10000 });
}

const results = [];
const step = async (name, fn) => {
  try {
    const detail = await fn();
    results.push(true);
    console.log(`ok ${results.length} ${name}${detail ? ": " + detail : ""}`);
  } catch (e) {
    results.push(false);
    console.error(`Fail: ${name} | ${e.message.split("\n")[0]}`);
  }
};
const expectMeta = async (p, want) => {
  const got = await memberMeta(p);
  if (got !== want) throw new Error(`Expected: ${want} | Got: ${got ?? "guest chrome"}`);
  return got;
};

const browser = await chromium.launch();
try {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1, reducedMotion: "reduce" });
  const p = await ctx.newPage();
  await p.goto(BASE + "/", { waitUntil: "networkidle", timeout: 120000 });
  await p.waitForTimeout(800);

  await step("fresh load is tiered", () => expectMeta(p, TIERED));
  await step("guest -> Đăng ký -> level-0", async () => {
    await setState(p, "Khách");
    const { dialog } = await openAuth(p, "Đăng ký");
    await fillAndSubmit(dialog, "Đăng ký");
    return expectMeta(p, LEVEL0);
  });
  await step("guest -> Đăng nhập -> tiered", async () => {
    await setState(p, "Khách");
    const { dialog } = await openAuth(p, "Đăng nhập");
    await fillAndSubmit(dialog, "Đăng nhập");
    return expectMeta(p, TIERED);
  });
  await step("reload is tiered", async () => {
    await p.reload({ waitUntil: "networkidle", timeout: 120000 });
    await p.waitForTimeout(800);
    return expectMeta(p, TIERED);
  });
  await step("Escape closes the modal, focus returns to the trigger", async () => {
    await setState(p, "Khách");
    const trigger = p.locator("header").getByRole("button", { name: "Đăng nhập", exact: true }).first();
    await trigger.focus();
    await p.keyboard.press("Enter");
    const dialog = p.getByRole("dialog").first();
    await dialog.waitFor({ state: "visible", timeout: 10000 });
    await p.keyboard.press("Escape");
    await dialog.waitFor({ state: "hidden", timeout: 10000 });
    await p.waitForTimeout(200);
    const back = await trigger.evaluate((el) => el === document.activeElement);
    if (!back) throw new Error("Expected: focus on the Đăng nhập trigger | Got: " + (await p.evaluate(() => document.activeElement?.outerHTML.slice(0, 80))));
    return "focus restored";
  });
  await ctx.close();
} finally {
  await browser.close();
}

const passed = results.filter(Boolean).length;
if (passed === 5) {
  console.log("AUTH FLOW OK 5/5");
  process.exit(0);
}
console.error(`AUTH FLOW FAILED ${passed}/5`);
process.exit(1);
