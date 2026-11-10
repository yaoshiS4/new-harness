#!/usr/bin/env node
/* with-dev-server: run one command against a fresh Next server on its own port.
 *
 * Usage:  node scripts/with-dev-server.mjs --port <p> [--mode dev|start] -- <cmd...>
 *         node scripts/with-dev-server.mjs --self-test
 *
 * Refuses a busy port (exit 1). Starts `next dev -p <p>` (or `next start -p <p>`,
 * which needs .next/BUILD_ID) as its own process group, logs to
 * /tmp/yb-server-<p>.log, waits up to 120 s for any HTTP response, runs the
 * command with BASE=http://localhost:<p>, then stops the group and waits until
 * the port is free. Exits with the command's code, or 3 with FONT FALLBACK when
 * the server log shows a Google Fonts download fallback. */

import { spawn } from "node:child_process";
import { closeSync, existsSync, openSync, readFileSync } from "node:fs";
import { createRequire } from "node:module";
import net from "node:net";
import path from "node:path";

const require = createRequire(import.meta.url);
const READY_MS = 120000;
const FONT_FALLBACK = /Failed to download[\s\S]*?Using fallback font instead/;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/* True when something accepts TCP connections on the port (IPv4 or IPv6 loopback). */
function connects(port, host) {
  return new Promise((resolve) => {
    const s = net.connect({ port, host });
    const done = (v) => {
      s.destroy();
      resolve(v);
    };
    s.setTimeout(1000, () => done(false));
    s.once("connect", () => done(true));
    s.once("error", () => done(false));
  });
}

async function portBusy(port) {
  return (await connects(port, "127.0.0.1")) || (await connects(port, "::1"));
}

async function waitHttp(port, ms) {
  const until = Date.now() + ms;
  while (Date.now() < until) {
    try {
      const res = await fetch(`http://localhost:${port}/`, {
        redirect: "manual",
        signal: AbortSignal.timeout(Math.max(1000, until - Date.now())),
      });
      await res.arrayBuffer().catch(() => {});
      return true;
    } catch {
      await sleep(500);
    }
  }
  return false;
}

function killGroup(child, signal) {
  try {
    process.kill(-child.pid, signal);
  } catch {}
}

async function stopServer(child, port) {
  if (child.exitCode === null) killGroup(child, "SIGTERM");
  for (let i = 0; i < 60; i++) {
    if (!(await portBusy(port)) && (child.exitCode !== null || child.signalCode !== null)) return true;
    if (i === 20) killGroup(child, "SIGKILL");
    await sleep(500);
  }
  killGroup(child, "SIGKILL");
  return !(await portBusy(port));
}

function runCommand(cmd, env) {
  return new Promise((resolve) => {
    const c = spawn(cmd[0], cmd.slice(1), { stdio: "inherit", env });
    c.once("error", (e) => {
      console.error(`with-dev-server: cannot run ${cmd[0]}: ${e.message}`);
      resolve(127);
    });
    c.once("exit", (code, signal) => resolve(code ?? (signal ? 128 : 1)));
  });
}

/**
 * Core driver. `server` is [file, ...args] for the server process (the default
 * is the installed next binary); the self-test passes a stub instead.
 */
export async function withServer({ port, mode = "dev", cmd, server, cwd = process.cwd(), quiet = false }) {
  const say = (m) => {
    if (!quiet) console.error(`with-dev-server: ${m}`);
  };
  if (await portBusy(port)) {
    say(`port ${port} is already bound`);
    return 1;
  }
  if (mode === "start" && !existsSync(path.join(cwd, ".next", "BUILD_ID"))) {
    say("--mode start needs .next/BUILD_ID (run next build first)");
    return 1;
  }
  const argv = server ?? [require.resolve("next/dist/bin/next"), mode, "-p", String(port)];
  const logFile = `/tmp/yb-server-${port}.log`;
  const fd = openSync(logFile, "w");
  const child = spawn(process.execPath, argv, { cwd, detached: true, stdio: ["ignore", fd, fd], env: process.env });
  closeSync(fd);
  const onSignal = () => {
    killGroup(child, "SIGKILL");
    process.exit(130);
  };
  process.once("SIGINT", onSignal);
  process.once("SIGTERM", onSignal);
  let code;
  try {
    if (!(await waitHttp(port, READY_MS))) {
      say(`no HTTP response on port ${port} within ${READY_MS / 1000} s (log: ${logFile})`);
      code = 1;
    } else {
      say(`server ready on port ${port} (log: ${logFile})`);
      code = await runCommand(cmd, { ...process.env, BASE: `http://localhost:${port}` });
    }
  } finally {
    const freed = await stopServer(child, port);
    process.removeListener("SIGINT", onSignal);
    process.removeListener("SIGTERM", onSignal);
    if (!freed) {
      say(`port ${port} still bound after stopping the server`);
      code = code || 1;
    }
  }
  const log = existsSync(logFile) ? readFileSync(logFile, "utf8") : "";
  if (FONT_FALLBACK.test(log)) {
    console.error("FONT FALLBACK: the server could not download a Google font and used a local fallback");
    return 3;
  }
  return code;
}

