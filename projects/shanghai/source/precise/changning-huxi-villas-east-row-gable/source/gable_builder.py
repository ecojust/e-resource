"""Project physical UV repeats onto each triangulated surface and embed both material maps."""
from pathlib import Path
import sys
import finishes
from photo_architecture import Builder
sys.path.insert(0,str(finishes.PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder
class GableBuilder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        super().add(vertices,faces,material,label)
        if material in finishes.STEMS:finishes.metric_uv(self.parts[-1])
    def save(self,path,metadata=None):
        Builder.save(self,path,metadata)
        return finishes.writer.embed_normals(path)
