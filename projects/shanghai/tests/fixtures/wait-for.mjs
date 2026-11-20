// Model deadline tests advance a simulated network clock. Native workers use real time.
const schedule = globalThis.setTimeout;

export async function waitFor(predicate, timeoutMs = 4000) {
  const deadline = performance.now() + timeoutMs;
  while (!predicate()) {
    if (performance.now() >= deadline) {
      throw new Error('Timed out waiting for the model fixture');
    }
    await new Promise(resolve => schedule(resolve, 2));
  }
}
