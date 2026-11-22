"""Use continuous course spacing on each exposed brick face."""
import importlib.util
from pathlib import Path
from material_names import TEXTURES
path=Path(__file__).resolve().parents[2]/'hongkou-tanggu-road-apartment-dated-crown/source/crown_builder.py'
spec=importlib.util.spec_from_file_location('shanghai_cladding_uv',path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class ShanyinBuilder(module.CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        super().add(vertices,faces,material,label)
        if material in TEXTURES:
            part=self.parts[-1]
            # Eight stretcher lengths and sixteen courses repeat within 1.97 x 1.01 display metres.
            part['texcoords']=[(u/(.78*1.97),v/(.78*1.01))for u,v in part['texcoords']]
