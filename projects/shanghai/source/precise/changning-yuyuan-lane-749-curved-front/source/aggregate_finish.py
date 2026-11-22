"""Original repeating washed-aggregate finish and arc-length coordinates on the rounded facade."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

TEXTURE=Path(__file__).with_name('yuyuan-washed-aggregate.png')
CAST='Yuyuan grey washed aggregate'
REPEAT=.72

def create():
    rng=np.random.default_rng(20180213)
    field=rng.standard_normal((160,160))
    flecks=gaussian_filter(rng.standard_normal((160,160)),.60,mode='wrap')
    grain=8.5*field+21*gaussian_filter(field,1.2,mode='wrap')+31*gaussian_filter(field,4.8,mode='wrap')
    grain+=np.where(flecks>.78,29,np.where(flecks<-.77,-25,0))
    base=np.array([137.,139.,140.])+grain[:,:,None]*np.array([1.,1.,1.04])
    Image.fromarray(base.round().clip(0,255).astype('uint8')).save(TEXTURE,optimize=True)

def apply_metric_uv(builder,radius):
    for part in builder.parts:
        if part['material']!=CAST:continue
        v=np.asarray(part['vertices'],dtype=np.float32).astype(float)
        tri=v[np.asarray(part['triangles'])]
        normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
        rho=np.hypot(tri[:,:,0],radius-tri[:,:,1])
        theta=np.arctan2(tri[:,:,0],radius-tri[:,:,1])
        vertical=np.linalg.norm(normal[:,:2],axis=1)>np.abs(normal[:,2])
        cylindrical=vertical&(np.ptp(rho,axis=1)<.00005)
        u=np.where(cylindrical[:,None],theta*rho,np.where(vertical[:,None],rho-radius,tri[:,:,0]))
        v=np.where(vertical[:,None],tri[:,:,2],tri[:,:,1])
        part.update(vertices=tri.reshape(-1,3).tolist(),triangles=np.arange(3*len(tri)).reshape(-1,3).tolist(),
                    texcoords=np.stack([u/REPEAT,1-v/REPEAT],axis=2).reshape(-1,2).tolist())

if __name__=='__main__':create()
