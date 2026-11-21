import assert from 'node:assert/strict';
import test from 'node:test';
import {historicalSiteCaption, setupHistoricalView, validHistoricalSite} from '../src/historical-view.js';
import {placeDescription, walkingPose} from '../src/precise-registration-ui.js';
import {mergeCandidateCityModels} from '../src/candidate-city-integrations.js';

const id = 'jingan-chen-bingqian-historic-residence';
const page = 'chen-bingqian-historic-residence.html';
const folder = 'assets/models/candidates/'+id+'/';
const view = {kind:'archival-facade', listed_year:1994, approximate_loss_year:1994,
  evidence_kind:'reprinted-photograph', evidence_years:[2014,2014]};
const asset = key => ({file:folder+id+'-'+key+'.glb', bytes:42, sha256:'1'.repeat(64)});
const marker = {id, name:'陈炳谦宅', kind:'historical-site', districtId:'310106', district_name:'静安区',
  lng:121.4525, lat:31.2272, historical_view:view, individual_page:page, candidate_manifest:folder+'manifest.json',
  source_feature_ids:{building:[],building_part:[]}, collision_geometry:null, replacement_geometry:null,
  navigation:{listed:false}, assets:{web:asset('web'),lod:asset('lod')}};

test('the historical site retains the current campus and opens its exact verified local page', () => {
  assert.ok(validHistoricalSite(marker));
  for (const individual_page of ['../'+page, '//other.example/'+page, 'other-residence.html']) {
    assert.equal(validHistoricalSite({...marker, individual_page}), false);
  }
  assert.equal(validHistoricalSite({...marker,id:'another-residence'}),false);
  assert.equal(validHistoricalSite({...marker, source_feature_ids:{building:['w1287266688'],building_part:[]}}),false);
  for (const changes of [{building_year:1900},{evidence_years:[1948,2014]},{evidence_years:[1948,1948]}]) {
    assert.equal(validHistoricalSite({...marker,historical_view:{...view,...changes}}),false);
  }
  const [place] = mergeCandidateCityModels([],{schema:'candidate-city-integrations-v1',models:[marker]});
  assert.equal(place.model,undefined);
  assert.equal(walkingPose(place),null);
  assert.equal(historicalSiteCaption(view),'1994年名录登记 · 原建筑约1994年灭失');
  assert.equal(placeDescription(place),'静安区 · 1994年名录登记 · 原建筑约1994年灭失 · 历史照片复原');
});

test('the location dialog labels the 2014 publication and keeps the photograph undated', () => {
  const before = globalThis.window;
  globalThis.window = new EventTarget();
  try {
    const control = () => Object.assign(new EventTarget(),{hidden:false,focus(){}});
    const button=control(), closeButton=control(), title={}, frame={};
    const dialog=Object.assign(new EventTarget(),{open:false,showModal(){this.open=true;}});
    const panel=setupHistoricalView({dialog,button,frame,title,closeButton,onModalChange(){}});
    panel.select(marker);
    button.dispatchEvent(new Event('click'));
    assert.equal(title.textContent,'陈炳谦宅 · 2014年刊载的历史照片，拍摄年份未详');
    assert.equal(frame.src,page+'?embed=history');
  } finally {
    if (before===undefined) delete globalThis.window;
    else globalThis.window=before;
  }
});
