"""Cast the two source camera stations into each actual GLB at photographed landmarks."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

HERE = Path(__file__).absolute().parent
PROJECT = next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
CHECK = runpy.run_path(str(PROJECT/'source/precise/changning-yuyuan-1112-no4/measurements/check_surface_projections.py'))


def report(mesh):
    triangles, indices, materials, _ = CHECK['LOAD'](mesh)
    cameras = json.loads((HERE/'portico-camera-pair.json').read_bytes())['stations']
    readings = json.loads((HERE/'two-photo-surface-marks.json').read_bytes())
    observations = []
    for station, points in readings.items():
        ray = CHECK['first_surface'](triangles, indices, materials, cameras[station])
        for feature, pixel, expected in points:
            material = ray(*pixel)
            observations.append(dict(station=station,feature=feature,native_photo_pixel=pixel,
                                     expected=expected,first_material=material,matched=material==expected))
    return dict(file=mesh.name,sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),
                direct=sum(x['matched'] for x in observations),total=len(observations),points=observations)


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('meshes',type=Path,nargs=2)
    cli.add_argument('output',type=Path)
    args = cli.parse_args()
    args.output.write_text(json.dumps([report(p) for p in args.meshes],ensure_ascii=False,indent=2)+'\n')
