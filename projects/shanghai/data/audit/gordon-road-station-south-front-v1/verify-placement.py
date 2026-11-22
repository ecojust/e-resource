"""Check the partial courtyard elevation against the registered original building and adjoining facades."""
from pathlib import Path
import argparse, math, sys
import numpy as np
import shapely as geo
from shapely.geometry import MultiLineString, Point, Polygon, box, shape
HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / 'tools'))
from candidate_placement_meshes import PlacementMeshes, read, sha, write
from build_candidate_city_integrations import checked_geometry, check_source_section_caps

ID = 'jingan-gordon-road-station-south-front'
OWNER = 1295



def load_values(file, dtype):
    if file.is_file():
        return np.fromfile(file, dtype)
    import gzip, hashlib
    values = gzip.decompress(file.with_name(file.name + '.gz').read_bytes())
    expected = file.with_name(file.name + '.sha256').read_text().strip()
    assert hashlib.sha256(values).hexdigest() == expected
    return np.frombuffer(values, dtype).copy()


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
    src = site.footprints[OWNER]
    # Some photographed roof edges project into the court past the original footprint.
    overlap = profile.intersection(src)
    assert cut.buffer(.002).covers(overlap), overlap.difference(cut).bounds
    # The court, the masonry surrounds and the publicly visible door recess form
    # the observer-facing boundary. Behind the closed door the original stays solid.
    gable = box(-2.32, 0, 2.32, 3.59).difference(box(-.96, -.04, .96, .86))
    sides = [box(-7.10, .98, -2.32, 3.59), box(2.32, .98, 7.10, 3.59)]
    collision = geo.union_all([gable, *sides, physical],grid_size=.001)
    # The door's 3cm-high sill is not an above-ground obstacle.
    collision = collision.difference(box(-.90, -.015, .90, .84)).simplify(.002)
    # Far street walls carry explicit IDs. The separately recorded near check
    # establishes a clear ownership margin throughout the replaced area.
    triangles = load_values(args.work / 'baseline-far-triangles.f64', np.float64).reshape(-1, 3, 3)
    labels = load_values(args.work / 'baseline-far-owners.u32', np.uint32)
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
    for x in (-6.40,-4.71,-3.0,3.0,4.71,6.40):
        for y, occupied in [(-1.60,False),(.48,False),(1.25,True),(3.0,True),(3.90,True)]:
            check_ground(f'廊前与保留基座 {x:g}, {y:g}',[x,y],occupied)
    for x in (-.60,0,.60):
        for y, occupied in [(-1.50,False),(.36,False),(.65,False),(1.10,True)]:
            check_ground(f'门套前与门扇 {x:g}, {y:g}',[x,y],occupied)
    for x in (-9.,9.):
        for y, occupied in [(-1.5,False),(1.5,True)]:
            check_ground(f'原楼延续部分 {x:g}, {y:g}',[x,y],occupied)
    manifest = read(args.manifest)
    contract = {'id': ID, 'owner': {'macro_id': review['frozen_macro'], 'feature_local_id': OWNER},
                'source_feature_ids': {'building': [review['owner']['source_key'].split(':', 1)[1]], 'building_part': []},
                'replacement_geometry': site.wgs(cut), 'collision_geometry': site.wgs(collision), 'source_section_caps': caps,
                'lng': site.lon, 'lat': site.lat, 'heading': review['author_frame']['runtime_heading_deg'], 'scale': 1, 'altitude': 0,
                'model_geometry_sha256': {key: asset['sha256']for key, asset in assets.items()}, 'bounds_glb': bounds,
                'overviewBearing': 14, 'overviewPitch': 54, 'overviewZoom': 19.78, 'maxDistance': 460, 'lod_switch_in_m': 590, 'lod_switch_out_m': 755,
                'navigation': {'listed': False, 'status': '从南院可见三层山墙、弧形石门套、上部圆券窗与两边廊柱。'},
                'placement': {'status': 'map-aligned', 'note': '名录4B013及w490281437@2与原底图1295吻合。依历史正照与修缮设计单位正照定位南庭中央段，两侧及后部原楼保留。'},
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
