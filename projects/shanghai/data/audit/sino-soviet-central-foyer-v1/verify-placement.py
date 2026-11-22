"""Verify the south court, the threshold and the retained galleries adjoining the central foyer."""
from pathlib import Path
import argparse, math, sys
import numpy as np
import shapely as geo
from shapely.geometry import MultiLineString, Point, Polygon, shape
HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / 'tools'))
from candidate_placement_meshes import PlacementMeshes, read, sha, write
from build_candidate_city_integrations import checked_geometry, check_source_section_caps

ID = 'jingan-sino-soviet-central-foyer'
OWNER = 969


def main(args):
    source = PROJECT / 'source/precise' / ID
    review = read(source / 'footprint-review.json')
    proof = read(args.cut)
    assert proof['id'] == ID and proof['passed'] and proof['source_review_sha256'] == sha(
        source / 'footprint-review.json')
    site = PlacementMeshes(PROJECT, args.work, review)
    decoder = HERE.parent / 'mitsui-bussan-pediment-front-v1/decode-texture.cjs'
    site.env['NODE_OPTIONS'] = (site.env.get('NODE_OPTIONS', '') + ' --require=' + str(decoder)).strip()
    assets, bounds, profile, physical = site.decode_model(args.manifest)
    cut = Polygon(proof['mask_local_m'])
    src=site.footprints[OWNER]
    # The columns, cornices and stairs extend beyond the hall wall. Trimming
    # those exterior projections would remove original parts of the adjoining
    # wings. Only the square floor replaces the old city structure.
    assert profile.buffer(.025).covers(cut.buffer(-.06))
    assert profile.bounds[0]>=-23.50 and profile.bounds[2]<=23.50
    assert -3.88<=profile.bounds[1]<=-3.82 and profile.bounds[3]<=46.50
    from shapely import transform
    gate=read(source/'source/court-placement.json')
    collision=transform(shape(gate['collision_geometry']),site.to_xy)
    assert cut.buffer(.001).covers(collision) and 2085 < collision.area < 2105
    assert physical.covers(Point(0,20)) and not physical.covers(Point(0,-4.1))
    # Far street walls carry explicit IDs. The separately recorded near check
    # establishes a clear ownership margin throughout the replaced area.
    triangles = np.fromfile(args.work / 'baseline-far-triangles.f64', np.float64).reshape(-1, 3, 3)
    labels = np.fromfile(args.work / 'baseline-far-owners.u32', np.uint32)
    assert len(triangles) == len(labels)
    selected = triangles[labels == OWNER].copy()
    selected[:, :, :2] = selected[:, :, :2] @ site.axes.T
    outline = site.project_faces(selected)
    sections = geo.get_parts(geo.line_merge(cut.boundary.intersection(outline)))
    edges = []
    for section in sections:
        for a, b in zip(section.coords, list(section.coords)[1:]):
            if math.dist(a, b) > .003:
                edges.append([a, b])
    # Only actual retained wall joins need vertical faces. The 46 m south
    # entry must stay open to the court, including in the near detail mesh.
    assert len(edges)==3 and all(max(pt[1] for pt in edge)>45.9 for edge in edges)
    seam = MultiLineString(edges)
    assert not seam.is_empty and cut.boundary.buffer(.00002).covers(seam)
    ready = read(site.files['READY.json'])
    caps = {'geometry': site.wgs(seam), 'base_m': 0, 'roof_m': proof['source_levels']['far']['roof_m'],
            'height_reference': [ready['origin_longitude'], ready['origin_latitude']], 'far_sha256': sha(site.files['far.glb'])}
    reg = read(source / 'source/registration.json')
    probes = []

    def check_ground(name, xy, expected):
        v = np.asarray(xy)
        pt = Point(v)
        model_blocked = collision.covers(pt)
        in_cut = cut.covers(pt)
        blocked = model_blocked or (not in_cut and src.covers(pt))
        assert blocked == expected, (name, v.tolist(), blocked)
        probes.append({'name': name, 'xy': v.tolist(), 'wgs84': site.to_wgs(np.array([v]))[0].tolist(),
                       'expected_map': 'building' if expected else None, 'model_obstacle': model_blocked, 'source_cut': in_cut})
    for x in (-21.30,-14.73,-7.20,-3.6,0.,3.6,7.20,14.73,21.30):
        for y in (-4.10,-1.0,-.20,.50,2.30,2.76,6.1,20.,45.8):
            expected = y>0 and (abs(x)>4.48 or y>2.49)
            check_ground(f'南广场 X={x:.2f} Y={y:.2f}',[x,y],expected)
    for x in (-35.,35.):
        check_ground('保留侧翼内 '+str(x),[x,18.],True)
    check_ground('保留序馆后侧中央接续',[0.,46.6],True)
    manifest=read(args.manifest)
    contract = {'id': ID, 'owner': {'macro_id': review['frozen_macro'], 'feature_local_id': OWNER},
                'source_feature_ids': {'building': [review['owner']['source_key'].split(':', 1)[1]], 'building_part': []},
                'replacement_geometry': site.wgs(cut), 'collision_geometry': site.wgs(collision), 'source_section_caps': caps,
                'lng': site.lon, 'lat': site.lat, 'heading': review['author_frame']['runtime_heading_deg'], 'scale': 1, 'altitude': 0,
                'model_geometry_sha256': {key: asset['sha256']for key, asset in assets.items()}, 'bounds_glb': bounds,
                'overviewBearing':-23.2,'overviewPitch':57, 'overviewZoom': 17.6, 'maxDistance': 700, 'lod_switch_in_m': 900, 'lod_switch_out_m': 1120,
                'navigation': {'listed': False, 'status': '从南广场向北可见序馆拱门和两侧小亭，上方为列柱塔层、鎏金钢尖塔与红五星。'},
                'placement': {'status': 'map-aligned', 'note': '依第四批4B001、《上海名建筑志》46米方形中央大厅、原户969和南广场多期照片定位。保留两翼、内庭、厅后接续和相邻原楼。'},
                'partial_model': True, 'model_scope': manifest['scope']}
    for k in ('replacement_geometry', 'collision_geometry'):
        checked_geometry(contract[k], k, collision=k == 'collision_geometry')
    check_source_section_caps(contract, shape(contract['replacement_geometry']))
    args.out.mkdir(parents=True, exist_ok=True)
    write(args.out / 'final-placement-contract.json', contract)
    write(args.out / 'placement-geometry.json', {'id': ID, 'passed': True, 'source_cut_sha256': sha(args.cut), 'manifest_sha256': sha(args.manifest), 'checker_sha256': sha(Path(__file__)), 'texture_decoder_sha256': sha(decoder), 'assets': assets,
          'native_variants': proof['source_levels'], 'ground_probes': probes, 'neighbors': proof['neighbor_distance_m'], 'area_model_m2': profile.area, 'area_collision_m2': collision.area, 'area_cut_m2': cut.area, 'seam_segments': len(edges)})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--cut', type=Path, default=HERE / 'source-cut.json')
    parser.add_argument('--out', type=Path, default=HERE)
    main(parser.parse_args())
