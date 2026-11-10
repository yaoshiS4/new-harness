import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    // Harness worktrees and local state (each carries its own .next/types).
    ".claude/**",
  ]),

  /* ==========================================================================
   * COLLECTION SEAM.
   * --------------------------------------------------------------------------
   * Feature code talks to the ports and nothing else. Two bans:
   *
   *   1. `@/lib/collection/adapters/*` — a component that can import a fixture
   *      can ship one, and can learn whether it is talking to a fixture or a
   *      backend. Adapters are wired once, at the composition root.
   *   2. `@/lib/mock` — the collection feature has its own seam. Reaching past
   *      it into the app-wide fixture layer reintroduces exactly the coupling
   *      the ports exist to remove.
   *
   * The harness page is the single declared exception: its whole job is to
   * construct the adapters and prove the four envelope states render.
   * ========================================================================*/
  {
    files: ["src/components/collection/**/*.{ts,tsx}"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@/lib/collection/adapters", "@/lib/collection/adapters/*", "**/adapters/*"],
              message:
                "Collection components import the ports barrel (@/lib/collection), never an adapter. Adapters are wired at the composition root.",
            },
            {
              group: ["@/lib/mock", "@/lib/mock/*"],
              message:
                "Collection code goes through its own ports (@/lib/collection), not the app-wide fixture layer.",
            },
          ],
        },
      ],
    },
  },
]);

export default eslintConfig;
