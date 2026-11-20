"""Coordinates of the author's six paired recessed openings on the splayed wall, in meters."""
from pathlib import Path
import json,math,numpy as np
from hashlib import sha256
a=np.array([-33.15233,11.16454]);c=np.array([-22.02035,0.0]);half=np.linalg.norm(c-a)/2;t=(c-a)/(2*half);normal=np.array([t[1],-t[0]])
co=math.cos(math.radians(32));si=math.sin(math.radians(32));rot=np.array([[co,-si],[si,co]])
def point(u,z,depth=-.31):
 v=(((a+c)/2+t*u+depth*normal)-np.array([-11.81246,7.38124]))@rot.T
 return [*v,z]
out={}
for i,(z,h) in enumerate([(7.20,2.13),(10.06,1.71),(13.27,2.05),(17.04,2.02),(20.97,2.08),(25.15,2.02)]):
 start=-half+4.72;end=half+.04;w=(end-start)/2
 for bay in (0,1):
  x=start+w*bay+(.20 if bay else .07);xx=start+w*(bay+1)-(.07 if bay else .20)
  out[f'band {i+1}, bay {bay+1}']={'vertices':[point(u,h0)for u,h0 in [(x,z),(xx,z),(xx,z+h),(x,z+h)]]}
here=Path(__file__).resolve().parent
r=here.parents[4]/'source/precise/huangpu-chekiang-first-commercial-bank/source/frontage.py'
(here/'windows.json').write_text(json.dumps({'source_sha256':sha256(r.read_bytes()).hexdigest(),'windows':out}))
