# npm audit triage and compatible remediation

November14,2026. Before: eight affected package entries (4moderate,3high,1critical), not eight distinct CVEs. Full raw advisory ranges/URLs are in evidence/npm-audit-before.json; dependency paths before/after and the dry-run plan are retained. No secret configuration was printed.

| Package | Directness / exposure | Before -> after | Practical issue / disposition |
| --- | --- | --- | --- |
| eslint | Direct devDependency |10.9.1 ->10.15.0 | Inherits minimatch glob DoS; local lint tooling, not served dashboard. Compatible same-major update. |
| vite | Direct devDependency |8.2.2 ->8.3.8 | Dev-server editor-launch command/argument issues (especially Windows), file exposure and middleware advisories; dev-only package but an exposed development server is a practical risk. Compatible same-major update. |
| @eslint/config-array | Transitive dev, via eslint |0.23.5 ->0.23.6 | Inherits minimatch; fixed by compatible parent update. |
| minimatch | Transitive dev, via eslint/config-array |10.2.6 ->11.0.8 | Glob amplification DoS. Major TRANSITIVE change chosen by the compatible eslint10.15 dependency contract; no forced override of an old consumer to a new major. |
| brace-expansion | Transitive dev, via minimatch |5.0.9 ->5.0.13 | Recursion/CPU exhaustion in crafted glob braces; patched allowed dependency. |
| postcss-selector-parser | Transitive dev, via eslint-plugin-vue |7.1.5 ->7.2.1 | Crafted selector CPU exhaustion; compatible allowed minor update. |
| shell-quote | Transitive dev, via npm-run-all2 |1.10.0 ->1.12.0 | Critical command-injection advisory requires crafted quote tokens in command tooling; no normal quote input from market messages. Fixed allowed minor. |
| source-map-js | Transitive BOTH production graph (Vue compiler packages) and development (Vite/PostCSS) |1.2.1 ->1.2.2 | Malicious indexed source map offsets can cause event-loop DoS. Production dependency classification does not establish vulnerable code is reachable in the compiled dashboard bundle; dashboard does not accept arbitrary source maps. Patched allowed update, no runtime exploit claim. |

The reviewed dry-run proposed same-major direct ESLint/Vite updates plus their required allowed dependencies. Applied ordinary npm audit fix without --force, without changing manifest dependency ranges or introducing direct breaking upgrades. Actual output:10 added,2 removed,17 changed,227 audited. Additional cache/rolldown/PostCSS helper dependency changes follow those parent resolutions; full exact lockfile is authoritative. Chart5.3.0, Vue3.5.42, Leaflet1.9.4 and Oxlint1.73.0 remain. Both full and omit-dev post-fix audit report ZERO known vulnerabilities. No breaking direct upgrade was required or applied. Node24.20.0 ran tests/lint/build; no engine incompatibility was reported. This does not prove the absence of undisclosed flaws or replace a clean-install check.

Remaining risk: keep the localhost development server private; installed dev tooling still executes local project configuration. Do not treat npm audit zero as security certification. Do not expose the unauthenticated local controls publicly. A clean-checkout npm ci/build and browser check with this exact lockfile remain pending; no machine-level/global changes made.

Primary sources reviewed November14,2026 (URLs also embedded in raw audit):

- https://github.com/advisories/GHSA-pqg4-j6r4-53mv
- https://github.com/advisories/GHSA-587h-7wmj-h5pm
- https://github.com/advisories/GHSA-g3hv-75wg-m249
- https://github.com/advisories/GHSA-68fv-2mgg-jv7q
- https://github.com/advisories/GHSA-rj75-hqrm-r3gf
- https://github.com/advisories/GHSA-q2hr-2g5m-vwhr
- https://github.com/vitejs/vite/releases/tag/v8.3.8
- https://github.com/eslint/eslint/releases/tag/v10.15.0
