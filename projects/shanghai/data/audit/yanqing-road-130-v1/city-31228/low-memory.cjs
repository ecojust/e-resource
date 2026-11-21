'use strict';
// Use the same source page, camera and WebGL adapter with one Chromium process.
const { chromium } = require('/tmp/country-tools/node_modules/playwright');
const launch = chromium.launch.bind(chromium);
chromium.launch = (options = {}) => launch({
  ...options,
  args: [...new Set([...(options.args || []),
    '--single-process', '--no-zygote', '--in-process-gpu',
    '--disable-gpu-shader-disk-cache', '--renderer-process-limit=1'
  ])]
});
