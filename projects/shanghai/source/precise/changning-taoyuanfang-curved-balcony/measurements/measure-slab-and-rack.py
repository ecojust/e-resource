"""Measure the lowest bright balcony moulding and locate the four drying rods in the reference."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates,gaussian_filter1d
here=Path(__file__).absolute().parent;sys.path.insert(0,str(here.parent/'source'))
from geometry_reference import DATA,on_plane
COARSE=np.array([[401,407],[429,399],[459,389],[483,379],[512,367],[552,352],[602,336],[649,324],[701,311],[745,297],[772,290],[811,281]])
TRAIN=[402,417,434,452,471,487,511,543,579,621,663,705,740,761]
SCALE=np.array([5312/1062,2988/597])
def lower_bead(im,u):
    initial=np.interp(u,COARSE[:,0],COARSE[:,1])
    y=np.arange(initial-4.3,initial+4.4,.09)
    shifts=np.arange(-1.55,4.76,.15);xx=u*SCALE[0]
    p=np.stack([map_coordinates(im,[(y[:,None]+shifts)*SCALE[1],np.full((len(y),len(shifts)),xx+du)],order=1)for du in [-3,0,3]]).mean(axis=0)
    bright=p[:,(shifts>=-.95)&(shifts<=-.24)].mean(1)
    dark=p[:,(shifts>=.25)&(shifts<=1.15)].mean(1)
    return_glint=p[:,(shifts>=1.2)&(shifts<=4.1)].max(1)
    score=bright-dark-.62*np.maximum(0,return_glint-dark-12)
    ix=int(score.argmax());return dict(u=u,v=float(y[ix]),contrast=float(bright[ix]-dark[ix]),confidence_score=float(score[ix]))
def load(path):
    assert hashlib.sha256(path.read_bytes()).hexdigest()==DATA['photo_sha256']
    image=Image.open(path);return np.asarray(image.convert('L'))
if __name__=='__main__':
    im=load(Path(sys.argv[1]));train=[lower_bead(im,u)for u in TRAIN]
    assert all(r['contrast']>15 for r in train)
    # Far right is crossed by several service wires; the last terminal is an observed limit only.
    endpoints=[[397,409.4],[810,280.7]]
    pixels=[endpoints[0],*[[r['u'],r['v']]for r in train],endpoints[1]]
    xyz=on_plane(pixels,2,-.37)
    rows=dict(photo_sha256=DATA['photo_sha256'],lower_bead_elevation_m=-.37,balcony_paving_elevation_m=-.135,
              training=train,terminal_controls_px=endpoints,edge_samples_xy_m=xyz[:,:2].tolist(),
              minimum_confidence=min(r['confidence_score']for r in train),
              limitations='模型着重两道浅色线脚和缓转的沿街边缘。东端最后约50个工作像素受电缆遮挡，端部按最后可见边界收束。')
    (here/'slab-edge.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    print('lower bead',[(r['u'],round(r['v'],2),round(r['contrast']))for r in train]);print(np.round(xyz[:,:2],3))
