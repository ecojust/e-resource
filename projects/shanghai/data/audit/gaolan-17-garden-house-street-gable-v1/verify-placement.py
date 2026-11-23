"""Check the partial courtyard elevation against the registered original building and adjoining facades."""
from pathlib import Path
import argparse, math, sys
import numpy as np
import shapely as geo
from shapely.geometry import MultiLineString, Point, Polygon, box, shape
HERE = Path(__file__).resolve().parent
PROJECT = Path(__file__).resolve().parents[3]
if not (PROJECT/'tools').is_dir():
    PROJECT = next(x for x in Path.cwd().resolve().parents if (x/'tools/package_architectural_model.py').is_file())
sys.path.insert(0, str(PROJECT / 'tools'))
from candidate_placement_meshes import PlacementMeshes, read, sha, write
from build_candidate_city_integrations import checked_geometry, check_source_section_caps

ID = 'huangpu-gaolan-17-garden-house-street-gable'
OWNER = 251



def load_values(file, dtype):
    if file.is_file():
        return np.fromfile(file, dtype)
    import gzip, hashlib
    values = gzip.decompress(file.with_name(file.name + '.gz').read_bytes())
    expected = file.with_name(file.name + '.sha256').read_text().strip()
    assert hashlib.sha256(values).hexdigest() == expected
    return np.frombuffer(values, dtype).copy()


def main(args):
    source = Path(__import__('os').environ.get('GAOLAN_GABLE_SOURCE_ROOT', PROJECT)) / 'source/precise' / ID
    review = read(source / 'footprint-review.json')
    proof = read(args.cut)
    assert proof['id'] == ID and proof['passed'] and proof['source_review_sha256'] == sha(
        source / 'footprint-review.json')
    site = PlacementMeshes(PROJECT, args.work, review)
    decoder = PROJECT/'data/audit/mitsui-bussan-pediment-front-v1/decode-texture.cjs'
    site.env['NODE_OPTIONS'] = (site.env.get('NODE_OPTIONS', '') + ' --require=' + str(decoder)).strip()
    original_link=site.link
    def link_verified_input(name, file):
        # Keep the owning process's descriptor directly reachable during a preflight decode.
        import os
        descriptor=os.readlink(file) if file.is_symlink() else ''
        if descriptor.startswith('/proc/') and '/fd/' in descriptor:
            target=site.work/name
            target.unlink(missing_ok=True)
            target.symlink_to(descriptor)
        else:
            original_link(name,file)
    site.link=link_verified_input
    assets, bounds, profile, physical = site.decode_model(args.manifest)
    cut = Polygon(proof['mask_local_m'])
    src = site.footprints[OWNER]
    # Some photographed roof edges project into the court past the original footprint.
    overlap = profile.intersection(src)
    assert cut.buffer(.002).covers(overlap), overlap.difference(cut).bounds
    # The enclosed gabled room and the projecting lower bay occupy the ground.
    # Retained rooms in the same house and the exterior passage are separate.
    collision=geo.union_all([box(-2.94,0.,2.94,6.15),Polygon([(-1.23,0),(-.89,-.455),(.89,-.455),(1.23,0)])],grid_size=.001)
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
    for x in (-2.8,-2.,-1.,0.,1.,2.,2.8,3.6,4.3):
        check_ground(f'山墙前庭 {x:g}',[x,-1.2],False)
    for x in (-.8,0,.8):
        check_ground(f'凸窗台前 {x:g}',[x,-.58],False)
        check_ground(f'凸窗下方 {x:g}',[x,-.23],True)
    for x in (-2.83,-1.9,-.71,0,.71,1.9,2.83):
        check_ground(f'二层窗所在墙身 {x:g}',[x,.13],True)
        check_ground(f'与底图相接的原房 {x:g}',[x,5.7],True)
    for y in (.24,1.26,1.84,2.42):
        check_ground(f'山墙西侧返边外 {y:g}',[3.34,y],False)
    for x in (-2.,0.,2.):check_ground(f'保留原宅后部 {x:g}',[x,7.12],True)
    manifest = read(args.manifest)
    contract = {'id': ID, 'owner': {'macro_id': review['frozen_macro'], 'feature_local_id': OWNER},
                'source_feature_ids': {'building': [review['owner']['source_key'].split(':', 1)[1]], 'building_part': []},
                'replacement_geometry': site.wgs(cut), 'collision_geometry': site.wgs(collision), 'source_section_caps': caps,
                'lng': site.lon, 'lat': site.lat, 'heading': review['author_frame']['runtime_heading_deg'], 'scale': 1, 'altitude': 0,
                'model_geometry_sha256': {key: asset['sha256']for key, asset in assets.items()}, 'bounds_glb': bounds,
                'overviewBearing': 161.43, 'overviewPitch': 34, 'overviewZoom': 20.42, 'maxDistance': 460, 'lod_switch_in_m': 590, 'lod_switch_out_m': 755,
                'navigation': {'listed': False, 'status': '从皋兰路向南看17号灰卵石山墙、百叶与凸窗。'},
                'placement': {'status': 'map-aligned', 'note': '市表4C009。17号门柱、2015与2022照片以及2020两处相机定到251西翼，局部展现实际向街突出的山墙与凸窗。'},
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
