# Opaque inferred city-window shadow correction

This is an explicitly approved, staged one-file correction. MAIN and the original app/QA tools remain untouched. Only `src/realistic-lighting.js` changes: opaque materials named exactly `Inferred dark glazing` may cast shadows. Existing caster filters, all other glazing, visible materials, geometry, shadow-map parameters and state restoration retain their behavior.

Original file:22,727 bytes, SHA256 `d157ea58952b4bbf018ea75f64058cf988c349d980234a7eec598388973a858d`.
Patched file:23,086 bytes, SHA256 `6cb2fb4dc1cca564d70f2718014c11600ba5846915df4d707caa5b56a873838c`.
The immutable contract is `runtime-delta.json`, SHA256 `6a415603a7e183f868f57607e58471bbd56649f9ec90cff1f130b93af0a87ea2`.

The original11-frame run passed functional checks but root rejected the roof window-grid light leaks. Its original report and image identities are retained in `evidence/diagnosis.json`; technical shadow-map size checks do not constitute visual acceptance. The east retained neighbor local1474 lies in the sun direction. Actual compressed-near decoding and169 finite diagnostic rays found50 leaks when opaque inferred glazing was excluded; the patched production selector removes all50 while retaining all18 neighbor meshes and hiding the same8 target meshes. This CPU probe uses a6m diagnostic plane and is not a pixel-exact GPU comparison.

Fifteen narrow old/new CPU controls, four disposal-state combinations and four unchanged relevant production suites passed. They cover the exact material name, opacity threshold, transparent exclusions, unchanged precise/photo/other glass, caster-filter veto, visibility radius, lighting parameters and restoration. `module-resolution.mjs` redirects only the tested lighting module when running existing suites; no production source is edited.

`runtime-only-installation-plan.json` is for a new isolated candidate only. The full guarded candidate/final publication workflow lives in the separate `../integration-two-district-app-shadow-v2/` revision. Both the original42/13 locks and an additional31-file source snapshot are retained. Every other runtime source must remain exact. Root must perform a new complete11-frame run and both5-frame catalog runs; their visual records must bind the delta and patched runtime SHA. No patched browser success is claimed here.

CPU reproduction in this workspace:

```sh
node tests/opaque-inferred-controls.mjs
node tests/replay-compressed-near-rays.mjs
```

The freeze scripts deliberately refuse to overwrite existing evidence. Original failed visual evidence and original tools remain available. Each published file remains strictly below100 MB.
