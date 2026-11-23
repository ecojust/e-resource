const fs = require('node:fs');
const out = process.argv[2];
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
  for (let attempt = 0; attempt < 60; attempt++) {
    try {
      const pages = await (await fetch('http://127.0.0.1:19476/json/list')).json();
      const page = pages.find(p => p.type === 'page' && p.url.includes('127.0.0.1:31276/'));
      if (!page) { await wait(800); continue; }
      const socket = new WebSocket(page.webSocketDebuggerUrl);
      const state = await new Promise((resolve, reject) => {
        const timer = setTimeout(() => { socket.close(); reject(Error('debug timeout')); }, 3000);
        socket.onopen = () => socket.send(JSON.stringify({id: 1, method: 'Runtime.evaluate', params: {expression: `(()=>{const s=window.__SHANGHAI_APP__?.scene;if(!s)return null;const q=s.getRealismState(),l=q.lighting;return {site:location.href,renderer:window.initialMapRendering?.renderer,pixel_ratio:s.map.getPixelRatio(),lighting:{enabled:l?.enabled,shadowSize:l?.shadowSize,activeCasterModels:l?.activeCasterModels},viewport:[innerWidth,innerHeight]};})()`, returnByValue:true}}));
        socket.onmessage = event => {
          const reply = JSON.parse(event.data);
          if (reply.id !== 1) return;
          clearTimeout(timer); socket.close(); resolve(reply.result?.result?.value);
        };
        socket.onerror = error => {clearTimeout(timer); reject(error);};
      });
      if (state && typeof state.lighting.enabled === 'boolean') {
        fs.writeFileSync(out, JSON.stringify({...state, observed_at: new Date().toISOString()}, null, 2)+'\n');
        return;
      }
    } catch {}
    await wait(1000);
  }
  process.exitCode = 2;
})();
