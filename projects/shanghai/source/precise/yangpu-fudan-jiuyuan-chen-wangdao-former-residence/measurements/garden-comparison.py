"""Create a photo-matched diagram from the actual released mesh, independent of the builder."""
import argparse,json,runpy
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
LOADER=runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
COLORS={'yellow roughcast':[226,193,138],'green glazed pan tiles':[117,122,103],'grey beige coping':[170,160,145],'dark green steel':[43,53,51],'reflected grey blue glazing':[94,108,117],'shaded olive glazing':[78,91,86],'recessed vent':[50,54,47],'painted rainwater goods':[71,66,55]}
def draw(obj,P,size):
    s=LOADER(obj);tri=s.tri
    v=np.concatenate((tri,np.ones((*tri.shape[:2],1))),axis=2)@P.T
    screen=v[:,:,:2]/v[:,:,2:];order=np.argsort(v[:,:,2].mean(axis=1))[::-1]
    n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);ln=np.linalg.norm(n,axis=1)[:,None]
    n/=np.maximum(ln,1.e-15);lighting=np.clip(.81+.18*(n@np.array([-.15,-.6,.78])),.57,1.03)
    img=Image.new('RGB',size,'#e9e9e3');d=ImageDraw.Draw(img)
    eye=-np.linalg.solve(P[:,:3],P[:,3]);front=(n*(eye-tri.mean(axis=1))).sum(axis=1)>0
    for i in order:
        if not front[i]:continue
        pts=[tuple(p) for p in screen[i]];key=s.materials[s.mi[i]].split(' | ')[1];col=tuple(int(c*lighting[i]) for c in COLORS[key]);d.polygon(pts,fill=col)
    return img
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('model',type=Path);a.add_argument('output',type=Path);a.add_argument('--photo',type=Path);opt=a.parse_args()
    fit=json.loads((HERE/'garden-front-registration.json').read_bytes());im=draw(opt.model,np.array(fit['photos']['fayhoo']['matrix']),(1008,756))
    if opt.photo:
        ph=Image.open(opt.photo).convert('RGB').resize((1008,756));joint=Image.new('RGB',(1344,528),'white');joint.paste(ph.resize((672,504)),(0,0));joint.paste(im.resize((672,504)),(672,0))
        d=ImageDraw.Draw(joint);d.text((11,510),'Fayhoo / Wikimedia Commons, 9 November 2019 / CC BY-SA 3.0',fill='black');d.text((684,510),'Released mesh projected from the registered garden photograph',fill='black');im=joint
    im.save(opt.output,quality=88)
