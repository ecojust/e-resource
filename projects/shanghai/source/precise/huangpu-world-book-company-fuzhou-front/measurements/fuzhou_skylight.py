"""Estimate near-field sky occlusion from the visible mesh surface in the registered photo camera."""
import ctypes
import json
import struct

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter


class SurfaceCapture:
    def __init__(self, library, model):
        self.shadow_depth=library.shadow_depth
        self._paint=library.paint
        with model.open('rb') as source:
            source.seek(12)
            size,kind=struct.unpack('<II',source.read(8))
            assert kind==0x4e4f534a
            doc=json.loads(source.read(size))
        ids=doc['scenes'][doc.get('scene',0)]['nodes']
        self.remaining=sum(len(doc['meshes'][doc['nodes'][i]['mesh']]['primitives']) for i in ids)

    def paint(self,*args):
        self._paint(*args)
        self.remaining-=1
        if self.remaining==0:
            _,_,_,width,height,depth,*_=args
            flat=np.ctypeslib.as_array(ctypes.cast(depth,ctypes.POINTER(ctypes.c_float)),shape=(height,width))
            self.depth=flat.copy()


def horizon_shading(image,depth,camera,crop):
    """Measure eight local horizon sectors. Reject background and distant unrelated surfaces."""
    # Use the full geometry for colour. Half-resolution horizons avoid amplifying
    # the single-pixel mortar joints already present in the geometry and texture.
    scale=2
    z=depth[::scale,::scale];height,width=z.shape
    vv,uu=np.indices(z.shape,dtype='float32')
    pitch=(crop[2]-crop[0])/depth.shape[1]
    uv=np.stack([crop[0]+(scale*uu+.5)*pitch,crop[1]+(scale*vv+.5)*pitch,np.ones_like(uu)],axis=-1)
    inv=np.linalg.inv(camera[:,:3]).astype('float32')
    rays=uv@inv.T
    valid=z>0
    pos=rays/np.where(valid,z,1.)[:,:,None]
    def offset(array,dx,dy):return np.roll(array,(-dy,-dx),axis=(0,1))
    def tangent(dx,dy):
        a=offset(pos,dx,dy)-pos;b=pos-offset(pos,-dx,-dy)
        aa=(a*a).sum(2);bb=(b*b).sum(2)
        return np.where((aa<bb)[:,:,None],a,b)
    normal=np.cross(tangent(1,0),tangent(0,1))
    normal/=np.maximum(np.linalg.norm(normal,axis=2,keepdims=True),1.e-8)
    normal*=np.where((normal*rays).sum(2)>0,-1.,1.)[:,:,None]
    amount=np.zeros_like(z)
    for dx,dy in [(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)]:
        horizon=np.zeros_like(z)
        for step in (2,5,10,17,27):
            sx,sy=dx*step,dy*step
            delta=offset(pos,sx,sy)-pos;dist=np.linalg.norm(delta,axis=2)
            sine=(delta*normal).sum(2)/np.maximum(dist,1.e-7)
            inside=(uu+sx>=0)&(uu+sx<width)&(vv+sy>=0)&(vv+sy<height)
            nearby=inside&valid&offset(valid,sx,sy)&(dist>.018)&(dist<1.25)
            horizon=np.maximum(horizon,np.where(nearby,np.maximum(0.,sine-.035)*(1-dist/1.25),0.))
        amount+=horizon/8.
    # The photographed street receives diffuse light from the sky. This factor
    # darkens only geometry that has sampled neighbours above its local horizon.
    weights=gaussian_filter(np.where(valid,amount,0.),.65)
    factor=1.-.58*weights
    full=np.array(Image.fromarray(factor.astype('float32')).resize(image.size,Image.Resampling.BILINEAR))
    full=np.where(depth>0,full,1.)
    rgb=np.asarray(image).astype('float32')/255.
    v=np.where(rgb<.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)*full[:,:,None]
    srgb=np.where(v<.003131,12.92*v,1.055*v**(1/2.4)-.055)
    return Image.fromarray((np.clip(srgb,0,1)*255+.5).astype('uint8')),round(float(amount[valid].mean()),5)
