"""Keep one physical brick module around every face, including the raised roof bodies."""
import importlib.util
from pathlib import Path
import numpy as np
from hospital_finish import BRICK,REPEAT
base=Path(__file__).resolve().parents[2]/'hongkou-tanggu-road-apartment-dated-crown/source/crown_builder.py'
spec=importlib.util.spec_from_file_location('historic_masonry_metric_faces',base)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class HospitalBuilder(module.CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        super().add(vertices,faces,material,label)
        if material==BRICK:
            part=self.parts[-1]
            part['texcoords']=(np.asarray(part['texcoords'])/(.78*np.asarray(REPEAT))).tolist()
