"""Assign repeating brick UVs in model units on horizontal, front and return faces."""
from pathlib import Path
import importlib.util
from material_names import TEXTURES
path=Path(__file__).resolve().parents[2]/'hongkou-tanggu-road-apartment-dated-crown/source/crown_builder.py'
spec=importlib.util.spec_from_file_location('shanghai_metric_brick',path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class WujinBuilder(module.CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        super().add(vertices,faces,material,label)
        if material in TEXTURES:
            part=self.parts[-1]
            part['texcoords']=[(u/(.78*1.92),v/(.78*1.008)) for u,v in part['texcoords']]
