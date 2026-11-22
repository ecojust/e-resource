"""Identify all baseline owners close enough to require triangle-level eye-to-feature checks."""
from argparse import ArgumentParser
import gzip
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import MultiPoint, shape

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
MODEL = 'jingan-eye-hospital-building-three-front'


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--table', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    read = lambda f: json.loads(f.read_bytes())
    digest = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
    review = read(PROJECT/'source/precise'/MODEL/'footprint-review.json')
    source = next(v for v in review['frozen_bindings'] if v['repository_path'].endswith('/feature-table.json.gz'))
    assert digest(args.table) == source['sha256']
    catalog = json.loads(gzip.decompress(args.table.read_bytes()))['features']
    rays_file = HERE/'model-sightlines.json'
    rays = read(rays_file)
    assert rays['contract_sha256'] == digest(HERE/'final-placement-contract.json')
    frame = review['author_frame']
    lng, lat = frame['anchor']['lng'], frame['anchor']['lat']
    k = frame['earth_radius_m']*math.cos(math.radians(lat))
    north0 = math.asinh(math.tan(math.radians(lat)))
    yaw = math.radians(frame['runtime_heading_deg'])
    rot = np.array([[math.cos(yaw), -math.sin(yaw)], [math.sin(yaw), math.cos(yaw)]])
    def local(geographic):
        x = np.radians(geographic[:, 0]-lng)*k
        y = (np.arcsinh(np.tan(np.radians(geographic[:, 1])))-north0)*k
        return np.column_stack([x,y]) @ rot.T
    groups = review['near_tiles']
    active = {n for group in groups for n in group['feature_local_ids']}
    results = []
    for name in ('desktop','mobile'):
        points = []
        for model in rays['geometry']:
            camera, = [v for v in model['views'] if v['view']==name]
            points.append(camera['local_camera_eye'][:2])
            points.extend(r['hit']['physical_endpoint_m'][:2] for r in camera['targets'])
        corridor = MultiPoint(points).convex_hull.buffer(3.5)
        matches = []
        for building in catalog:
            if building.get('geometry') and corridor.intersects(shapely.transform(shape(building['geometry']),local)):
                matches.append(building['localId'])
        assert 712 in matches and set(matches) <= active, (name,matches)
        results.append(dict(view=name,buffer_m=3.5,footprint_owners=sorted(matches),checked_model_rays=len(points)-len(rays['geometry'])))
    result=dict(order=315, passed=True, model_rays_sha256=digest(rays_file), baseline_table_sha256=digest(args.table),
                exact_near_groups=[g['id'] for g in groups], baseline_footprints=len(catalog), views=results)
    args.out.write_text(json.dumps(result,indent=2)+'\n')

if __name__ == '__main__':
    main()
