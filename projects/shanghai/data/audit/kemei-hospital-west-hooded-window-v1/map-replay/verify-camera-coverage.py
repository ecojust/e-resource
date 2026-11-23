"""Verify the signed ordinary overview and the narrow lightwell views without discarding occlusions."""
from pathlib import Path
from hashlib import sha256
import json
w=Path(__file__).parent
read=lambda f:json.loads(f.read_bytes())
hashof=lambda f:sha256(f.read_bytes()).hexdigest()
camera=read(w/'map-camera-proof.json'); witness=read(w/'actual-camera-city-triangles.json')
assert witness['modules_from']==31273 and witness['contract_sha256']==hashof(w.parent/'final-placement-contract.json')
key={(r['device'], r['feature']):r for r in witness['results']}
assert len(key)==len(witness['results'])==120
coverage={'desktop':{},'mobile':{}}
views={}
for view in camera['winner']['scores']:
    probes=[]
    for probe in view['probes']:
        event=key[(view['screen'],probe['feature'])]
        clear=probe['inside'] and probe['self_clear'] and event['city_mesh_sight_clear']
        probes.append({'feature':probe['feature'],'visible':clear,'in_view':probe['inside'],'clear_of_modeled_window':probe['self_clear'],
                       'original_near_clear':event['first']['near'] is None,'original_far_clear':event['first']['far'] is None,
                       'pixel':probe['px'],'view_depth_m':probe['depth_m']})
        if clear:coverage[view['device']].setdefault(probe['feature'],[]).append(view['view'])
    views[view['screen']]={'camera':view['camera'],'eye_local_m':view['camera_local'],'visible':sum(p['visible']for p in probes),'checks':probes}
missing=[(k,t['feature'])for k in coverage for t in camera['winner']['scores'][0]['probes'] if t['feature'] not in coverage[k]]
out={'overview':{device:views[device+'-overview']['visible']for device in coverage},
     'coverage':coverage,'unseen':missing,'passed':not missing,'views':views,'camera_sha256':hashof(w/'map-camera-proof.json'),
     'signed_original_sightlines_sha256':hashof(w/'actual-camera-city-triangles.json'),'contract_sha256':witness['contract_sha256'],
     'coordinate_system':'MapLibre center, bearing, pitch, zoom and elevation. X runs along the documented window wall, Y inward, Z metres above city ground.'}
t=w/'combined-window-visibility.json';tmp=t.with_suffix('.tmp');tmp.write_text(json.dumps(out,indent=2)+'\n');tmp.replace(t)
print(out['overview'],{k:len(v)for k,v in coverage.items()},missing)
if missing:raise SystemExit(1)
