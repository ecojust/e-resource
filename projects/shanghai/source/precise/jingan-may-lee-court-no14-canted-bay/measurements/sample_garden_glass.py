"""Repeat the per-pane 3×3 colour readings with a locally supplied original."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from garden_main_corner import SETBACK, WINDOWS, X
from fit_garden_corner import project
def sample(image):
    record=json.loads((HERE/'garden-corner-camera.json').read_text())
    if sha256(image.read_bytes()).hexdigest()!=record['source_sha256']:
        raise ValueError('Original garden photo 93 is required at its native 690 × 821 size')
    photo=np.array(Image.open(image).convert('RGB'))
    P=np.array(record['main_corner_projection']);eye=np.array(record['camera_position'])
    results={}
    for name,a,b,lo,hi,rails,bars in WINDOWS:
        edges=(a+.13,*bars,b-.13);heights=(lo+.135,*rails,hi-.12);values=[]
        for row,(z0,z1) in enumerate(zip(heights,heights[1:])):
            for col,(near,far) in enumerate(zip(edges,edges[1:])):
                pos=np.array([X+SETBACK+.0405,(near+far)/2,(z0+z1)/2])
                u,v=np.rint(project(P,pos)).astype(int)
                direction=pos-eye;face=eye+direction*((X-eye[0])/direction[0])
                clear=a+.103<face[1]<b-.103 and lo+.11<face[2]<hi-.089 and not(name=='ground' and v>641)
                rgb=np.median(photo[v-1:v+2,u-1:u+2],axis=(0,1))
                lum=round(float(rgb@[.2126,.7152,.0722]),1)
                values.append(dict(row=row,col=col,pixel=[int(u),int(v)],clear=bool(clear),
                                   median_rgb=rgb.astype(int).tolist() if clear else None,luma=lum if clear else None))
        for v in values:
            nearest=min((c for c in values if c['clear']),key=lambda c:(abs(c['row']-v['row'])*2+
                abs(c['col']-v['col']),abs(c['col']-v['col'])))
            v['tone']=int(np.searchsorted([52,65,79,96],nearest['luma']))
            if not v['clear']:v['adopted_cell']=[nearest['row'],nearest['col']]
        results[name]=values
    return results
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('original',type=Path);args=ap.parse_args()
    result=sample(args.original)
    expected=json.loads((HERE/'garden-side-glass-tones.json').read_text())['levels']
    if result!=expected:raise ValueError('Native sample differs from the recorded source measurements')
    print('Verified 43 measured and 32 locally estimated pane colours')
