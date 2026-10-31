'use strict';

// Private QA host helper: deliberately has no browser lifecycle operations.
const fs = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');
const Module = require('node:module');
const { performance } = require('node:perf_hooks');

const sha256 = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const errorDetails = error => ({
  message: String(error && error.message || error),
  stack: error && typeof error.stack === 'string' ? error.stack : String(error),
});

async function waitForContinuation({
  controlPath, context, report, save, verifyFrozenInputs,
  onProgress = message => console.log(message), intervalMs = 1000,
}) {
  if (typeof controlPath !== 'string' || !path.isAbsolute(controlPath)) {
    throw new TypeError('controlPath must be an absolute path');
  }
  if (!context || typeof context !== 'object' || !report || typeof report !== 'object') {
    throw new TypeError('context and report must be objects');
  }
  if (typeof save !== 'function' || typeof verifyFrozenInputs !== 'function' ||
      typeof onProgress !== 'function') {
    throw new TypeError('save, verifyFrozenInputs, and onProgress must be functions');
  }
  if (!Number.isFinite(intervalMs) || intervalMs < 1) {
    throw new TypeError('intervalMs must be a finite number of at least 1');
  }
  if (context.report !== undefined && context.report !== report) {
    throw new TypeError('context.report must refer to the supplied report');
  }
  context.report = report;
  const events = Array.isArray(report) ? report : (report.continuations ??= []);
  if (!Array.isArray(events)) throw new TypeError('report.continuations must be an array');

  const seenControls = new Set();
  let lastProgress = -Infinity;
  let lastReadError;
  const append = event => events.push({ at: new Date().toISOString(), ...event });

  async function progress(message, details = {}) {
    try {
      await onProgress(message, details);
    } catch (error) {
      // A broken logging callback must not tear down the retained QA host.
      append({ type: 'continuation-progress-failed', ...errorDetails(error) });
    }
  }

  async function record(event) {
    append(event);
    try {
      await save(report);
    } catch (error) {
      // Preserve the in-memory evidence and live host even if persistence fails.
      const failure = { type: 'continuation-save-failed', ...errorDetails(error) };
      append(failure);
      await progress(`Continuation report could not be saved: ${failure.message}`, failure);
    }
  }

  await record({
    type: 'continuation-waiting', controlPath,
    message: 'Host awaiting continuation control; this does not establish a passing QA result.',
  });

  for (;;) {
    if (performance.now() - lastProgress >= 30_000) {
      lastProgress = performance.now();
      await progress(`QA host alive; awaiting a new continuation at ${controlPath}`, {
        controlPath, controlsSeen: seenControls.size,
      });
    }

    let bytes;
    try {
      bytes = await fs.readFile(controlPath);
      lastReadError = undefined;
    } catch (error) {
      if (error.code !== 'ENOENT') {
        const key = `${error.code}:${error.message}`;
        if (key !== lastReadError) {
          lastReadError = key;
          await record({ type: 'continuation-control-read-failed', controlPath, ...errorDetails(error) });
        }
      }
    }

    if (bytes) {
      const controlSha256 = sha256(bytes);
      if (!seenControls.has(controlSha256)) {
        // Mark all observed bytes, including invalid controls, before doing work.
        seenControls.add(controlSha256);
        const binding = { controlPath, controlSha256 };
        let phase = 'validate-control';
        let started = false;
        try {
          const control = JSON.parse(bytes.toString('utf8'));
          if (!control || typeof control !== 'object' || Array.isArray(control)) {
            throw new TypeError('Control must be a JSON object');
          }
          if (typeof control.module !== 'string' || !path.isAbsolute(control.module) ||
              !control.module.endsWith('.cjs')) {
            throw new TypeError('Control module must be an absolute .cjs path');
          }
          binding.module = path.resolve(control.module);
          if (typeof control.reason !== 'string' || !control.reason.trim()) {
            throw new TypeError('Control reason must be a nonempty string');
          }
          binding.reason = control.reason.trim();
          if (typeof control.sha256 !== 'string' || !/^[a-fA-F0-9]{64}$/.test(control.sha256)) {
            throw new TypeError('Control sha256 must contain exactly 64 hexadecimal characters');
          }
          binding.expectedModuleSha256 = control.sha256.toLowerCase();

          phase = 'read-module';
          const file = await fs.open(binding.module, 'r');
          let source;
          try {
            if (!(await file.stat()).isFile()) throw new TypeError('Control module must be a regular file');
            source = await file.readFile();
          } finally {
            await file.close();
          }
          binding.moduleSha256 = sha256(source);
          if (binding.moduleSha256 !== binding.expectedModuleSha256) {
            throw new Error(`Module SHA-256 mismatch: expected ${binding.expectedModuleSha256}, actual ${binding.moduleSha256}`);
          }

          phase = 'verify-before';
          await verifyFrozenInputs(context);
          phase = 'bind-provenance';
          const provenance = Object.freeze({ ...binding });
          context.activeCaptureScript = binding.module;
          context.controlBinding = provenance;
          if (typeof context.setCaptureProvenance === 'function') {
            await context.setCaptureProvenance(provenance);
          }

          await record({ type: 'continuation-started', ...binding });
          started = true;
          phase = 'load-module';
          // Compile the verified snapshot rather than rereading a mutable path.
          // A fresh CommonJS Module also avoids reusing a failed module's exports.
          const continuation = new Module(binding.module, module);
          continuation.filename = binding.module;
          continuation.paths = Module._nodeModulePaths(path.dirname(binding.module));
          continuation._compile(source.toString('utf8'), binding.module);
          continuation.loaded = true;
          if (typeof continuation.exports !== 'function') {
            throw new TypeError('Continuation module must export a function(ctx, args)');
          }
          phase = 'run-module';
          const result = await continuation.exports(context, control.args);
          phase = 'validate-result';
          if (typeof context.validateContinuationResult === 'function') {
            await context.validateContinuationResult(result);
          }
          phase = 'verify-after';
          await verifyFrozenInputs(context);
          await record({ type: 'continuation-succeeded', ...binding });
          return result;
        } catch (error) {
          await record({
            type: started || phase === 'verify-before' || phase === 'bind-provenance'
              ? 'continuation-failed' : 'continuation-rejected',
            ...binding, phase, ...errorDetails(error),
          });
          await progress(`Continuation ${started ? 'failed' : 'was not executed'} (${phase}); host remains alive and awaits new control bytes.`, binding);
        }
      }
    }

    // The heartbeat remains at 30 seconds even with a larger polling interval.
    const untilProgress = Math.max(1, 30_000 - (performance.now() - lastProgress));
    await new Promise(resolve => setTimeout(resolve, Math.min(intervalMs, untilProgress)));
  }
}

module.exports = { waitForContinuation };
