"""Procedurally generated narrow-grain red-brown varnish on the window frame."""
from pathlib import Path
MATERIAL='Weathered red timber frame';TEXTURE=Path(__file__).with_name('liang-weathered-frame.png')
REPEAT=.49
def generate():
    from PIL import Image
    import numpy as np
    from scipy.ndimage import gaussian_filter
    r=np.random.default_rng(189861);raw=r.standard_normal((176,176))
    field=5.6*gaussian_filter(raw,[8,.65],mode='wrap')+18*gaussian_filter(raw,[13,1.3],mode='wrap')+4.0*raw
    grain=np.maximum(0,gaussian_filter(raw,[4,.55],mode='wrap')-.33)*33.
    rgb=np.array([130,65,49.])+field[:,:,None]*np.array([1.,.87,.77])+grain[:,:,None]*np.array([1.,1.05,.97])
    Image.fromarray(np.uint8(np.clip(rgb,0,255))).save(TEXTURE,optimize=True)
def metric_uv(b):
    import numpy as np
    for part in b.parts:
        if part['material']!=MATERIAL:continue
        vertices=np.asarray(part['vertices'],dtype=np.float32).astype(float);c=vertices[np.asarray(part['triangles'])]
        normals=np.cross(c[:,1]-c[:,0],c[:,2]-c[:,0]);dom=np.argmax(abs(normals),axis=1)
        x,y,z=c.transpose(2,0,1);u=np.where((dom==0)[:,None],y,x);v=np.where((dom==2)[:,None],y,z)
        part.update(vertices=c.reshape(-1,3).tolist(),triangles=np.arange(c.size//3).reshape(-1,3).tolist(),texcoords=np.stack([u/REPEAT,1-v/REPEAT],axis=-1).reshape(-1,2).tolist())
if __name__=='__main__':generate()
