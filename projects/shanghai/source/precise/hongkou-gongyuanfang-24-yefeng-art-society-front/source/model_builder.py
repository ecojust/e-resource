"""Masonry texture coordinates in measured metres, continuous along the convex facade."""
import importlib.util
from pathlib import Path
import numpy as np
from frontage_coordinates import CX, CY, WALL_RADIUS
from material_names import RED, DARK, TILE_METRES

BACKEND=Path(__file__).resolve().parents[2]/'hongkou-tanggu-road-apartment-dated-crown/source/crown_builder.py'
spec=importlib.util.spec_from_file_location('gongyuan_metric_surface',BACKEND)
backend=importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend)


class FacadeBuilder(backend.CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        super().add(vertices,faces,material,label)
        if material not in TILE_METRES:return
        part=self.parts[-1]
        w,h=TILE_METRES[material]
        tex=np.asarray(part['texcoords'])/[.78*w,.78*h]
        if label.startswith('Curved bay |') and material in (RED,DARK):
            points=np.asarray(part['vertices'])
            for tri in part['triangles']:
                indices=list(tri);xyz=points[indices]
                normal=np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]);normal/=np.linalg.norm(normal)
                radial=xyz[:,:2].mean(axis=0)-[CX,CY];radial/=np.linalg.norm(radial)
                if abs(normal[:2]@radial)>.94:
                    tex[indices,0]=WALL_RADIUS*np.arctan2(xyz[:,0]-CX,CY-xyz[:,1])/w
                    tex[indices,1]=xyz[:,2]/h
        part['texcoords']=tex.tolist()
