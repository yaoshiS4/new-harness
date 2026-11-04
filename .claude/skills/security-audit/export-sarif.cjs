#!/usr/bin/env node

/**
 * Exports confirmed findings in findings.json to SARIF 2.1.0 with the
 * google/mantis (`reference/core/sarif.py`) Zero-Leak Path Relativizer.
 *
 * Usage:
 *   node export-sarif.cjs --scan-root <dir> --findings <file> [--out <file>]
 *   node export-sarif.cjs --self-test
 */

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const SARIF_VERSION = "2.1.0";
const SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json";
const HOST_PATH_LEAK_RE = /(?:^|\/)(?:home|Users|root|private|var\/folders|tmp)\//i;
const WINDOWS_ABS_RE = /^[A-Za-z]:[\\/]/;

function mapSeverityToSarifLevel(severityObj) {
  const score = severityObj &&
    severityObj.overall &&
    typeof severityObj.overall.score === "string"
    ? severityObj.overall.score.toLowerCase()
    : (severityObj &&
      severityObj.impact &&
      typeof severityObj.impact.score === "string"
      ? severityObj.impact.score.toLowerCase()
      : "medium");

  if (score === "critical" || score === "high") return "error";
  if (score === "medium") return "warning";
  return "note";
}

/**
 * Zero-Leak Path Relativizer (`google/mantis` `sarif.py` invariant):
 * Re-derives `rawPath` relative to `scanRoot`. Drops and rejects:
 * - null/empty/non-string paths
 * - raw absolute host paths (`/home/...`, `/Users/...`, `/root/...`, Windows drive paths)
 *   unless they strictly resolve inside `scanRoot` AND caller allows scan-root stripping;
 *   by strict Zero-Leak policy, any raw input starting with `/` or Windows drive or
 *   containing `..` escape outside scanRoot is rejected so host layout never leaks.
 */
function relativizePathZeroLeak(rawPath, scanRoot) {
  if (typeof rawPath !== "string" || rawPath.trim().length === 0) {
    return null;
  }
  const trimmed = rawPath.trim().replace(/\\/g, "/");
  if (trimmed.includes("\0")) {
    return null;
  }

  // Reject explicit absolute host paths or URI schemes immediately
  if (
    trimmed.startsWith("/") ||
    trimmed.startsWith("~") ||
    WINDOWS_ABS_RE.test(trimmed) ||
    /^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(trimmed)
  ) {
    return null;
  }

  const rootResolved = path.resolve(scanRoot || ".");
  const candidateResolved = path.resolve(rootResolved, trimmed);
  const rel = path.relative(rootResolved, candidateResolved).replace(/\\/g, "/");

  if (
    !rel ||
    rel === "." ||
    rel.startsWith("..") ||
    path.isAbsolute(rel) ||
    WINDOWS_ABS_RE.test(rel) ||
    HOST_PATH_LEAK_RE.test(rel)
  ) {
    return null;
  }

  const segments = rel.split("/");
  if (segments.some((seg) => seg === "" || seg === "." || seg === "..")) {
    return null;
  }

  return rel;
}

function buildSarifReport(findings, scanRoot) {
  const safeFindings = Array.isArray(findings) ? findings : [];
  const rules = [];
  const ruleIndexById = new Map();
  const results = [];
  let droppedPathsCount = 0;
  let droppedFindingsCount = 0;

  for (const record of safeFindings) {
    if (!record || typeof record !== "object" || record.verdict !== "confirmed") {
      continue;
    }

    const ruleId = typeof record.fingerprint === "string" && record.fingerprint.trim()
      ? record.fingerprint.trim()
      : "SECURITY-AUDIT-FINDING";
    const title = typeof record.title === "string" && record.title.trim()
      ? record.title.trim()
      : ruleId;
    const description = typeof record.description === "string" && record.description.trim()
      ? record.description.trim()
      : title;
    const level = mapSeverityToSarifLevel(record.severity);

    const locations = [];
    const traceList = Array.isArray(record.trace) ? record.trace : [];
    const evidenceList = Array.isArray(record.evidence) ? record.evidence : [];
    const rawCandidates = [...traceList, ...evidenceList];

    for (const item of rawCandidates) {
      if (!item || typeof item !== "object") continue;
      const safeRelPath = relativizePathZeroLeak(item.file, scanRoot);
      if (!safeRelPath) {
        droppedPathsCount++;
        continue;
      }
      const line = Number.isInteger(item.line) && item.line >= 1 ? item.line : 1;
      locations.push({
        physicalLocation: {
          artifactLocation: {
            uri: safeRelPath,
            uriBaseId: "%SRCROOT%",
          },
          region: {
            startLine: line,
          },
        },
      });
    }

    if (locations.length === 0) {
      droppedFindingsCount++;
      continue;
    }

    if (!ruleIndexById.has(ruleId)) {
      ruleIndexById.set(ruleId, rules.length);
      rules.push({
        id: ruleId,
        shortDescription: { text: title },
        fullDescription: { text: description },
        defaultConfiguration: { level },
      });
    }

    results.push({
      ruleId,
      ruleIndex: ruleIndexById.get(ruleId),
      level,
      message: {
        text: `${title}: ${description}`,
      },
      locations: [locations[0]],
      relatedLocations: locations.slice(1).map((loc, idx) => ({
        id: idx + 1,
        physicalLocation: loc.physicalLocation,
        message: { text: "Trace / evidence step" },
      })),
    });
  }

  const sarif = {
    $schema: SARIF_SCHEMA,
    version: SARIF_VERSION,
    runs: [
      {
        tool: {
          driver: {
            name: "antigravity-security-audit",
            informationUri: "https://github.com/google/mantis",
            rules,
          },
        },
        properties: {
          zeroLeakRelativizer: {
            droppedPathsCount,
            droppedFindingsCount,
          },
        },
        results,
      },
    ],
  };

  return { sarif, droppedPathsCount, droppedFindingsCount };
}

