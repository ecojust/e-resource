"""Report projected sample positions, road-/roof-level modelling limit, and actual label intersections."""
from pathlib import Path
import json,hashlib
w=Path(__file__).parent;a=Path('/workspace/e-resource/projects/shanghai/data/audit/pure-heart-church-v1');o=a/'final-map-24138'
read=lambda f:json.loads(f.read_bytes())
hist=read(a/'overview-sightlines.json');d=read(o/'main-browser.json');models={}
for v in d['views']:
 points=v['courtWitnesses']['points'];models[v['view']]={'camera':v['camera'],'viewport':v['viewport'],'samples':len(points),'samples_inside_viewport':sum(int(p['inViewport'])for p in points),'outside_the_screen':[p['name']for p in points if not p['inViewport']], 'labels_covering_samples':{p['name']:p['coveringBeaconIds']for p in points if p['coveringBeaconIds']},'interface_covering_samples':{p['name']:p['coveringHud']for p in points if p['coveringHud']}}
raw={'model':d['id'],'purpose':'Actual label and HUD rectangles are compared with frozen facade feature coordinates using the active WebGL map transform. Independent original neighboring buildings are evaluated in the preceding study. Point overlap does not establish the visibility of an entire feature.', 'main_browser_sha256':hashlib.sha256((o/'main-browser.json').read_bytes()).hexdigest(),'previous_frozen_obstruction_study_sha256':hashlib.sha256((a/'overview-sightlines.json').read_bytes()).hexdigest(),'previous_neighbor_volume_result':{c['view']:{p['feature']:p['obstructions']for p in c['probes']if p['obstructions']}for c in hist['cases']['default']},'views':models}
(o/'facade-witnesses.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(models,ensure_ascii=False,indent=2))
