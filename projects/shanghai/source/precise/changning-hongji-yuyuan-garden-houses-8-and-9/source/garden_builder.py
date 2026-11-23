"""Keep each house editable in its own axes before placing it around the same lawn."""
from pathlib import Path
import sys

import numpy as np

SOURCE=Path(__file__).resolve().parent
PROJECT=next(root for root in SOURCE.parents if (root/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as packaging
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder
from photo_architecture import Builder
from hongji_roof_geometry import TILE8, TILE9


class GardenBuilder(CrownBuilder):
    def add(self, vertices, faces, material='limestone', label='detail'):
        if material in (TILE8, TILE9):
            # Tile UVs are set from each roof plane by strips_and_caps.
            Builder.add(self,vertices,faces,material,label)
        else:
            super().add(vertices,faces,material,label)

    def place_house(self, local, number, frame):
        origin=frame['left_wall_projection']['garden_ENU_m']
        axes=np.array([frame['local_X_unit_EN'],frame['local_Y_unit_EN']])
        if abs(np.linalg.det(axes)-1.) > 2e-5:
            raise ValueError('The two courtyard facades need right-handed local frames')
        for item in local.parts:
            vertices=np.asarray(item['vertices']).copy()
            vertices[:,:2]=vertices[:,:2]@axes+origin
            prefix=str(number)+' | '
            label=item['label'] if item['label'].startswith(prefix) else prefix+item['label']
            self.parts.append({**item,'label':label,'vertices':vertices.tolist()})
        self.palette.update(local.palette)
