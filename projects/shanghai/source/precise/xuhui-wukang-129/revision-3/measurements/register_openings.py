"""Two Wukang Road reference cameras. Inputs and outputs use original pixel centres."""
import json
from pathlib import Path

import numpy as np

class Camera:
    """ENU by default. Construction coordinates are photographic U, inward depth, Z."""
    def __init__(self, year, registration=None):
        path=registration or Path(__file__).absolute().with_name('two-photo-cameras.json')
        model=json.loads(Path(path).read_text())
        data=model['cameras'][str(year)]
        self.width,self.height=(5312,2988) if int(year)==2017 else (1800,1200)
        self.k=np.array(data['K_native'])
        self.r=np.array(data['R_uzd_to_cv'])
        self.origin=np.array(model['origin_enu'])
        self.basis=np.array(model['ENU_from_uzd'])
        self.c_uzd=np.array(data['C_uzd'])
        self.c=np.array(data['C_enu'])
        self.blender_world=np.array(data['blender_camera_to_enu'])

    def pixel_uzd(self, point):
        q=self.k@self.r@(np.asarray(point)-self.c_uzd)
        return q[:2]/q[2]

    def pixel(self, enu):
        return self.pixel_uzd(self.basis.T@(np.asarray(enu)-self.origin))

    def builder_pixel(self, u_depth_z):
        u,depth,z=u_depth_z
        return self.pixel_uzd([u,z,-depth])

    def ray_uzd(self, uv):
        direction=self.r.T@np.linalg.solve(self.k,[*uv,1.])
        return self.c_uzd.copy(),direction/np.linalg.norm(direction)

    def ray(self, uv):
        _,direction=self.ray_uzd(uv)
        return self.c.copy(),self.basis@direction

    def wall(self, uv, depth=0):
        """Intersect one original pixel at inward-positive builder depth, return U, depth, Z."""
        c,v=self.ray_uzd(uv)
        if abs(v[2])<1.e-10:
            raise ValueError('Ray parallel to street plane')
        p=c+(-depth-c[2])/v[2]*v
        return np.array([p[0],depth,p[1]])
