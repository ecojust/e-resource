"""Sample the preserved art panel and lintel edges in the original Gao photograph."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates
from PIL import Image

OFFSET=np.array([1360.,735.])
INITIAL = [[166,140],[250,140],[307,193],[307,280],[249,340.7],[155,342.5],[104,285],[105,198]]
def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def fit_edge(im,p,q,radius):
    along=q-p
    normal=np.array([-along[1],along[0]])/np.linalg.norm(along)
    base=p+np.linspace(.13,.87,max(13,int(np.linalg.norm(along)/3)))[:,None]*along
    offsets=np.linspace(-radius,radius,65)
    candidates=base[:,None,:]+ offsets[None,:,None]*normal
    gray=map_coordinates(im,np.stack([candidates[:,:,1],candidates[:,:,0]]),order=1)
    slopes=abs(np.gradient(gray,offsets,axis=1))
    chosen=offsets[np.argmax(slopes,axis=1)]
    pts=base+np.expand_dims(chosen,1)*normal
    weights=np.max(slopes,axis=1).clip(1,20)
    for _ in range(5):
        cen=np.average(pts,axis=0,weights=weights)
        _,_,v=np.linalg.svd((pts-cen)*np.sqrt(weights[:,None]),full_matrices=False)
        n=v[-1];delta=(pts-cen)@n
        weights=np.minimum(1.,1.25/np.maximum(np.abs(delta),1e-8))*np.max(slopes,axis=1).clip(1,20)
    coeff=np.r_[n,-cen@n]
    return coeff,dict(pixels_sampled=len(pts),median_normal_error_px=float(np.median(np.abs(delta))),
                      p95_normal_error_px=float(np.quantile(np.abs(delta),.95)))

def read(photo):
    im=Image.open(photo).convert('L')
    assert im.size==(3449,2696) and sha(photo)=='5a6b323801d642de980b47e24334b7fdcdf2475907ac4bee0de06dcf9a8d37e2'
    local=np.asarray(im.crop((1360,735,1790,1120)),float)
    local=gaussian_filter(local,.98)
    pts=np.array(INITIAL,float)
    lines,stats=zip(*(fit_edge(local,a,b,1.65 if i==4 else 4.) for i,(a,b) in enumerate(zip(pts,np.roll(pts,-1,axis=0)))))
    outline=[]
    for i in range(8):
        meet=np.cross(lines[i-1],lines[i]);outline.append(np.round(meet[:2]/meet[2]+OFFSET,3).tolist())
    return dict(native_size_px=list(im.size),raw_sha256=sha(photo),source_url='https://blog.sina.com.cn/s/blog_5d1bdf480102y3oa.html',
        attribution='高参88，2018年6月27日。参考原图只用于数值量测。',source_exif_time=Image.open(photo).getexif().get_ifd(34665).get(36867),
        tablet_outline_native_px=outline,edges=list(stats),manual_edge_guides_native_px=(pts+OFFSET).tolist(),
        hood_front_fascia_outline_native_px=(np.array([[59,70],[355,64],[360,78],[358,163],[356,173],[308,173],[307,128],[109,133],[108,171],[58,173]])+OFFSET).tolist(),
        hood_upper_cap_ridge_native_px=(np.array([[59,70],[73,66],[84,53],[337,50],[343,59],[355,64]])+OFFSET).tolist(),
        tablet_lower_bevel_outer_native_px=(np.array([[104,285],[152,348],[248,348],[311,281]])+OFFSET).tolist(),
        plinth_top_edge_native_px=(np.array([[51,359],[59,355],[350,351],[360,355]])+OFFSET).tolist(),
        state='Eight cut corners bound the projecting tablet. Aggregate and faint weathering are visible. No legible inscription or representational motif is established. The overhanging hood has two downward ends around a recessed lower edge; the tablet and hood remain separated by a shadow gap.')
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('image',type=Path)
    ap.add_argument('output',type=Path)
    args=ap.parse_args()
    args.output.write_text(json.dumps(read(args.image),ensure_ascii=False,indent=1)+'\n')
