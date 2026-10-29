import sys,json,gzip,importlib.util
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,MultiPolygon
from shapely.strtree import STRtree
import argparse
ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();P=args.project.resolve();args.out.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(P/'source/city'));from build_district_models import cleaned_ring,Mesh
from roof_geometry import append_roof_shell
spec=importlib.util.spec_from_file_location('engine',P/'source/city/detail/geometry_engine.py');E=importlib.util.module_from_spec(spec);spec.loader.exec_module(E)
D=P/'assets/city-detail/macros/14-13719-6695';table=json.loads(gzip.decompress((D/'feature-table.json.gz').read_bytes()));near=next(n for n in json.loads((D/'READY.json').read_text())['near'] if 3433 in n['featureLocalIds']);fs=[]
for row in table['features']:
 f=dict(row);polys=f['geometry']['coordinates'] if f['geometry']['type']=='MultiPolygon' else [f['geometry']['coordinates']];f['rings']=[[r for r in [cleaned_ring(r,table['origin'],j==0) for j,r in enumerate(poly)] if r] for poly in polys];gs=[Polygon(r[0],r[1:]) for r in f['rings']];f['local_geometry']=gs[0] if len(gs)==1 else MultiPolygon(gs);f['local_id']=f['localId'];f['eave']=f['height']-f['roof']['roof_height'] if f['roof'] else f['height'];fs.append(f)
tree=STRtree([f['local_geometry'] for f in fs])
def roof(rings,f):
 rm,wm=Mesh(),Mesh();r=f['roof'];append_roof_shell(rm,wm,rings,base=f['base'],height=f['height'],roof_height=r['roof_height'],roof_shape=r['roof_shape'],ridge_unit=r.get('ridge_unit'),down_slope_unit=r.get('down_slope_unit'));return rm,wm
out=[];triangles=[]
for f in fs:
 if f['local_id'] not in near['featureLocalIds']:continue
 ins,unique=E.feature_near(f,fs,tree,roof)
 for bi,batch in enumerate(unique):
  for tri in np.array(batch.idx).reshape(-1,3):triangles.append({'owner':f['local_id'],'batch':bi,'points':np.array(batch.pos,dtype=np.float32)[tri].tolist()})
 for kind,rows in ins.items():
  for row in rows:out.append({'owner':f['local_id'],'kind':kind,'T':np.array(row[0],dtype=np.float32).tolist(),'R':np.array(row[1],dtype=np.float32).tolist(),'S':np.array(row[2],dtype=np.float32).tolist()})
(args.out/'instance-reference.json').write_text(json.dumps(out));(args.out/'triangle-reference.json').write_text(json.dumps(triangles));print(len(out),len(triangles))
