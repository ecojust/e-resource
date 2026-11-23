"""Test first intersections on issued and independently decoded files, looking up source component names only after matching position and material."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
from photo_ray_mesh import load_triangles,ProjectedMesh
here=Path(__file__).absolute().parent
parser=argparse.ArgumentParser()
for k in ('geometry','packaged','stations','output'):
 parser.add_argument(k,type=Path)
args=parser.parse_args()
def read(p):return json.loads(p.read_bytes())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
manifest=read(args.packaged/'manifest.json')
args.output.mkdir(exist_ok=True,parents=True)
stations=read(args.stations);summary={}
for level,original,rfile in [('raw','full',manifest['assets']['raw']['file']),('full','full','decoded-full.glb'),('lod','lod','decoded-lod.glb')]:
 geom=args.geometry/(original+'-source.glb');source=ProjectedMesh(geom,read(geom.with_suffix('.geometry.json')))
 artifact=args.packaged/manifest['assets'][level]['file'];assert sha(artifact)==manifest['assets'][level]['sha256']
 tested=args.packaged/rfile;mesh=ProjectedMesh.__new__(ProjectedMesh);mesh.tri,mesh.labels,materials,mesh.asset=load_triangles(tested)
 mesh.parts=[dict(label=None,material=m) for m in materials]
 out={'issued':manifest['assets'][level],'tested_geometry':mesh.asset,'authored_geometry':source.asset,'cameras_sha256':sha(args.stations),'source_component_transfer':'Only when the independent first hit on the same photographic ray agrees on material, within 12 mm of the authored point. A failed centre sample remains in the evidence; nearest is the previously recorded independent offset.','photo_tables':{},'stations':{}}
 refgen=here/'check.py'
 for setname,table in [('main','independent-source-pixels.json'),('plaque','independent-pier-plaque.json')]:
  point_file=here/table;out['photo_tables'][setname]=sha(point_file)
  out_name=args.output/(original+'-'+setname+'-authored.json')
  if not out_name.exists() or read(out_name)['mesh']['sha256']!=source.asset['sha256']:
   import subprocess,sys
   subprocess.run([sys.executable,'-B',refgen,geom,args.stations,out_name,'--points',point_file],check=True)
  ref=read(out_name);marks=[]
  for name,rows in ref['stations'].items():
   mesh.station(stations[name]);source.station(stations[name])
   for row in rows:
    uv=row['uv'];points={'centre':uv}
    if row['nearby'] is not None:points['nearest_authored_matches']=[a+b for a,b in zip(uv,row['nearby']['delta'])]
    results={}
    for role,(u,v) in points.items():
     a=source.hit(u,v);b=mesh.hit(u,v);delta=round(float(np.linalg.norm(np.array(a['xyz'])-b['xyz'])),6)if a and b else None
     agree=delta is not None and delta<=.012 and a['material']==b['material']
     results[role]={'uv':[u,v],'authored':a,'decoded':b,'separation_m':delta,'matching_surface':agree,'expected_component':bool(agree and (role!='centre' or row['direct']))}
    marks.append({'station':name,'feature':row['feature'],'source_nearest_offset':row['nearby']['delta'] if row['nearby'] else None,'observations':results})
  out['stations'][setname]=marks
 all_rows=[v for group in out['stations'].values()for v in group];counts={'total':len(all_rows),'direct':sum(r['observations']['centre']['expected_component']for r in all_rows),'four_px_or_less':sum(bool(r['observations'].get('nearest_authored_matches',{}).get('expected_component') and sum(n*n for n in r['source_nearest_offset'])<=16)for r in all_rows)}
 out['result']=counts;p=args.output/(level+'-first-hits.json');p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');summary[level]={'file':p.name,'sha256':sha(p),**counts}
(args.output/'registered-material-validation.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary)
