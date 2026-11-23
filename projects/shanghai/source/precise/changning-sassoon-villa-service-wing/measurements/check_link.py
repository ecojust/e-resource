"""Check the exposed connecting roof and supporting bays in the two photographic records."""
from pathlib import Path
import numpy as np
import json,runpy,hashlib,sys
m=Path(__file__).resolve().parent
sys.path.insert(0,str(m))
from wing_frame import Camera
from check_courtyard import HELPER
pts={'design':{'plain tile':[(394,161),(406,178),(432,181),(467,185),(486,177)],'garden brick':[(379,216),(385,219),(428,216),(439,218)],'stained doors':[(398,214),(410,219),(464,219),(482,220)]},
     'album':{'plain tile':[(654,537),(673,549),(694,543),(730,548),(746,563)]}}
def check(src):
 sc=runpy.run_path(str(HELPER))['SerialScene'](src);rows=[]
 for k,types in pts.items():
  c=Camera(k)
  for typ,points in types.items():
   for uv in points:
    h=sc.ray(c.C,c.ray(uv),300);material=h['material'] if h else None
    rows.append({'station':k,'uv':uv,'observed':typ,'first_hit':material,'expected':bool(material and typ in material)})
 return {'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'camera_sha256':hashlib.sha256((m/'wing-cameras.json').read_bytes()).hexdigest(),'total':len(rows),'direct':sum(r['expected'] for r in rows),'rays':rows}
if __name__=='__main__':
 p=Path(sys.argv[1]);out=Path(sys.argv[2]);j=check(p);out.write_text(json.dumps(j,indent=2)+'\n');print(j['direct'],j['total'])
