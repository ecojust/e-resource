"""Repeat the 337 street-station intersections and the gate's two editable mesh audits."""
import argparse
import collections
import importlib.util
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).absolute().parent


def intersect(shots, origin):
    kx = 111320 * math.cos(math.radians(origin[1]))
    ky = 110870
    equations = []
    offsets = []
    rays = []
    for shot in shots:
        lon, lat = shot["camera_wgs84"]
        pos = np.array([(lon-origin[0])*kx, (lat-origin[1])*ky])
        w, h = shot["size"]
        f = w / (2*math.tan(math.radians(shot["horizontal_fov"])/2))
        u = (shot["point"][0]-w/2)/f
        v = (h/2-shot["point"][1])/f
        pitch = math.radians(shot["pitch"])
        slope = math.cos(pitch)-v*math.sin(pitch)
        az = math.radians(shot["azimuth"])+math.atan2(u,slope)
        d = np.array([math.sin(az), math.cos(az)])
        normal = np.array([d[1],-d[0]])
        equations.append(normal)
        offsets.append(normal@pos)
        el = (math.sin(pitch)+v*math.cos(pitch))/math.hypot(u,slope)
        rays.append((pos,d,el,shot["relative_to_street_height_m"]))
    point = np.linalg.lstsq(equations, offsets, rcond=None)[0]
    z = np.median([height + ((point-pos)@d)*el for pos,d,el,height in rays])
    return point, z


class MeshCheck:
    def __init__(self):
        self.parts = 0
        self.triangles = 0

    def add(self, vertices, triangles, material, label):
        counts = collections.Counter()
        directed = collections.Counter()
        volume = 0.
        v = np.array(vertices)
        for a,b,c in triangles:
            cross = np.cross(v[b]-v[a],v[c]-v[a])
            assert np.linalg.norm(cross)>1e-12, label
            volume += np.dot(v[a], np.cross(v[b], v[c]))/6
            for edge in [(a,b),(b,c),(c,a)]:
                counts[tuple(sorted(edge))] += 1
                directed[edge] += 1
        assert set(counts.values()) == {2} and volume>0 and all(directed[q]==directed[q[::-1]] for q in directed), label
        self.parts += 1
        self.triangles += len(triangles)


def verify():
    doc = json.loads((HERE/"courtyard-gate-survey.json").read_bytes())
    origin = [121.45152,31.22152]
    solutions = []
    for row in doc["observations"]:
        for date, target in row["same_date_intersections"].items():
            shots = [s for s in row["image_readings"] if s["date"]==date]
            en,z = intersect(shots,origin)
            assert np.max(np.abs(en-target["en"]))<1.e-7 and abs(z-target["z"])<1.e-7
            solutions.append([row["point"],date])
    spec=importlib.util.spec_from_file_location("number_337_gate",HERE.parent/"source/courtyard_gate.py")
    model=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model)
    geometry=[]
    for lod in (False,True):
        checker=MeshCheck()
        model.add_courtyard_gate(checker,lod)
        geometry.append(dict(lod=lod,closed_positive_parts=checker.parts,triangles=checker.triangles))
    assert len(solutions)>=14
    return dict(same_date_intersections=solutions,geometry=geometry)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    result=json.dumps(verify(),indent=2)+"\n"
    if args.output:
        args.output.write_text(result)
    print(result,end="")
