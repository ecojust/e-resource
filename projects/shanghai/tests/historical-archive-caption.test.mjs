import assert from 'node:assert/strict';
import test from 'node:test';

test('1934–1937 photographed cinema and 2010–2011 archived garden elevation keep their distinct captions',async()=>{
  const {setupHistoricalView}=await import('../src/historical-view.js');
  const originalWindow=globalThis.window,originalLocation=globalThis.location;
  const host=new EventTarget(),origin='https://example.test';
  globalThis.window=host;globalThis.location={origin};
  const control=()=>Object.assign(new EventTarget(),{hidden:false,isConnected:true,focus(){this.focused=true;}});
  const button=control(),closeButton=control(),dialog=control(),frameWindow={};
  Object.assign(dialog,{open:false,showModal(){this.open=true;},close(){this.open=false;this.dispatchEvent(new Event('close'));}});
  const title={},frame={contentWindow:frameWindow,removeAttribute(key){delete this[key];}},changes=[];
  const site={id:'huangpu-metropol-cinema-historic-front',kind:'historical-site',name:'历史建筑',individual_page:'example-history.html',
    historical_view:{building_year:1933,evidence_years:[1934,1937]}};
  const post=(source,messageOrigin)=>host.dispatchEvent(Object.assign(new Event('message'),
    {source,origin:messageOrigin,data:'close-historical-view'}));
  try {
    const panel=setupHistoricalView({dialog,button,frame,title,closeButton,onModalChange:open=>changes.push(open)});
    panel.select(site);assert.equal(button.hidden,false);assert.equal(dialog.open,false);assert.equal(frame.src,undefined);
    button.dispatchEvent(new Event('click'));assert.equal(dialog.open,true);assert.equal(frame.src,site.individual_page+'?embed=history');
    assert.equal(title.textContent,'历史建筑 · 1934—1937年照片');assert.equal(closeButton.focused,true);
    post({},origin);post(frameWindow,'https://unrelated.test');assert.equal(dialog.open,true);
    post(frameWindow,origin);assert.equal(dialog.open,false);assert.equal(frame.src,undefined);assert.equal(button.focused,true);
    button.dispatchEvent(new Event('click'));panel.select({id:'modern',kind:'building'});
    assert.equal(dialog.open,false);assert.equal(button.hidden,true);assert.equal(frame.src,undefined);
    button.dispatchEvent(new Event('click'));assert.deepEqual(changes,[true,false,true,false]);
    panel.select({...site,id:'xuhui-huaihai-1469-garden-front',name:'花园住宅',
      historical_view:{building_year:1921,evidence_years:[2010,2011]}});
    button.dispatchEvent(new Event('click'));
    assert.equal(title.textContent,'花园住宅 · 影像资料年份 2010—2011');
    post(frameWindow,origin);
    panel.select({...site,id:'xuhui-jianguo-618-historic-front',name:'建国西路住宅',
      historical_view:{building_year:1948,evidence_years:[2013,2013]}});
    button.dispatchEvent(new Event('click'));
    assert.equal(title.textContent,'建国西路住宅 · 2013年照片');
    post(frameWindow,origin);
    assert.equal(dialog.open,false);
  } finally {
    if(originalWindow===undefined)delete globalThis.window;else globalThis.window=originalWindow;
    if(originalLocation===undefined)delete globalThis.location;else globalThis.location=originalLocation;
  }
});