function runSelfTest() {
  const scanRoot = "/workspace/repo-under-test";

  // 1. Valid relative path
  assert.equal(relativizePathZeroLeak("src/auth/login.ts", scanRoot), "src/auth/login.ts");
  assert.equal(relativizePathZeroLeak("./src/api/../auth/login.ts", scanRoot), "src/auth/login.ts");

  // 2. Reject host absolute paths & traversal escapes
  assert.equal(relativizePathZeroLeak("~/Projects/secret.ts", scanRoot), null);
  assert.equal(relativizePathZeroLeak("/Users/alice/repo/src/a.ts", scanRoot), null);
  assert.equal(relativizePathZeroLeak("../../etc/passwd", scanRoot), null);
  assert.equal(relativizePathZeroLeak("src/../../../etc/shadow", scanRoot), null);
  assert.equal(relativizePathZeroLeak("C:\\Users\\admin\\file.js", scanRoot), null);
  assert.equal(relativizePathZeroLeak("file:///home/user/a.js", scanRoot), null);

  // 3. Build SARIF report and verify zero host path leak
  const sampleFindings = [
    {
      verdict: "confirmed",
      fingerprint: "authz-bypass-01",
      title: "Missing owner check on update route",
      description: "Any authenticated user can update another user's record.",
      severity: {
        overall: { score: "high", reason: "Cross-tenant write" },
      },
      trace: [
        { kind: "entrypoint", file: "~/leaked/host/path.ts", line: 10, scope: "route", description: "leaked" },
        { kind: "sink", file: "src/controllers/user.ts", line: 42, scope: "updateUser", description: "sink" },
      ],
      evidence: [],
    },
    {
      verdict: "confirmed",
      fingerprint: "all-leaked-paths-02",
      title: "Finding with only host paths",
      description: "Must be dropped entirely rather than emitting a leaked or empty location.",
      severity: {
        overall: { score: "medium", reason: "Leak test" },
      },
      trace: [
        { kind: "sink", file: "../../outside/repo.ts", line: 5, scope: "fn", description: "escape" },
      ],
      evidence: [],
    },
    {
      verdict: "needs_validation",
      fingerprint: "unconfirmed-03",
      title: "Should not appear in SARIF confirmed export",
      description: "Needs validation only",
    },
  ];

  const { sarif, droppedPathsCount, droppedFindingsCount } = buildSarifReport(sampleFindings, scanRoot);
  assert.equal(sarif.version, "2.1.0");
  assert.equal(droppedPathsCount, 2);
  assert.equal(droppedFindingsCount, 1);
  assert.equal(sarif.runs[0].results.length, 1);
  assert.equal(
    sarif.runs[0].results[0].locations[0].physicalLocation.artifactLocation.uri,
    "src/controllers/user.ts",
  );
  const serialized = JSON.stringify(sarif);
  assert.equal(serialized.includes("/home/"), false);
  assert.equal(serialized.includes(".."), false);

  console.log("PASS: export-sarif.cjs --self-test succeeded (Zero-Leak Path Relativizer verified)");
  return 0;
}

function parseArgs(argv) {
  const options = {
    scanRoot: process.cwd(),
    findings: null,
    out: null,
    selfTest: false,
  };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--self-test") {
      options.selfTest = true;
    } else if (arg === "--scan-root" && i + 1 < argv.length) {
      options.scanRoot = argv[++i];
    } else if (arg === "--findings" && i + 1 < argv.length) {
      options.findings = argv[++i];
    } else if (arg === "--out" && i + 1 < argv.length) {
      options.out = argv[++i];
    }
  }
  return options;
}

function main(argv) {
  const options = parseArgs(argv);
  if (options.selfTest) {
    return runSelfTest();
  }
  if (!options.findings) {
    console.error("Usage: node export-sarif.cjs --scan-root <dir> --findings <file> [--out <file>] | --self-test");
    return 1;
  }

  let findings;
  try {
    findings = JSON.parse(fs.readFileSync(options.findings, "utf8"));
  } catch (error) {
    console.error(`Failed to read or parse findings JSON: ${error.message}`);
    return 1;
  }

  const { sarif } = buildSarifReport(findings, options.scanRoot);
  const outputText = `${JSON.stringify(sarif, null, 2)}\n`;
  if (options.out) {
    fs.writeFileSync(options.out, outputText, "utf8");
  } else {
    process.stdout.write(outputText);
  }
  return 0;
}

module.exports = {
  SARIF_SCHEMA,
  SARIF_VERSION,
  buildSarifReport,
  mapSeverityToSarifLevel,
  relativizePathZeroLeak,
  runSelfTest,
};

if (require.main === module) {
  process.exit(main(process.argv.slice(2)));
}
