"""Check frozen wall rectangles/holes against the published geometry source."""
import argparse,json,hashlib,math
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--geometry-source',type=Path,required=True);ap.add_argument('--spec',type=Path,default=Path(__file__).with_name('wall-core-input.json'));ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
spec=json.loads(a.spec.read_text());text=a.geometry_source.read_text();expected=spec['baseline']['source/bund/chartered_bank/photo-v4.3/build_geometry.py']['sha256'];assert hashlib.sha256(a.geometry_source.read_bytes()).hexdigest()==expected
captured=[]
def capture(x0,x1,z0,z1,holes,mapper=None,masonry=False):
 assert masonry;captured.append({'rectangle':[x0,x1,z0,z1],'holes':[list(h) for h in holes],'offset':0 if mapper is None else mapper(0,0,0)[1]})
# These small known source sections contain only arithmetic, loops and the
# captured wall_rect calls; the full Blender generator is not executed.
context={'W':math.dist(*spec['coordinate_basis']['front_edge']),'wall_rect':capture}
first=text.index('central=5.05;side=11.30');last=text.index('\n\n',text.index('wall_rect(-W/2',first));exec(compile(text[first:last],str(a.geometry_source),'exec'),context)
first=text.index('atticW=15.8;atticY=3.2;atticZ=24.43');last=text.index('\nfor k in range(9):rect_window',first);exec(compile(text[first:last],str(a.geometry_source),'exec'),context)
assert len(captured)==len(spec['walls'])==2
for c,w in zip(captured,spec['walls']):
 assert c['rectangle']==w['rectangle'] and c['holes']==w['holes'] and c['offset']==w['depth_offset']
assert 'z*1.037) for x,y,z in vertices]' in text
report={'source_sha256':expected,'matching_wall_definitions':2,'matching_original_holes':sum(len(x['holes']) for x in captured),'vertical_scale':1.037,'method':'Evaluate only frozen arithmetic/opening-definition snippets with a capture-only wall_rect; no model is regenerated.'}
a.output.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
