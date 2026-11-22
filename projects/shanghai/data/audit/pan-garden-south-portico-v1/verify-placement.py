"""Check the partial courtyard elevation against the registered original building and adjoining facades."""
from pathlib import Path
import argparse, math, sys
import numpy as np
import shapely as geo
from shapely.geometry import MultiLineString, Point, Polygon, box, shape
HERE = Path(__file__).resolve().parent
PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / 'tools'))
from candidate_placement_meshes import PlacementMeshes, read, sha, write
from build_candidate_city_integrations import checked_geometry, check_source_section_caps

ID = 'jingan-pan-garden-south-portico'
OWNER = 2572



def load_values(file, dtype):
    if file.is_file():
        return np.fromfile(file, dtype)
    import gzip, hashlib
    values = gzip.decompress(file.with_name(file.name + '.gz').read_bytes())
    expected = file.with_name(file.name + '.sha256').read_text().strip()
    assert hashlib.sha256(values).hexdigest() == expected
    return np.frombuffer(values, dtype).copy()


def main(args):
    source = Path(__import__('os').environ.get('PAN_SOURCE_ROOT', PROJECT)) / 'source/precise' / ID
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
    # Walkable stairs and the slightly raised porch slab do not obstruct horizontal travel.
    # The authoritative obstructions are the masonry cheeks, the closed back wall, each shaft and the two small stone plinths.
    from shapely.geometry import box
    bays=[Polygon([(s*4.63,0),(s*5.07,0),(s*5.80,-.55),(s*9.27,-.55),(s*10.07,0),(s*10.95,0),(s*10.95,3.35),(s*4.63,3.35)]) for s in (-1,1)]
    front_parts=[*bays,box(-4.63,2.64,4.63,3.10)]
    front_parts.extend(box(x-.53,-.50,x+.53,.56) for x in (-2.12,2.12))
    front_parts.extend(box(x-.15,-.61,x+.15,-.25) for x in (-1.37,1.37))
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
    for x in (-10,-7,-4,-2.12,0,2.12,4,7,10):
        check_ground(f'庭院前地 {x:g}',[x,-2.7],False)
    for y in (-1.85,-1.2,-.65,-.05,.83,1.65,2.41):
        check_ground(f'中央弧阶与廊心 {y:g}',[0,y],False)
    for x in (-2.12,2.12):
        check_ground(f'石柱基 {x:g}',[x,.02],True)
    for x in (-1.37,1.37):
        check_ground(f'台上雕石方座 {x:g}',[x,-.43],True)
    for x in (-9,-7.4,7.4,9):
        check_ground(f'凸窗实体 {x:g}',[x,.44],True)
    for x in (-4.35,0,4.35):
        check_ground(f'门廊后墙 {x:g}',[x,2.75],True)
    for x in (-3.8,-1,1.,3.8):
        check_ground(f'廊下可通行 {x:g}',[x,.94],False)
    for x in (-7,0,7):
        check_ground(f'保留原楼 {x:g}',[x,4.04],True)
    manifest = read(args.manifest)
    contract = {'id': ID, 'owner': {'macro_id': review['frozen_macro'], 'feature_local_id': OWNER},
                'source_feature_ids': {'building': [review['owner']['source_key'].split(':', 1)[1]], 'building_part': []},
                'replacement_geometry': site.wgs(cut), 'collision_geometry': site.wgs(collision), 'source_section_caps': caps,
                'lng': site.lon, 'lat': site.lat, 'heading': review['author_frame']['runtime_heading_deg'], 'scale': 1, 'altitude': 0,
                'model_geometry_sha256': {key: asset['sha256']for key, asset in assets.items()}, 'bounds_glb': bounds,
                'overviewBearing': -67, 'overviewPitch': 55, 'overviewZoom': 19.78, 'maxDistance': 460, 'lod_switch_in_m': 590, 'lod_switch_out_m': 755,
                'navigation': {'listed': False, 'status': '院中朝向南楼，可见两根通高石柱与弧阶，上层石栏位于两柱后方。'},
                'placement': {'status': 'map-aligned', 'note': '市表4B024。院面21.9米与两期航片及市图廓的22米外弦合。仅切原房2572朝东南花园的前段。'},
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
