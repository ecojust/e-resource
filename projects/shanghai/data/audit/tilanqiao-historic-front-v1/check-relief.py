"""Read the three serialized variants and sample documented layers of the façade."""
from pathlib import Path
import argparse,json,hashlib,runpy
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);p.add_argument('--decoded',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();Scene=runpy.run_path(str(a.project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene'];doc=json.loads(a.manifest.read_bytes());rows=[];proof={}
def digest(f):return hashlib.sha256(f.read_bytes()).hexdigest()
for role in ['raw','full','lod']:
 src=a.manifest.parent/doc['assets'][role]['file'];assert doc['assets'][role]['sha256']==digest(src);actual=src if role=='raw' else a.decoded/(role+'.glb');s=Scene(actual);obs=[]
 def probe(label,x,z,allowed,context='street'):
  hit=s.ray([x,-4,z],[0,1,0],20) if context=='street'else s.ray([x,4,z],[0,-1,0],20)
  passed=bool(hit and hit['material']in allowed)
  if not passed:raise AssertionError((role,label,hit))
  obs.append({'name':label,'origin_m':[x,-4 if context=='street'else 4,z],'material':hit['material'],'hit_'+context+'_depth_m':round(float(hit['distance_m']),5)})
 for side in [-1,1]:
  for z in [2,4,7,9.5]:
   probe('fluted edge stone',7.17*side,z,['weathered limestone'])
  probe('grooved pier base',7.7*side,.6,['honed buff stone'])
  probe('stone under brick field',3.48*side,1.13,['honed buff stone'])
  probe('brick surround above stone',3.58*side,2.12,['mortar','brown brick','red brick','russet brick'])
 for z,allowed in [(7.27,['honed buff stone']),(7.43,['pale arris']),(8.18,['weathered limestone']),(8.75,['pale arris']),(9.23,['honed buff stone'])]:probe('horizontal header profile',.5,z,allowed)
 probe('left commemorative stone',-5.6,2.5,['pale marker']);probe('name tablet margin',7.335,2.77,['plaque porcelain'])
 probe('lower dark field',.70,2.38,['dark panel']);probe('central stone return',2.39,4.0,['honed buff stone'])
 probe('plain unobserved rear surface',0,4,['section'],'rear')
 labels=s.tri[s.mi==s.materials.index('plaque lettering')]
 assert len(labels)>500
 z=labels.mean(1)[:,2];xx=labels.mean(1)[:,0]
 assert xx.min()>7.32 and xx.max()<7.83
 glyphs=[]
 for i in range(8):
  mid=6.0-i*.437;count=int(((z>mid-.22)&(z<mid+.22)).sum());assert count>70;glyphs.append({'panel_row':i+1,'triangles':count})
 rows.append(dict(role=role,asset_sha256=digest(src),decoded_sha256=digest(actual),triangles=len(s.tri),architectural_probes=obs,tablet_glyph_groups=glyphs))
proof={'id':doc['id'],'manifest_sha256':digest(a.manifest),'script_sha256':digest(Path(__file__)),'passed':True,'variants':rows,'probe_count':sum(len(v['architectural_probes'])+len(v['tablet_glyph_groups'])for v in rows)}
a.out.write_text(json.dumps(proof,indent=2)+'\n');print(proof['probe_count'])
