"""Hold the door-head ornament out of a 2015/2020 image registration."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates
from scipy.optimize import least_squares

HERE=Path(__file__).resolve().parent
# Left and right door opening, four edges of the dark stair lights, then both edges
# of the horizontal plaster stringcourse at the north edge of the staircase.
ANCHORS=[([407,428],[516,380]),([631,426],[680,380]),
         ([413,111],[527,143]),([496,108],[591,144]),([540,106],[626,143]),([618,102],[683,142]),
         ([845,151],[827,182]),([843,237],[825,230]),([224,173],[381,190]),([222,246],[376,241])]

def evaluate(before,after,detail):
    src,dst=np.array(ANCHORS,dtype=float).transpose(1,0,2)
    mid=np.array([520.,300.])
    def transform(v,points):
        p=(np.asarray(points)-mid)/300.
        m=np.r_[v,1.].reshape(3,3)
        r=np.column_stack([p,np.ones(len(p))])@m.T
        return r[:,:2]/r[:,2,None]
    init=[220,0,600,0,230,285,0,0]
    fit=least_squares(lambda v:(transform(v,src)-dst).ravel(),init,loss='soft_l1',f_scale=1.7)
    g=np.array(Image.open(after).convert('L'),dtype=float)
    gy,gx=np.gradient(gaussian_filter(g,1.3))
    rows=[]
    for key in ['wave_upper_profile_px','cartouche_outline_px']:
        points=np.array(detail[key],dtype=float)
        mapped=transform(fit.x,points)
        for i in range(1,len(points)-1):
            u,v=points[i]
            if key.startswith('cartouche') and 216<=v<=253:continue
            zn=mapped[i+1]-mapped[i-1];normal=np.array([-zn[1],zn[0]])/np.linalg.norm(zn)
            shifts=np.linspace(-5,5,41)
            q=mapped[i]+shifts[:,None]*normal
            grad=np.abs(map_coordinates(gx,[q[:,1],q[:,0]],order=1)*normal[0]+map_coordinates(gy,[q[:,1],q[:,0]],order=1)*normal[1])
            j=int(grad.argmax())
            rows.append(dict(profile=key,pixel_2015=points[i].tolist(),predicted_2020=mapped[i].tolist(),
                             offset_to_2020_edge_px=float(shifts[j]),magnitude=float(grad[j]),interior_peak=bool(0<j<len(shifts)-1 and grad[j]>=2.5)))
    good=[abs(r['offset_to_2020_edge_px'])for r in rows if r['interior_peak']]
    return dict(source_images=[{'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [before,after]],
                fit='Ten door, window and stringcourse marks register the images. The two cast profiles are withheld. Search five pixels along the normal and retain an interior peak with at least 2.5 grey levels per pixel. Wire-covered cartouche marks are excluded.',
                image_pairs=ANCHORS,fit_anchor_errors_px=np.linalg.norm(transform(fit.x,src)-dst,axis=1).tolist(),
                sampled=len(rows),visible=len(good),median_absolute_offset_px=float(np.median(good)),
                p90_absolute_offset_px=float(np.percentile(good,90)),samples=rows)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('photo_2015',type=Path);p.add_argument('photo_2020',type=Path);p.add_argument('profile',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();r=evaluate(a.photo_2015,a.photo_2020,json.loads(a.profile.read_bytes()));a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(r['sampled'],r['visible'],r['median_absolute_offset_px'],r['p90_absolute_offset_px'],np.round(r['fit_anchor_errors_px'],1))
