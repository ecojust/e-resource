"""Keep the course height constant on piers, reveals and sloping roof faces."""
import importlib.util
from pathlib import Path
import numpy as np
from material_names import REPEAT,TILE

path=Path(__file__).resolve().parents[2]/'hongkou-tanggu-road-apartment-dated-crown/source/crown_builder.py'
spec=importlib.util.spec_from_file_location('yimin_measured_uv',path)
backend=importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend)

class HallBuilder(backend.CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        super().add(vertices,faces,material,label)
        if material not in REPEAT:return
        part=self.parts[-1]
        w,h=REPEAT[material]
        uv=np.asarray(part['texcoords'])/[.78*w,.78*h]
        part['texcoords']=uv.tolist()
