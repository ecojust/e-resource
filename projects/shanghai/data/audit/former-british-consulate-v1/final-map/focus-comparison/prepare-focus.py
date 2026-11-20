from pathlib import Path
import json,hashlib
w=Path('/tmp/consulate103');d=w/'focus-fixture';d.mkdir(exist_ok=True)
j=json.loads((w/'final-inputs/103/data/candidate-city-integrations.json').read_bytes())
id='huangpu-former-british-consulate';r=next(i for i in j['models']if i['id']==id)
bounds={'min':[-6.4,0,-7.3],'max':[19,11.8,.015]}
assert all(r['bounds_glb']['min'][i] <=bounds['min'][i]<bounds['max'][i]<=r['bounds_glb']['max'][i] for i in range(3))
r.update(overview_focus_bounds_glb=bounds,overviewZoom=19.35)
(d/'catalog.json').write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n')
(d/'request.json').write_text(json.dumps({'real_parent_catalog_sha256':hashlib.sha256((w/'final-inputs/103/data/candidate-city-integrations.json').read_bytes()).hexdigest(),'comparison_catalog_sha256':hashlib.sha256((d/'catalog.json').read_bytes()).hexdigest(),'id':id,'immutable_fields_checked':[k for k in r if k not in ['overviewZoom','overview_focus_bounds_glb']],'inputs_changed':{'overviewZoom':19.35,'overview_focus_bounds_glb':bounds},'note':'Browser comparison overrides the candidate directory response only. This is not a production freeze.'},indent=2)+'\n')
src=(w/'check-warm-defaults.cjs').read_text()
src=src.replace("const received=new Set();","const focusBytes=fs.readFileSync(process.env.QA_FOCUS_FIXTURE);\n  result.comparisonCatalogSha256=sha(focusBytes);result.mode='isolated-proposed-south-arcade-framing';\n  const received=new Set();")
src=src.replace("  page.setDefaultTimeout(180000);","  await page.route('**/data/candidate-city-integrations.json*',route=>route.fulfill({status:200,contentType:'application/json',body:focusBytes}));\n  page.setDefaultTimeout(180000);")
src=src.replace("      await card.tap();await view('warm-mobile','full',true);","      await card.tap();await view('focus-mobile','full',true);").replace("await view('warm-desktop','full',true);","await view('focus-desktop','full',true);")
src=src.replace("result.views.push({view:name,...state});save();","result.views.push({view:name,...state});save();assert.ok(state.camera.zoom>19.1);")
(w/'check-focus-defaults.cjs').write_text(src)
