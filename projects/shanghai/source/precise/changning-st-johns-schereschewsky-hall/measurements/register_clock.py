"""Project and intersect the two measured clock-tower stations. Pixel coordinates refer to pixel centres."""
from pathlib import Path
import json
import numpy as np

class Camera:
    def __init__(self, station, table=None):
        aliases = {'metromod-2004':'court', 'street-2026':'street'}
        filename = Path(table) if table else Path(__file__).with_name('tower-stations.json')
        data = json.loads(filename.read_bytes())['stations'][aliases.get(station,station)]
        for name in ('C','K','R','P'):
            setattr(self,name,np.array(data[name],dtype=float))
        self.image_size = tuple(data['image_size'])

    def pixel(self, xyz):
        homogeneous = self.P @ np.r_[xyz,1.]
        return homogeneous[:2]/homogeneous[2]

    def plane(self, uv, origin, normal):
        direction = self.R.T @ np.linalg.solve(self.K,np.r_[uv,1])
        normal = np.asarray(normal)
        divisor = normal @ direction
        if abs(divisor)<1.e-10:
            raise ValueError('Viewing ray is parallel to the requested plane')
        return self.C + direction*(normal @ (np.array(origin)-self.C))/divisor