async function freePort() {
  return new Promise((resolve) => {
    const s = net.createServer();
    s.listen(0, "127.0.0.1", () => {
      const { port } = s.address();
      s.close(() => resolve(port));
    });
  });
}

async function selfTest() {
  const stub = [
    "-e",
    "require('http').createServer((q,s)=>{s.end('stub')}).listen(Number(process.argv[1]))",
  ];
  let ok = 0;
  const port = await freePort();

  const probe = "process.exit(process.env.BASE === 'http://localhost:' + process.argv[1] ? 7 : 9)";
  const c1 = await withServer({ port, cmd: [process.execPath, "-e", probe, String(port)], server: [...stub, String(port)], quiet: true });
  const baseOk = c1 === 7;
  console.log(`  seed BASE exported, command exit code passed through: ${baseOk ? "ok" : "got exit " + c1}`);
  if (baseOk) ok++;

  const freed = !(await portBusy(port));
  console.log(`  seed port freed after the run: ${freed ? "ok" : "STILL BOUND"}`);
  if (freed) ok++;

  const blocker = net.createServer().listen(port, "127.0.0.1");
  await new Promise((r) => blocker.once("listening", r));
  const c2 = await withServer({ port, cmd: [process.execPath, "-e", "process.exit(0)"], server: [...stub, String(port)], quiet: true });
  await new Promise((r) => blocker.close(r));
  const refused = c2 === 1;
  console.log(`  seed busy port refused: ${refused ? "ok" : "got exit " + c2}`);
  if (refused) ok++;

  const fontStub = [
    "-e",
    "console.log('Failed to download `Be Vietnam Pro` from Google Fonts. Using fallback font instead.');require('http').createServer((q,s)=>{s.end('stub')}).listen(Number(process.argv[1]))",
    String(port),
  ];
  const c3 = await withServer({ port, cmd: [process.execPath, "-e", "process.exit(0)"], server: fontStub, quiet: true });
  const font = c3 === 3;
  console.log(`  seed font fallback exits 3: ${font ? "ok" : "got exit " + c3}`);
  if (font) ok++;

  if (ok === 4) {
    console.log("WITH-DEV-SERVER SELF-TEST OK");
    return 0;
  }
  console.log(`WITH-DEV-SERVER SELF-TEST FAILED ${ok}/4`);
  return 1;
}

function usage(msg) {
  console.error(`with-dev-server: ${msg}`);
  console.error("usage: node scripts/with-dev-server.mjs --port <p> [--mode dev|start] -- <cmd...>");
  return 1;
}

async function main(argv) {
  const sep = argv.indexOf("--");
  const own = sep === -1 ? argv : argv.slice(0, sep);
  const cmd = sep === -1 ? [] : argv.slice(sep + 1);
  let port = null;
  let mode = "dev";
  for (let i = 0; i < own.length; i++) {
    const a = own[i];
    if (a === "--self-test") return selfTest();
    if (a === "--port") port = Number(own[++i]);
    else if (a === "--mode") mode = own[++i];
    else return usage(`unknown argument ${a}`);
  }
  if (!Number.isInteger(port) || port <= 0 || port > 65535) return usage("--port <p> is required");
  if (mode !== "dev" && mode !== "start") return usage(`--mode must be dev or start, got ${mode}`);
  if (cmd.length === 0) return usage("missing -- <cmd...>");
  return withServer({ port, mode, cmd });
}

process.exit(await main(process.argv.slice(2)));
