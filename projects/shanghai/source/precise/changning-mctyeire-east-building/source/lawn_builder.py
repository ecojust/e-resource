"""Reuse the first model's mesh author, applying new finishes only on the added return."""
from pathlib import Path
import sys
import numpy as np
from photo_architecture import Builder as OriginalBuilder
import lawn_finishes as finishes
sys.path.insert(0,str(finishes.PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder

class LawnBuilder(CrownBuilder):
    def add(self, vertices, faces, material='limestone', label='detail'):
        m=material
        if label.startswith('southeast '):
            m={'court ashlar':finishes.RENDER,'burnt clay tiles':finishes.TILE,'casement glass':finishes.GLASS}.get(material,material)
        super().add(vertices,faces,m,label)
        if m in finishes.STEMS:
            part=self.parts[-1];part['texcoords']=(np.asarray(part['texcoords'])/(.78*np.asarray(finishes.REPEAT_METRES[m]))).tolist()
    def save(self,path,metadata=None):
        OriginalBuilder.save(self,path,metadata)
        return finishes.writer.embed_normals(path)
