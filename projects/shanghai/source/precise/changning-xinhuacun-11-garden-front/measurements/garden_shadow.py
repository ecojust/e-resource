"""Rasterize opaque model faces into a metric directional depth map for cast shadows."""
from pathlib import Path
import ctypes
import subprocess
import tempfile
import numpy as np


class SunMap:
    def __init__(self,triangles,direction,pixels_per_metre=24):
        east=np.cross(direction,[0,0,1])
        east/=np.linalg.norm(east)
        self.axes=np.column_stack([east,np.cross(direction,east),direction])
        self.scale=pixels_per_metre
        projected=triangles@self.axes
        self.minimum=projected[:,:,:2].min(axis=(0,1))-2/self.scale
        projected[:,:,:2]=(projected[:,:,:2]-self.minimum)*self.scale
        width,height=np.ceil(projected[:,:,:2].max(axis=(0,1))).astype(int)+3
        self.depth=np.empty((height,width),np.float32)
        with tempfile.TemporaryDirectory() as temp:
            lib=Path(temp)/'shadow.so'
            subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC',str(Path(__file__).with_suffix('.c')),'-lm','-o',str(lib)],check=True)
            depth=ctypes.CDLL(str(lib)).depth_map
            depth.argtypes=[np.ctypeslib.ndpointer(np.float64,flags='C_CONTIGUOUS'),ctypes.c_size_t,ctypes.c_int,ctypes.c_int,np.ctypeslib.ndpointer(np.float32,flags='C_CONTIGUOUS')]
            depth.restype=None
            depth(np.ascontiguousarray(projected),len(triangles),width,height,self.depth)

    def exposure(self,points):
        projected=points@self.axes
        coords=((projected[:,:2]-self.minimum)*self.scale).astype(int)
        x=np.clip(coords[:,0],0,self.depth.shape[1]-1)
        y=np.clip(coords[:,1],0,self.depth.shape[0]-1)
        return np.where(self.depth[y,x]>projected[:,2]+.11,.37,1.)
