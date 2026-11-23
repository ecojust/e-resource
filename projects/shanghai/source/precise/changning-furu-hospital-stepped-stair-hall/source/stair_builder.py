"""Project physical UV repeats onto each triangulated surface and embed both material maps."""
from pathlib import Path
import sys
import finishes
from photo_architecture import Builder
sys.path.insert(0,str(finishes.PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder
import numpy as np, json
METRIC=json.loads((finishes.HERE.parent/'measurements/street-metric-facade.json').read_bytes())
class StairBuilder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        v=np.array(vertices,dtype=float,copy=True)
        v[:,:2]*=METRIC['plate_x_scale']
        z=v[:,2].copy()
        v[:,2]=z*METRIC['plate_z_scale']+METRIC['plate_z_offset']*np.minimum(z/3.2,1.)
        super().add(v,faces,material,label)
        if material in finishes.STEMS:finishes.metric_uv(self.parts[-1])
    def save(self,path,metadata=None):
        Builder.save(self,path,metadata)
        return finishes.writer.embed_normals(path)
