"""Check roof and sash visibility using first-hit triangles at three original photograph stations."""
from argparse import ArgumentParser
from pathlib import Path
import hashlib
import json
import math
import runpy

import numpy as np

HERE = Path(__file__).resolve().parent
HELPER = HERE.parents[3] / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
RAY = runpy.run_path(str(HELPER))
# Pixel centres in the original photographs. The capped dormer behind leaves at
# the right edge of each Ctny photo is deliberately left unscored.
STATIONS = {
    'ctny-front': {
        'ridge': [(1329,465), (1364,458)],
        'caps': [(1,1371,490)],
        'glazing': [(1,1365,513)],
        'field': [(1332,481), (1395,521)],
        'casement': [(1372,512)]
    },
    'ctny-panorama': {
        'ridge': [(901,166), (977,155), (1034,150)],
        'caps': [(1,890,185), (2,940,181), (3,971,178), (4,1009,174), (5,1047,171)],
        'glazing': [(1,886,195), (2,935,191), (3,968,187), (4,1004,183), (5,1042,181)],
        'field': [(917,176), (959,197), (1022,165)],
        'casement': [(896,222)]
    },
    'historic-lawn': {
        'ridge': [(953,193.3), (1030,177.6), (1098,163.8), (1172,148.4)],
        'caps': [(1,969.5,219.5), (2,1044.5,206.5), (3,1097.5,197), (4,1154,186)],
        'glazing': [(1,965,236), (2,1043,221), (3,1093,215), (4,1150,205)],
        'field': [(966,208), (1017,224), (1068,211), (1126,196)],
        'casement': [(989,280), (1041,274), (1098,267)]
    }
}

class ProjectedMesh:
    def __init__(self, mesh, geometry):
        self.tri, indices, materials, self.asset = RAY['load_triangles'](mesh)
        assert geometry['sha256'] == self.asset['sha256']
        self.labels = np.empty(len(self.tri), dtype=np.int32)
        self.parts = geometry['part_summary']
        for m, name in enumerate(materials):
            which = np.flatnonzero(indices == m)
            start = 0
            for j, part in enumerate(self.parts):
                if part['material'] == name:
                    end = start + part['triangles']
                    self.labels[which[start:end]] = j
                    start = end
            assert start == len(which), name

    def station(self, station):
        self.eye = np.asarray(station['C'])
        rotation = np.asarray(station['R'])
        intrinsics = np.asarray(station['K'])
        self.inverse = rotation.T @ np.linalg.inv(intrinsics)
        homogeneous = (self.tri-self.eye) @ (intrinsics @ rotation).T
        depth = homogeneous[:, :, 2]
        uv = homogeneous[:, :, :2] / np.where(abs(depth)>1e-9,depth,1e-9)[:,:,None]
        self.low, self.high = uv.min(axis=1), uv.max(axis=1)
        self.behind = (depth<=0).all(axis=1)
        self.straddles = (depth<=0).any(axis=1) & ~self.behind
        self.cells = {}

    def hit(self, u, v):
        # Use conservative image-space bounds to reject triangles outside a
        # ray's grid cell. A triangle straddling the eye plane stays eligible.
        key = (math.floor(u/16),math.floor(v/16))
        if key not in self.cells:
            low = np.array(key)*16
            box = (self.low<=low+16).all(axis=1) & (self.high>=low).all(axis=1)
            self.cells[key] = np.flatnonzero((box & ~self.behind) | self.straddles)
        rows = self.cells[key]
        if not len(rows):
            return None
        j, d, point = RAY['first_hit'](self.tri[rows],self.eye,self.inverse@[u,v,1.])
        if not math.isfinite(d):
            return None
        index = int(rows[j])
        part = self.parts[self.labels[index]]
        return dict(triangle=index,material=part['material'],part=part['label'],xyz=point.round(4).tolist())

def matches(hit, kind, number=None):
    if hit is None:
        return False
    label = hit['part']
    if kind == 'ridge':
        return label.startswith('southeast return /') and 'tiled slope' in label
    if kind == 'field':
        return label.startswith('southeast return /') and 'tiled ' in label
    if kind == 'casement':
        return hit['material'] == 'dark casement'
    if f'roof light {number}/' not in label:
        return False
    if kind == 'glazing':
        return 'dark attic glazing' in label
    return 'cap' in label or 'fascia' in label

def examine(scene, samples):
    rows = []
    for kind, points in samples.items():
        for item in points:
            u,v=item[-2:]
            number=item[0] if len(item)==3 else None
            first = scene.hit(u,v)
            row = dict(feature=kind,axis=number,uv=[u,v],first=first,direct=matches(first,kind,number))
            if kind == 'ridge':
                # Signed offset of the upper edge of the continuous return
                # slope. One step is one original source pixel vertically.
                offset = next((dy for dy in range(-45,46) if matches(scene.hit(u,v+dy),kind)),None)
                row['upper_slope_edge_dy_px']=offset
            else:
                shifts = sorted(((dx,dy)for dx in range(-10,11)for dy in range(-10,11) if dx*dx+dy*dy<=100),key=lambda q:q[0]**2+q[1]**2)
                match = next(([dx,dy] for dx,dy in shifts if matches(first if (dx,dy)==(0,0) else scene.hit(u+dx,v+dy),kind,number)),None)
                row['nearest_within_10px']=match
            rows.append(row)
    return rows

def main():
    args=ArgumentParser(description=__doc__)
    args.add_argument('mesh',type=Path)
    args.add_argument('out',type=Path)
    args=args.parse_args()
    geo=json.loads(args.mesh.with_suffix('.geometry.json').read_bytes())
    scene=ProjectedMesh(args.mesh,geo)
    cameras=HERE/'lawn-return-stations.json'
    stations=json.loads(cameras.read_bytes())['stations']
    output={}
    for key,samples in STATIONS.items():
        scene.station(stations[key])
        output[key]=examine(scene,samples)
    result=dict(asset=scene.asset,registrations_sha256=hashlib.sha256(cameras.read_bytes()).hexdigest(),
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                scope='Local calibrated return in three original images. Roof face, individual dormer, sash and glazing identities come from the actual first-hit triangle and intact per-material order of the author GLB. A visually similar tile on the main roof cannot count as a dormer cap.',
                stations=output)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print({k:{'ridge_dy_px':[r['upper_slope_edge_dy_px'] for r in rows if r['feature']=='ridge'],'cap_direct':[r['direct'] for r in rows if r['feature']=='caps']} for k,rows in output.items()})

if __name__=='__main__':
    main()
