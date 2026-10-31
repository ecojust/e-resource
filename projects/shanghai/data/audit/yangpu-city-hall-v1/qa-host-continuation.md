# Retain the original QA host for continuation

`continuation-host.cjs` keeps an existing Node/Playwright host awaiting an explicit
control file after a QA failure. It never connects a browser or closes a page,
context, or browser. A continuation runs inside that same process with the same
objects. Keep this helper and its controls in the private QA directory.

```js
const { waitForContinuation } = require('./continuation-host.cjs');

// Created earlier by this one original QA host:
// browser, page, report, saveReport, verifyFrozenInputs, runAssertions
const context = {
  browser, page, report,
  validateContinuationResult: async result => {
    // Assert the required QA coverage, images, and assets; throw if incomplete.
    await runAssertions({ browser, page, report, result });
  },
};
try {
  await runAssertions(context);
} catch (error) {
  // Preserve the actual original failure before entering the continuation loop.
  report.originalFailure = { message: error.message, stack: error.stack };
  await saveReport(report);
  const result = await waitForContinuation({
    controlPath: '/workspace/yangpu-city-hall-qa/continuation-control.json',
    context,
    report,
    save: saveReport, // async (report) => persist the report
    verifyFrozenInputs, // async (context) => throw if any frozen input changed
    onProgress: message => console.log(message),
  });
  // Success means the continuation returned and the final frozen-input check passed.
  // The original assertion failure remains in report.originalFailure.
}
// Keep any browser teardown outside the catch/continuation loop.
```

The agent first writes an absolute `.cjs` module exporting an async function:

```js
module.exports = async function (ctx, args) {
  // Use ctx.page, ctx.browser, and ctx.report already owned by the host.
  // Capture provenance is available in ctx.activeCaptureScript and ctx.controlBinding.
  // Perform the intended QA steps and assertions; throw if they fail.
  return { completed: true, reason: args?.label };
};
```

Then the agent hashes the **exact module bytes** with SHA-256 and publishes a control
JSON file, preferably by writing a sibling temporary file and renaming it atomically:

```json
{
  "module": "/workspace/yangpu-city-hall-qa/continuation-01.cjs",
  "sha256": "<64 hexadecimal characters from the module's actual SHA-256>",
  "reason": "Continue QA after preserving the initial assertion failure",
  "args": { "label": "resume screenshots and remaining assertions" }
}
```

An invalid control or mismatched hash is recorded and never executed. Every distinct
control byte sequence is attempted at most once per `waitForContinuation` invocation,
including rejected controls. To retry, publish new control bytes with a clear reason.
Controls are not consumed or deleted; remove stale controls before a later invocation
if they should not run again.

The helper loads a fresh CommonJS module from the verified source snapshot. It checks
frozen inputs before loading/executing it and after it returns. The verifier must
throw to reject changes. Module load errors, thrown assertions, rejected promises,
and failed frozen-input checks are recorded with stacks, saved, and followed by
another wait. If provided, `context.validateContinuationResult(result)` runs after
the module returns and before the final frozen-input check. Throwing or rejecting
from that callback records a `continuation-failed` event with phase `validate-result`
and keeps the same host waiting for distinct control bytes. The rejected control
cannot run again within that invocation. A continuation only succeeds after its
result validator and final verifier pass; its success record describes continuation
execution, not an overall QA verdict.

Events go into `report.continuations` (or directly into `report` if it is an array).
Records include control and module hashes when available, reason, phase, and failures.
`save(report)` runs for every event. If saving fails, that failure remains in memory
and is sent to `onProgress`; the host remains alive. The default progress callback
prints to stdout; callbacks receive `(message, details)`. A callback failure is also
retained in memory. Waiting reports progress immediately and every 30 seconds.

If capture code keeps provenance in a closure, provide
`context.setCaptureProvenance = async binding => { /* update that closure */ }`.
It receives the same frozen binding assigned to `context.controlBinding` before the
module is loaded. `context.report`, if already present, must be the supplied report.

Continuation modules are trusted agent-written code with the host's full access.
The hash binds the entry module bytes; it does not sandbox the module or hash its
dependencies. Use the existing host's read-only QA operations and capture routines.
The helper creates no browser connections, subprocesses, or automatic teardown.
