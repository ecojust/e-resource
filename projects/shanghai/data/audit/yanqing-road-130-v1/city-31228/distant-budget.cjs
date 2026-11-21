'use strict';
// Use the same source page, camera and WebGL adapter with one Chromium process.
const { chromium } = require('/tmp/country-tools/node_modules/playwright');
const launch = chromium.launch.bind(chromium);
chromium.launch = (options = {}) => launch({
  ...options,
  args: [...new Set([...(options.args || []).filter(a=>!a.startsWith('--js-flags=')),
    '--single-process', '--no-zygote', '--in-process-gpu',
    '--disable-gpu-shader-disk-cache','--js-flags=--max-old-space-size=145 --max-semi-space-size=2 --optimize-for-size','--force-gpu-mem-available-mb=64','--disable-component-update','--disable-extensions', '--renderer-process-limit=1'
  ])]
});
