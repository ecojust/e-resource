"""Intersect the registered plinth of each decoded export with the three independent city footprints."""
import argparse
import json
import runpy
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, mapping
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'


def check(paths):
    identity = json.loads((HERE / 'placement-identity.json').read_bytes())
    survey = json.loads((HERE / 'registered-frontage-street-rays.json').read_bytes())
    scale = np.asarray(survey['metres_per_degree_lon_lat'])
    origin = np.asarray(identity['front_corners']['three-south'])
    street = (np.asarray(identity['front_corners']['three-north']) - origin) * scale
    street /= np.linalg.norm(street)
    inward = np.array([-street[1], street[0]])
    basis = np.stack((street, inward))
    owners = {}
    for owner, item in identity['original_footprints'].items():
        wgs = np.asarray(item['geometry_wgs84']['coordinates'][0])
        owners[owner] = Polygon((wgs - origin) * scale)
    read = runpy.run_path(str(READER))['load_triangles']
    report = {}
    for path in paths:
        triangles, _, _, asset = read(path)
        z = triangles[:, :, 2]
        floor = z.min()
        plinth = triangles[np.isclose(z, floor, atol=1e-6).all(axis=1), :, :2]
        footprint = unary_union([Polygon(tri @ basis) for tri in plinth])
        assert len(plinth) == 2 and footprint.is_valid
        assert abs(footprint.area - 46.50 * 12.82) < .001
        remainder = owners['561'].difference(footprint)
        cover = owners['561'].intersection(footprint)
        assert abs(owners['561'].area - (cover.area + remainder.area)) < 1e-5
        assert all(footprint.intersection(owners[key]).area == 0 for key in ['627', '3085'])
        report[path.name] = dict(asset=asset, ground_triangles=len(plinth),
                                 ground_height_m=float(floor), plinth_m2=footprint.area,
                                 registered_plinth_enu_m=mapping(footprint),
                                 city_561_area_m2=owners['561'].area, covered_561_m2=cover.area,
                                 retained_561_m2=remainder.area, retained_561_enu_m=mapping(remainder),
                                 beyond_561_m2=footprint.difference(owners['561']).area,
                                 neighbour_overlap_m2={k:footprint.intersection(owners[k]).area for k in ['627','3085']})
    return dict(basis='East/north metres at measured south street corner; front facade aligned to measured north corner',
                origin_wgs84=origin.tolist(), unit_street_enu=street.tolist(), unit_inward_enu=inward.tolist(),
                interpretation='约束主楼落地构件，外挑阳台和屋顶不作为地面碰撞。街景站可有数米整体偏移，本记录在给定坐标下计算实际相交面积。全城图接入前仍须做场景与地面验证。', meshes=report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('meshes', nargs='+', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.write_text(json.dumps(check(args.meshes), ensure_ascii=False, indent=2)+'\n')
