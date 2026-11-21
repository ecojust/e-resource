import assert from 'node:assert/strict';
import test from 'node:test';
import {historicalSiteCaption, setupHistoricalView, validHistoricalSite} from '../src/historical-view.js';
import {placeDescription, walkingPose} from '../src/precise-registration-ui.js';
import {mergeCandidateCityModels} from '../src/candidate-city-integrations.js';

const id = 'yangpu-yangshupu-power-turbine-hall';
const page = 'yangshupu-turbine-hall.html';
const folder = 'assets/models/candidates/'+id+'/';
const view = {kind:'archival-facade', location_precision:'complex', site_status:'protected-building-unlocated',
  evidence_kind:'dated-photograph', evidence_years:[1926,1926]};
const asset = key => ({file:folder+id+'-'+key+'.glb', bytes:42, sha256:'1'.repeat(64)});
const marker = {id, name:'杨树浦电厂汽机房及4号锅炉房', kind:'historical-site', districtId:'310110', district_name:'杨浦区',
  lng:121.557, lat:31.277, historical_view:view, individual_page:page, candidate_manifest:folder+'manifest.json',
  source_feature_ids:{building:[],building_part:[]}, collision_geometry:null, replacement_geometry:null,
  navigation:{listed:false}, assets:{web:asset('web'),lod:asset('lod')}};

test('the historical site retains the present campus and its extant protected building and opens its exact verified local page', () => {
  assert.ok(validHistoricalSite(marker));
  for (const individual_page of ['../'+page, '//other.example/'+page, 'other-residence.html']) {
    assert.equal(validHistoricalSite({...marker, individual_page}), false);
  }
  assert.equal(validHistoricalSite({...marker,id:'another-residence'}),false);
  assert.equal(validHistoricalSite({...marker, source_feature_ids:{building:['w1287266688'],building_part:[]}}),false);
  for (const changes of [{building_year:1900},{evidence_years:[1948,2014]},{approximate_loss_year:1994},{location_precision:'building'},{site_status:'lost'}]) {
    assert.equal(validHistoricalSite({...marker,historical_view:{...view,...changes}}),false);
  }
  const [place] = mergeCandidateCityModels([],{schema:'candidate-city-integrations-v1',models:[marker]});
  assert.equal(place.model,undefined);
  assert.equal(walkingPose(place),null);
  assert.equal(historicalSiteCaption(view),'厂区范围索引 · 保护建筑现存，照片对应的具体楼翼待考');
  assert.equal(placeDescription(place),'杨浦区 · 厂区范围索引 · 保护建筑现存，照片对应的具体楼翼待考 · 1926年拍摄');
});

test('the location dialog attributes the image to the documented exposure year', () => {
  const before = globalThis.window;
  globalThis.window = new EventTarget();
  try {
    const control = () => Object.assign(new EventTarget(),{hidden:false,focus(){}});
    const button=control(), closeButton=control(), title={}, frame={};
    const dialog=Object.assign(new EventTarget(),{open:false,showModal(){this.open=true;}});
    const panel=setupHistoricalView({dialog,button,frame,title,closeButton,onModalChange(){}});
    panel.select(marker);
    button.dispatchEvent(new Event('click'));
    assert.equal(title.textContent,'杨树浦电厂汽机房及4号锅炉房 · 1926年拍摄的历史照片');
    assert.equal(frame.src,page+'?embed=history');
  } finally {
    if (before===undefined) delete globalThis.window;
    else globalThis.window=before;
  }
});
