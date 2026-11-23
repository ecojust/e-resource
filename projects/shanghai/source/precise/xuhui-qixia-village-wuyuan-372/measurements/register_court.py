"""Project local row coordinates into four January 2016 courtyard photographs."""
import json
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
class Camera:
    def __init__(self,photo):
        views=json.loads((HERE/'court-cameras.json').read_text())['views']
        view=views[str(int(photo)%100)]
        self.k=np.asarray(view['intrinsic']);self.r=np.asarray(view['rotation'])
        self.c=np.asarray(view['centre']);self.inverse=self.r.T@np.linalg.inv(self.k)
    def ray(self,pixel):
        return self.inverse@np.r_[pixel,1.]
    def wall(self,pixel,depth=0.):
        ray=self.ray(pixel)
        return self.c+ray*((depth-self.c[1])/ray[1])
    def pixel(self,xyz):
        image=self.k@self.r@(np.asarray(xyz)-self.c)
        return image[:2]/image[2]
    def projection(self):
        return self.k@self.r@np.column_stack([np.eye(3),-self.c])
