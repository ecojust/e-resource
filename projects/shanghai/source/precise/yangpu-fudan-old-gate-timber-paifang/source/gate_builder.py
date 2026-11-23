"""Retain physical texture periods on roof faces and orient timber grain along each member."""
import sys
import numpy as np
from photo_architecture import Builder
import gate_finishes as finish
sys.path.insert(0,str(finish.PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder
class GateBuilder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        super().add(vertices,faces,material,label)
        if material not in finish.STEMS:return
        part=self.parts[-1]
        uv=np.array(part['texcoords'])/.78
        if material==finish.WOOD and ('lintel' in label or 'fascia' in label or 'bracket' in label):
            uv=uv[:,::-1]
        part['texcoords']=(uv/finish.REPEAT_METRES[material]).tolist()
    def save(self,path,metadata=None):
        Builder.save(self,path,metadata)
        return finish.writer.embed_normals(path)
