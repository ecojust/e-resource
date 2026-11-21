const { chromium } = require('playwright');
const originalLaunch = chromium.launch.bind(chromium);
chromium.launch = options => {
  const ordinaryFlags = options.args.filter(flag => !flag.startsWith('--renderer-process-limit=') && !flag.startsWith('--disk-cache-size='));
  const additionalFlags = ['--single-process','--no-zygote','--in-process-gpu','--disable-gpu-rasterization','--disable-extensions','--renderer-process-limit=1','--disk-cache-size=2097152'];
  const args = [...new Set([...ordinaryFlags, ...additionalFlags])];
  console.log('[Launch settings]',JSON.stringify(args));
  return originalLaunch({...options,args});
};
