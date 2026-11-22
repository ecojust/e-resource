"""Check the old hall, east courtyard steps and open colonnade against the delivered meshes."""
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

ID = 'jingan-jueyuan-xiangguang-hall'
OWNER = 354


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
    from shapely.geometry import box
    from shapely.ops import unary_union
    src = site.footprints[OWNER]
    # Eave tiles and courtyard steps can overhang the original footprint.
    # Only original wall or roof pixels lose area in the source.
    assert profile.difference(cut).intersection(src).area < .002
    reg = read(source/'source/frontage-registration.json')
    half=reg['width_m']/2
    leaves=box(-half,1.51,half,reg['rear_depth_m'])
    center_recess=box(-.20,1.50,.20,1.94)
    pillars=[box(x-.12,-.108,x+.12,.24) for x in reg['full_bay_bounds']]
    side_rails=[box(x-.05,-.09,x+.05,1.52) for x in [-half,half]]
    collision=unary_union([leaves.difference(center_recess),*pillars,*side_rails])
    # Exclude low genuine treads and the .55m gallery floor from obstructions.
    assert collision.difference(physical.buffer(.09)).area < .02
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
    seam = MultiLineString(edges)
    assert not seam.is_empty and cut.boundary.buffer(.00002).covers(seam)
    ready = read(site.files['READY.json'])
    caps = {'geometry': site.wgs(seam), 'base_m': 0, 'roof_m': proof['source_levels']['far']['roof_m'],
            'height_reference': [ready['origin_longitude'], ready['origin_latitude']], 'far_sha256': sha(site.files['far.glb'])}
    reg = read(source / 'source/frontage-registration.json')
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
    for x in (-10.7,-7.5,-4.3,-1.0,0.,1.0,4.3,7.5,10.7):
        for y,occupied,label in [(-2.05,False,'庭院'),(-1.11,False,'台阶前缘'),(-.28,False,'廊前'),
                                 (.44,False,'柱后'),(1.26,False,'木廊'),(2.02,True,'门屏后'),
                                 (4.2,True,'木楼'),(5.24,True,'原楼保留段')]:
            check_ground(f'{x} {label}',[x,y],occupied)
    for x in reg['full_bay_bounds']:
        check_ground(f'{x} 柱身',[x,.02],True)
    for x in (-.65,0.,.65):
        check_ground(f'{x} 中央门口',[x,1.69],x!=0)
    manifest = read(args.manifest)
    contract = {'id': ID, 'owner': {'macro_id': review['frozen_macro'], 'feature_local_id': OWNER},
                'source_feature_ids': {'building': [review['owner']['source_key'].split(':', 1)[1]], 'building_part': []},
                'replacement_geometry': site.wgs(cut), 'collision_geometry': site.wgs(collision), 'source_section_caps': caps,
                'lng': site.lon, 'lat': site.lat, 'heading': review['author_frame']['runtime_heading_deg'], 'scale': 1, 'altitude': 0,
                'model_geometry_sha256': {key: asset['sha256']for key, asset in assets.items()}, 'bounds_glb': bounds,
                'overviewBearing': -105, 'overviewPitch': 38, 'overviewZoom': 19.78, 'maxDistance': 460, 'lod_switch_in_m': 590, 'lod_switch_out_m': 755,
                'navigation': {'listed': False, 'status': '东院可见两层木廊，台阶通向柱后的香光堂门匾，上层为菱格木窗。'},
                'placement': {'status': 'map-aligned', 'note': '依名录4B008、区志和两期原照确认西楼。依据拍摄时刻与投影定位东院长面，保留北侧金刚道场三进和南厢房。'},
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
