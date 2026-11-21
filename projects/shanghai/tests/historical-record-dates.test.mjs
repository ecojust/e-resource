import assert from 'node:assert/strict';
import test from 'node:test';
import { historicalSiteCaption, setupHistoricalView, validHistoricalSite } from '../src/historical-view.js';
import { placeDescription, walkingPose } from '../src/precise-registration-ui.js';
import { mergeCandidateCityModels } from '../src/candidate-city-integrations.js';

const id='changning-hongqiao-road-2275-historic-front';
const folder='assets/models/candidates/'+id+'/';
const period={kind:'archival-facade',listed_year:1994,approximate_loss_year:1996,evidence_kind:'published-drawing',evidence_years:[2015,2020]};
const asset=role=>({file:folder+id+'-'+role+'.glb',bytes:42,sha256:'1'.repeat(64)});
const marker={id,name:'虹桥路2275号历史住宅',kind:'historical-site',districtId:'310105',district_name:'长宁区',lng:121.38,lat:31.19,
  historical_view:period,individual_page:'hongqiao-road-2275-history.html',candidate_manifest:folder+'manifest.json',
  source_feature_ids:{building:[],building_part:[]},collision_geometry:null,replacement_geometry:null,
  navigation:{listed:false},assets:{web:asset('web'),lod:asset('lod')}};

test('a listing, approximate loss and publication have distinct meanings on the location card',()=>{
  assert.ok(validHistoricalSite(marker));
  const [place]=mergeCandidateCityModels([],{schema:'candidate-city-integrations-v1',models:[marker]});
  assert.equal(walkingPose(place),null);
  assert.equal(place.model,undefined);
  assert.equal(historicalSiteCaption(period),'1994年名录登记 · 原建筑约1996年灭失');
  assert.equal(placeDescription(place),'长宁区 · 1994年名录登记 · 原建筑约1996年灭失 · 出版画稿复原');
  const dated={kind:'archival-facade',building_year:1933,evidence_years:[1934,1937]};
  assert.ok(validHistoricalSite({...marker,historical_view:dated}));
  assert.equal(historicalSiteCaption(dated),'1933年建筑原址');
  assert.equal(placeDescription({...marker,historical_view:dated}),'长宁区 · 1933年建筑 · 历史照片复原');
});

test('reversed, ambiguous or unsupported dates cannot create a valid marker',()=>{
  for(const change of [{listed_year:1997},{approximate_loss_year:NaN},{listed_year:'1994'},{building_year:1994},
                       {evidence_kind:'photographs'},{evidence_years:[2020,2015]},{evidence_years:[2015,3000]}]){
    assert.equal(validHistoricalSite({...marker,historical_view:{...period,...change}}),false);
  }
  const {approximate_loss_year,...missing}=period;
  assert.equal(validHistoricalSite({...marker,historical_view:missing}),false);
});

test('the independent viewer identifies the original publication and reprint of the drawing',()=>{
  const originalWindow=globalThis.window;
  globalThis.window=new EventTarget();
  try{
    const control=()=>Object.assign(new EventTarget(),{hidden:false,focus(){}});
    const button=control(),closeButton=control(),title={},frame={};
    const dialog=Object.assign(new EventTarget(),{open:false,showModal(){this.open=true;}});
    const panel=setupHistoricalView({dialog,button,frame,title,closeButton,onModalChange(){}});
    panel.select(marker);
    button.dispatchEvent(new Event('click'));
    assert.equal(title.textContent,'虹桥路2275号历史住宅 · 2015年出版的钢笔画，2020年重刊');
    assert.equal(frame.src,'hongqiao-road-2275-history.html?embed=history');
  } finally {
    if(originalWindow===undefined)delete globalThis.window;else globalThis.window=originalWindow;
  }
});
