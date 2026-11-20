// Rerun against the postal QA server with system Chromium and Playwright.
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const { createHash } = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { chromium } = require('playwright');

const tileUrl = 'https://tiles.overturemaps.org/2026-10-21.0/buildings.pmtiles';
const sha = data => createHash('sha256').update(data).digest('hex');
const origin = new URL(process.env.MODEL_BASE_URL || 'http://127.0.0.1:8784/').origin;

async function readInBrowser(page, range) {
  return page.evaluate(async ({ url, range }) => {
    const response = await fetch(url, { headers: { Range: range }, signal: AbortSignal.timeout(30000) });
    const data = await response.arrayBuffer();
    const digest = await crypto.subtle.digest('SHA-256', data);
    return {
      url: response.url,
      status: response.status,
      type: response.type,
      contentRange: response.headers.get('Content-Range'),
      etag: response.headers.get('ETag'),
      bytes: data.byteLength,
      sha256: Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join(''),
    };
  }, { url: tileUrl, range });
}

async function main() {
  const executablePath = process.env.CHROMIUM_EXECUTABLE || '/usr/bin/chromium';
  const browser = await chromium.launch({ executablePath, headless: true, args: ['--no-sandbox'] });
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'postal-range-'));
  const report = {
    checkedAt: new Date().toISOString(),
    scriptSha256: sha(fs.readFileSync(__filename)),
    origin, tileUrl, chromium: browser.version(),
    ignoreHTTPSErrors: true, routeInterception: false,
    scope: 'Two direct range GETs from the local audit origin and independent byte comparisons at the recorded time.',
    ranges: [],
  };
  try {
    const page = await browser.newPage({ ignoreHTTPSErrors: true });
    await page.goto(origin + '/qa-blank.html');
    for (const [start, end] of [[0, 16383], [16384, 17407]]) {
      const range = 'bytes=' + start + '-' + end;
      const observed = await readInBrowser(page, range);
      const headers = path.join(tmp, 'headers');
      const data = execFileSync('curl', [
        '-fsS', '--max-time', '30', '-D', headers,
        '-H', 'Origin: ' + origin, '-H', 'Range: ' + range, tileUrl,
      ]);
      const received = fs.readFileSync(headers, 'utf8').trim().split(/\r?\n\r?\n/).pop();
      const fields = {};
      for (const line of received.split(/\r?\n/).slice(1)) {
        const index = line.indexOf(':');
        if (index > 0) fields[line.slice(0, index).toLowerCase()] = line.slice(index + 1).trim();
      }
      assert.match(received, /^HTTP\/\S+ 206\b/);
      assert.equal(observed.status, 206);
      assert.equal(observed.type, 'cors');
      assert.equal(observed.url, tileUrl);
      assert.equal(observed.contentRange, fields['content-range']);
      assert.match(observed.contentRange, new RegExp('^bytes ' + start + '-' + end + '/[0-9]+$'));
      assert.ok(observed.etag);
      assert.equal(observed.etag, fields.etag);
      assert.ok(['*', origin].includes(fields['access-control-allow-origin']));
      assert.equal(observed.bytes, end - start + 1);
      assert.equal(data.length, observed.bytes);
      assert.equal(sha(data), observed.sha256);
      if (!start) assert.equal(data.subarray(0, 7).toString('ascii'), 'PMTiles');
      report.ranges.push({ range, browser: observed, curl: {
        status: 206, contentRange: fields['content-range'], etag: fields.etag,
        allowOrigin: fields['access-control-allow-origin'],
        exposeHeaders: fields['access-control-expose-headers'], bytes: data.length, sha256: sha(data),
      } });
    }
  } finally {
    await browser.close();
    fs.rmSync(tmp, { recursive: true });
  }
  process.stdout.write(JSON.stringify(report, null, 2) + '\n');
}

main().catch(error => { console.error(error); process.exitCode = 1; });
