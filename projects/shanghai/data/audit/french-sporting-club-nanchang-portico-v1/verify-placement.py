"""Check the partial courtyard elevation against the registered original building and adjoining facades."""
from pathlib import Path
import argparse, math, sys
import numpy as np
import shapely as geo
from shapely.geometry import MultiLineString, Point, Polygon, box, shape
HERE = Path(__file__).resolve().parent
PROJECT = Path(__file__).resolve().parents[3]
if not (PROJECT/'tools').is_dir():
    PROJECT = Path.cwd()
sys.path.insert(0, str(PROJECT / 'tools'))
from candidate_placement_meshes import PlacementMeshes, read, sha, write
from build_candidate_city_integrations import checked_geometry, check_source_section_caps

ID = 'huangpu-french-sporting-club-nanchang-portico'
OWNER = 2366



def load_values(file, dtype):
    if file.is_file():
        return np.fromfile(file, dtype)
    import gzip, hashlib
    values = gzip.decompress(file.with_name(file.name + '.gz').read_bytes())
    expected = file.with_name(file.name + '.sha256').read_text().strip()
    assert hashlib.sha256(values).hexdigest() == expected
    return np.frombuffer(values, dtype).copy()


def main(args):
    source = Path(__import__('os').environ.get('SPORTING_CLUB_SOURCE_ROOT', PROJECT)) / 'source/precise' / ID
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
    # The gate blocks the central axis even where its railings are openwork.
    # The shallow threshold is walkable. Preserve each freestanding circular shaft.
    shaft_solids=[Point(x,0).buffer(.365,quad_segs=12) for x in (-1.421,1.421)]
    front_parts=[*shaft_solids,box(-1.105,-.03,1.105,.02),box(-3.68,1.54,3.68,1.85)]
    front_parts.extend(box(x-.10,1.55,x+.10,2.29) for x in (-3.68,3.68))
    collision=geo.union_all(front_parts,grid_size=.001)
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
    for x in (-4,-2,-1.421,-.5,0,.5,1.421,2,4):
        check_ground(f'南昌路人行道 {x:g}',[x,-.85],False)
    for x in (-.87,0,.87):
        check_ground(f'浅石阶前沿 {x:g}',[x,-.29],False)
        check_ground(f'铁门扇 {x:g}',[x,-.005],True)
    for x in (-1.421,1.421):
        check_ground(f'独立圆柱 {x:g}',[x,0],True)
    for x in (-2.7,-2,-.74,0,.74,2,2.7):
        check_ground(f'门廊内侧空地 {x:g}',[x,.94],False)
        check_ground(f'内退门窗所在墙身 {x:g}',[x,1.67],True)
    for x in (-2,0,2):
        check_ground(f'保留的原屋 {x:g}',[x,3.08],True)
    manifest = read(args.manifest)
    contract = {'id': ID, 'owner': {'macro_id': review['frozen_macro'], 'feature_local_id': OWNER},
                'source_feature_ids': {'building': [review['owner']['source_key'].split(':', 1)[1]], 'building_part': []},
                'replacement_geometry': site.wgs(cut), 'collision_geometry': site.wgs(collision), 'source_section_caps': caps,
                'lng': site.lon, 'lat': site.lat, 'heading': review['author_frame']['runtime_heading_deg'], 'scale': 1, 'altitude': 0,
                'model_geometry_sha256': {key: asset['sha256']for key, asset in assets.items()}, 'bounds_glb': bounds,
                'overviewBearing': 154, 'overviewPitch': 62, 'overviewZoom': 20.12, 'maxDistance': 460, 'lod_switch_in_m': 590, 'lod_switch_out_m': 755,
                'navigation': {'listed': False, 'status': '从南昌路看带题额的双柱门棚、镂砖阳台与上层券窗。'},
                'placement': {'status': 'map-aligned', 'note': '市表4C005。展馆实名底图与原屋2366吻合，仅替换南昌路一侧门棚和券窗阳台，保留两端及后部。'},
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
