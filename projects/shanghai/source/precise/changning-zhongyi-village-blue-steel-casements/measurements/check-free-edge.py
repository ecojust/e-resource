"""Compare withheld photograph scanlines against the serialized outer metal edge of the open leaf."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import numpy as np
from PIL import Image

HERE = Path(__file__).absolute().parent
PROJECT = next(p for p in HERE.parents if (p/'data/audit/postal-office-v1').is_dir())
load = runpy.run_path(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py')['load_triangles']
crop = HERE/'wql-steel-window-pair.jpg'
crop_info = json.loads((HERE/'primary-crop.json').read_bytes())
assert hashlib.sha256(crop.read_bytes()).hexdigest()==crop_info['sha256']
camera = json.loads((HERE/'two-window-camera.json').read_bytes())
projection = np.array(camera['world_to_pixel'])
image = np.asarray(Image.open(crop)).astype(float)
offset_x, offset_y = crop_info['crop_original_px'][:2]
# The green-painted free stile changes to blue in the lower two thirds.
# The upper portion meets a dark recess with insufficient colour separation.
scanlines = list(range(951,1148,13))

def read_pixels():
    edges = []
    for v in scanlines:
        stripe = image[v-offset_y-2:v-offset_y+3].mean(axis=0)
        chroma = stripe[:,2]-stripe[:,0]
        # A fixed search strip covers the free stile across the scanned region.
        ix = np.arange(1244,1275)-offset_x
        delta = np.mean([chroma[ix+t] for t in [2,3,4]],axis=0)-np.mean([chroma[ix-t] for t in [2,3,4]],axis=0)
        k = int(np.argmax(delta))
        if delta[k] >= 8:
            edges.append(dict(v=v, observed_u=int(ix[k]+offset_x), colour_step=float(delta[k])))
    return edges

def check_model(file, observed):
    triangles, materials, names, meta = load(file)
    select = (materials==names.index('Weathered green steel')) & (triangles[:,:,1].min(axis=1)<-.19)
    tri = triangles[select]
    xyz1 = np.concatenate([tri,np.ones(tri.shape[:2]+(1,))],axis=2)
    uvw = xyz1 @ projection.T
    uv = uvw[:,:,:2]/uvw[:,:,2,None]
    a = uv.reshape(-1,2)
    b = np.roll(uv,-1,axis=1).reshape(-1,2)
    samples = []
    for pt in observed:
        v = pt['v']
        crossing = (np.minimum(a[:,1],b[:,1])<=v)&(v<np.maximum(a[:,1],b[:,1]))
        points = a[crossing]+(b[crossing]-a[crossing])*((v-a[crossing,1])/(b[crossing,1]-a[crossing,1]))[:,None]
        predicted = float(points[:,0].max())
        samples.append(dict(**pt, predicted_u=predicted, residual_px=predicted-pt['observed_u']))
    errors = np.array([r['residual_px'] for r in samples])
    return dict(sha256=meta['sha256'], sampled_outer_steel_triangles=len(tri), samples=samples,
                rms_px=float(np.mean(errors**2)**.5), max_abs_px=float(np.abs(errors).max()))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['raw','full','lod','output']:parser.add_argument(name,type=Path)
    inputs=parser.parse_args();observed=read_pixels()
    models={r:check_model(getattr(inputs,r),observed)for r in ['raw','full','lod']}
    assert len(observed)>=11
    result=dict(photo_sha256=crop_info['source_sha256'],crop_sha256=crop_info['sha256'],
                measured_feature='outer free stile of the outward-opening left leaf',scanline_search_u_px=[1244,1274],
                examined_scanlines=scanlines, accepted_samples=len(observed),min_colour_step=8,
                fit_used_scanlines=False,models=models)
    inputs.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(len(observed),[(k,r['rms_px'],r['max_abs_px'])for k,r in models.items()])
