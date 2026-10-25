"""Independent projected-footprint alignment check; not a survey validation."""
from pathlib import Path
import json, random, math, argparse
import numpy as np
import pyogrio
from pyproj import Transformer
from shapely import from_wkb, STRtree, make_valid
from shapely.geometry import shape
from shapely.ops import transform
from shapely.affinity import translate
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[2]);parser.add_argument('--raw',type=Path);args=parser.parse_args();PROJECT=args.project;ROOT=PROJECT/'data'; proj=Transformer.from_crs(4326,3857,always_xy=True).transform
sources=[]
for path in (args.raw or ROOT/'heights/cmab/raw').rglob('*.shp'):
 info=pyogrio.read_info(path);sources.append((path,info['total_bounds']))
if not sources:raise SystemExit('Download the original CMAB shapefiles first; see data/heights/REBUILD.md, or use --raw /path/to/shapefiles')
trials={'declared_3857':(0,0),'gcj02_shift_hypothesis':(-500,250),'opposite_shift_control':(500,-250),'100m_control':(100,100)}
reports=[]
for file in sorted((PROJECT/'data/neighborhoods').glob('*.geojson')):
 d=json.loads(file.read_text()); refs=[]
 for f in d['features']:
  g=transform(proj,shape(f['geometry']));g=make_valid(g)
  if g.area>40 and g.geom_type in ['Polygon','MultiPolygon']:refs.append((f,g))
 random.Random(20261025).shuffle(refs);refs=refs[:80]
 bounds=transform(proj,shape({'type':'Polygon','coordinates':[[[d['bbox'][0],d['bbox'][1]],[d['bbox'][2],d['bbox'][1]],[d['bbox'][2],d['bbox'][3]],[d['bbox'][0],d['bbox'][3]],[d['bbox'][0],d['bbox'][1]]]]})).bounds
 query=(bounds[0]-800,bounds[1]-800,bounds[2]+800,bounds[3]+800)
 cmab=[]
 for path,b in sources:
  if b[2]<query[0] or b[0]>query[2] or b[3]<query[1] or b[1]>query[3]:continue
  meta,table=pyogrio.read_arrow(path,bbox=query,columns=['Height','merged_id']);column=meta.get('geometry_name') or 'wkb_geometry'
  for g in from_wkb(table[column].to_numpy()):
   g=make_valid(g)
   if not g.is_empty:cmab.append(g)
 tree=STRtree(cmab);result={}
 for label,(dx,dy) in trials.items():
  scores=[]
  for f,reference in refs:
   g=translate(reference,xoff=-dx,yoff=-dy);best=0
   for idx in tree.query(g,predicate='intersects'):
    candidate=cmab[idx];inter=g.intersection(candidate).area;union=g.area+candidate.area-inter
    if union>0:best=max(best,inter/union)
   scores.append(best)
  result[label]={'median_iou':round(float(np.median(scores)),4),'matched_at_iou_0_3':sum(s>=.3 for s in scores),'matched_at_iou_0_5':sum(s>=.5 for s in scores),'tested':len(scores)}
 row={'district_id':file.stem,'name':d['metadata'].get('district_name'),'cmab_candidates':len(cmab),'trials':result};reports.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
report={'method':'Compare up to80 deterministic sampled Overture footprints per district against CMAB polygons in declared EPSG3857. Each reference is matched by maximum polygon IoU. Translation trials are controls only, not applied to published data. This checks coordinate consistency, not true footprint accuracy.','trial_cmab_translations_mercator_m':trials,'reports':reports}
(ROOT/'audit/cmab-alignment.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
