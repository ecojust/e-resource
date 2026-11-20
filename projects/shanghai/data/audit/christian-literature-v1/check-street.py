"""Probe the two flanks and giant pointed surround directly in decoded GLBs."""
from pathlib import Path
import argparse,json,hashlib,runpy,numpy as np
cli=argparse.ArgumentParser(description=__doc__)
for k in ['project','decoded','manifest','out']:cli.add_argument('--'+k,type=Path,required=True)
args=cli.parse_args();doc=json.loads(args.manifest.read_bytes());Scene=runpy.run_path(str(args.project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene'];digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rows=[]
for role in ['raw','full','lod']:
 file=args.manifest.parent/doc['assets'][role]['file'];decoded=file if role=='raw' else args.decoded/(role+'.glb');assert digest(file)==doc['assets'][role]['sha256'];s=Scene(decoded);observed=[]
 def shoot(label,x,z,materials,interval=None):
  hit=s.ray([x,-4,z],[0,1,0],20)
  assert hit and hit['material'] in materials,(role,label,x,z,hit)
  if interval:assert interval[0]<=hit['distance_m']<=interval[1],(role,label,x,z,hit,interval)
  observed.append(dict(name=label,x=x,z=z,material=hit['material'],distance_m=hit['distance_m']))
 for side in (-1,1):
  for bay in range(5):
   x=side*(2.93+(bay+.5)*(9.56-2.93)/5)
   for floor in (0,3,6):
    shoot('wing '+str(side)+' bay '+str(bay+1)+' level '+str(floor+2),x+.10,3.65+floor*3.03+.93,['aged glazing'])
  for floor in (0,3,6):
   shoot('faceted outer pilaster',side*(2.93+2*(9.56-2.93)/5),4.1+floor*3.03,['dark brown tile','weathered mortar'])
  shoot('tall side of continuous stone arch',side*2.05,15.75,['rose stone','rose joint'])
  shoot('inclined upper stone arch face',side*1.31,26.12,['rose stone','rose arris','rose joint'])
  shoot('pointed street-level return',side*2.12,1.1,['recessed door'],[4.60,4.65])
  shoot('storefront glazing',side*5.16,.91,['aged glazing'])
 for level in (0,2,4,6):
  for x in [-.91,.07,1.10]:shoot('three central sash columns',x,3.65+level*3.03+.83,['aged glazing'])
  shoot('cross-floor decorated spandrel',.08,6.08+level*3.03,['decorated spandrel','cast spandrel rib'])
 shoot('head inside pointed archivolt',.02,26.29,['rose joint','decorated spandrel','pale stone cap'],[4.0,5.05])
 shoot('top ashlar of great arch',.08,27.74,['rose stone','rose joint'])
 shoot('pair of entrance leaves',.08,1.46,['recessed door','aged glazing'])
 lab=s.tri[s.mi==s.materials.index('metal sign')];assert len(lab)>1200
 z=lab.mean(1)[:,2];labels=[]
 for name,h in [('English',3.30),('Chinese',2.98)]:
  count=int((np.abs(z-h)<.12).sum());assert count>450,(role,name,count);labels.append({'band':name,'triangles':count})
 rows.append({'variant':role,'sha256':digest(file),'decoded_sha256':digest(decoded),'triangle_count':len(s.tri),'surfaces':observed,'solid_lettering':labels})
args.out.parent.mkdir(exist_ok=True,parents=True);report={'id':doc['id'],'manifest_sha256':digest(args.manifest),'script_sha256':digest(Path(__file__)),'passed':True,'check_count':sum(len(r['surfaces'])+len(r['solid_lettering'])for r in rows),'variants':rows};args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(report['check_count'])
