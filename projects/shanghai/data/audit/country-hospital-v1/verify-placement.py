"""Project this garden elevation and its actual near/far city neighbors.

Requires Node (module.registerHooks), NumPy and Shapely 2. Point --macro at
14-13718-6695 containing the four files bound by the source footprint review.
--manifest may also point to a staged model manifest. Writes two JSON reports.
"""
import argparse
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile

import numpy as np
import shapely as geom
from shapely.geometry import box, mapping, shape

MODEL = "jingan-country-hospital"


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def project_triangles(triangles):
    pieces = []
    for start in range(0, len(triangles), 8192):
        faces = geom.polygons(triangles[start:start + 8192, :, :2])
        pieces.append(geom.union_all(faces[geom.area(faces) > 1e-11], grid_size=1e-7))
    return geom.union_all(pieces, grid_size=1e-7)


def ground_projection(triangles):
    # All model vertices above the site's minimum (including the shallow
    # foundation) through pedestrian head height. Clip crossing faces exactly.
    low = 2.0
    z = triangles[:, :, 2]
    projections = [project_triangles(triangles[z.max(axis=1) <= low])]
    for triangle in triangles[(z.min(axis=1) < low) & (z.max(axis=1) > low)]:
        polygon = []
        for a, b in zip(triangle, np.roll(triangle, -1, axis=0)):
            if a[2] <= low:
                polygon.append(a[:2])
            if (a[2] < low < b[2]) or (b[2] < low < a[2]):
                polygon.append((a + (b-a) * ((low-a[2])/(b[2]-a[2])))[:2])
        if len(polygon) >= 3:
            face = geom.Polygon(polygon)
            if face.area > 1e-11:
                projections.append(face)
    return geom.union_all(projections, grid_size=1e-7)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--macro', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    source_path = project / 'source/precise' / MODEL / 'footprint-review.json'
    source = read(source_path)
    manifest = read(args.manifest)
    assert manifest['id'] == source['model_id'] == MODEL
    checked = {}
    for file, expected in source['frozen_bindings'].items():
        path = args.macro / file.split(source['owner']['macro_id'] + '/')[1]
        assert path.stat().st_size == expected['bytes'] and digest(path) == expected['sha256'], file
        checked[path.name] = path.resolve()

    corner = source['model_envelope_wgs84']['coordinates'][0]
    lng, lat = np.mean(corner[:2], axis=0)  # Center of projected garden frontage
    uv = np.asarray(source['authoring_uv']['axes_enu'])
    k = 6371008.8 * math.cos(math.radians(lat))
    log0 = math.log(math.tan(math.pi/4 + math.radians(lat)/2))

    def to_uv(coordinates):
        east = np.radians(coordinates[:, 0] - lng) * k
        north = (np.log(np.tan(math.pi/4 + np.radians(coordinates[:, 1])/2)) - log0) * k
        return np.column_stack((east, north)) @ uv.T

    def to_wgs(coordinates):
        east, north = (coordinates @ uv).T
        return np.column_stack((lng + np.degrees(east / k),
            np.degrees(2*np.arctan(np.exp(north/k + log0)) - math.pi/2)))

    assets = {}
    bounds = []
    projections = []
    ground = []
    target = {}
    neighbors = {}
    source_roof_heights = {}
    postal = project / 'data/audit/postal-office-v1'
    decoders = [postal / 'map-decode-delivered.mjs', postal / 'map-decode-source.mjs']
    with tempfile.TemporaryDirectory() as directory:
        scratch = Path(directory)
        env = dict(os.environ, POSTAL_MAPPING_WORK=directory, POSTAL_REPO=str(project.parents[1]), POSTAL_ASSET_PREFIX='')
        for variant in ('raw', 'web', 'lod'):
            asset = manifest['assets']['full' if variant == 'web' else variant]
            path = (args.manifest.parent / asset['file']).resolve()
            assert digest(path) == asset['sha256'] and path.stat().st_size == asset['bytes']
            (scratch / (variant + '.glb')).symlink_to(path)
        subprocess.run(['node', decoders[0], scratch], env=env, check=True, stdout=subprocess.DEVNULL)
        for result in read(scratch/'delivered-decode.json'):
            variant = result['variant']
            asset = manifest['assets']['full' if variant == 'web' else variant]
            triangles = np.fromfile(result['triangle_file'], np.float64).reshape(-1,3,3)
            assert result['triangles'] == len(triangles) == asset['triangles']
            assert np.isfinite(triangles).all()
            bounds.append([triangles.min((0,1)), triangles.max((0,1))])
            # Model coordinates are x along frontage, y up, z toward garden.
            triangles = triangles[:,:,[0,2,1]] * [1,-1,1]
            projections.append(project_triangles(triangles))
            ground.append(ground_projection(triangles))
            assets[variant] = {key: result[key] for key in ('bytes', 'sha256', 'triangles')}
        rows = json.loads(gzip.decompress(checked['feature-table.json.gz'].read_bytes()))['features']
        contexts = [row for row in rows if row['localId'] in source['near']['local_ids']]
        write(scratch/'initial-local-frame.json', {'anchor': {'lng':lng, 'lat':lat}})
        write(scratch/'context-features.json', contexts)
        for name, file in [('baseline-near.glb.gz', Path(source['near']['file']).name),
                           ('baseline-far.glb', 'far.glb'), ('macro-READY.json', 'READY.json')]:
            (scratch/name).symlink_to(checked[file])
        subprocess.run(['node', decoders[1]], env=env, check=True, stdout=subprocess.DEVNULL)
        for variant in ('near', 'far'):
            triangles = np.fromfile(scratch/f'baseline-{variant}-triangles.f64').reshape(-1,3,3)
            triangles[:,:,:2] = triangles[:,:,:2] @ uv.T
            if variant == 'far':
                owners = np.fromfile(scratch/'baseline-far-owners.u32', np.uint32)
            else:
                # The near asset merges owners. Identify the isolated target
                # by distances to every footprint registered in the actual tile.
                points = geom.points(triangles[:,:,:2].mean(axis=1))
                footprints = [geom.transform(shape(r['geometry']), to_uv) for r in contexts]
                distances = np.stack([geom.distance(points, p) for p in footprints], axis=1)
                owners = np.array([r['localId'] for r in contexts])[distances.argmin(axis=1)]
                ordered = np.sort(distances, axis=1)
                target_rows = owners == source['owner']['feature_local_id']
                max_distance = float(ordered[:,0].max())
                target_gap = float((ordered[target_rows,1] - ordered[target_rows,0]).min())
                assert max_distance < .2 and target_gap > 2
            is_target = owners == source['owner']['feature_local_id']
            assert is_target.any() and len(set(owners[~is_target])) == 15
            source_roof_heights[variant] = float(triangles[is_target,:,2].max())
            target[variant] = project_triangles(triangles[is_target])
            neighbors[variant] = project_triangles(triangles[~is_target])

    full = geom.union_all(projections)
    structural = geom.union_all(ground)
    # Keep tight structural obstacles, including the modeled pier plinths.
    # Dissolve sub-decimetre mesh seams, preserving the deep open arcade bays.
    collision = structural.buffer(.025, join_style='mitre').simplify(.012)
    assert structural.difference(collision).area < 1e-6 and collision.difference(structural.buffer(.06)).area < .001
    x0, _, x1, rear = full.bounds
    assert 76 < x1 - x0 < 79 and 4 < rear < 5
    # The adjacent wings reach further back than the central portico. Determine
    # their actual inner edges where the geometry exceeds the central depth.
    deep = full.intersection(box(x0-1, 3.6, x1+1, rear+1))
    left = deep.intersection(box(x0-1, 0, 0, rear+1)).bounds[2] + .02
    right = deep.intersection(box(0, 0, x1+1, rear+1)).bounds[0] - .02
    assert left < -8 < 8 < right
    center_rear = full.intersection(box(left, -10, right, rear+1)).bounds[3]
    limit = min(p.bounds[1] for p in target.values()) - .03
    clip = geom.union_all([box(x0-.015, limit, left, rear+.015),
                           box(left, limit, right, center_rear+.015),
                           box(right, limit, x1+.015, rear+.015)]).simplify(.00001)
    assert clip.covers(full)
    assert all(clip.distance(p) > 5 for p in neighbors.values())
    assert all(p.difference(clip).area / p.area > .74 for p in target.values())
    # Include other macros/tile owners from the repository's feature table.
    surrounding = [(r['localId'], geom.transform(shape(r['geometry']), to_uv))
                   for r in rows if r['localId'] != source['owner']['feature_local_id']
                   and shape(r['geometry']).distance(geom.Point(lng,lat)) < .0015]
    assert min(p.distance(clip) for _, p in surrounding) > 5
    collision_wgs = mapping(geom.transform(collision, to_wgs))
    clip_wgs = mapping(geom.transform(clip, to_wgs))
    bounds = np.array(bounds)
    owner = {k:source['owner'][k] for k in ('macro_id','feature_local_id')}
    ids = {'building':[source['owner']['source_key'].split(':',1)[1]], 'building_part':[]}
    # Close only the newly exposed cut through the retained, hollow source
    # mesh. The far roof gives the shared underlying structural wall outline.
    # Small near window projections are ornaments, not a longer cut plane.
    seam = geom.line_merge(clip.boundary.intersection(target['far']))
    assert seam.geom_type == 'LineString' and not seam.is_ring
    seam = seam.simplify(.001)
    assert len(seam.coords) == 8  # Two ends, two shoulders, three backs.
    other_seam = geom.line_merge(clip.boundary.intersection(target['near']))
    assert seam.hausdorff_distance(other_seam) < .15
    assert min(v for _, v in seam.coords) > limit
    assert all(seam.distance(p) > 5 for p in neighbors.values())
    assert abs(source_roof_heights['far'] - source_roof_heights['near']) < .01
    macro = read(checked['READY.json'])
    section_caps = {
        'geometry': mapping(geom.MultiLineString([geom.transform(seam, to_wgs)])),
        'base_m': 0, 'roof_m': source_roof_heights['far'],
        'height_reference': [macro['origin_longitude'], macro['origin_latitude']],
        'far_sha256': digest(checked['far.glb']),
    }
    # Bearing is the direction of the camera's view toward the facade.
    contract = {
        'id':MODEL, 'lng':lng, 'lat':lat, 'heading':-15, 'scale':1, 'altitude':0,
        'owner':owner, 'source_section_caps':section_caps, 'source_feature_ids':ids, 'collision_geometry':collision_wgs,
        'replacement_geometry':clip_wgs, 'model_geometry_sha256':{k:v['sha256'] for k,v in assets.items()},
        'bounds_glb':{'min':bounds[:,0].min(0).tolist(),'max':bounds[:,1].max(0).tolist()},
        'overviewBearing':-15, 'overviewPitch':63, 'overviewZoom':18.6,
        'maxDistance':480, 'lod_switch_in_m':550, 'lod_switch_out_m':700,
        'navigation':{'listed':False,'status':'庭园立面俯瞰，无室内或登楼路线。'},
        'placement':{'status':'estimated','note':'花园侧历史立面按照片与航影估位，源2764的背部与两端仍用地图体块。'},
        'partial_model':True, 'model_scope':'宏恩医院历史主楼南向花园立面浅段（中央及两端柱廊和中间开间）；其余侧后翼、屋顶、连接体及室内待核。'
    }
    import sys
    sys.path.insert(0,str(project/'tools'))
    from build_candidate_city_integrations import checked_geometry
    # Use JSON list types as in actual production serialization.
    checked_geometry(json.loads(json.dumps(collision_wgs)), 'garden structural collision', collision=True)
    checked_geometry(json.loads(json.dumps(clip_wgs)), 'garden source clip')
    metrics = {}
    for variant in target:
        profile = target[variant]
        kept = profile.difference(clip)
        metrics[variant] = {
            'target_projection_m2':profile.area, 'remaining_target_m2':kept.area,
            'retained_fraction':kept.area/profile.area, 'other_owners_overlap_m2':neighbors[variant].intersection(clip).area,
            'other_owners_clearance_m':neighbors[variant].distance(clip)
        }
    review = {
        'id': MODEL, 'manifest_sha256':digest(args.manifest), 'source_footprint_review_sha256':digest(source_path),
        'script_sha256':digest(Path(__file__)), 'decoder_sha256':{p.name:digest(p) for p in decoders},
        'assets':assets, 'source_inputs':source['frozen_bindings'], 'partial_model':True,
        'method':'Foot of image-aligned projecting porticos at midpoint of the two southern roof-envelope corners. Local +X runs at 75 degrees, -Z at 345 degrees. Actual transformed GLB triangles projected for each variant. Near merged triangle centroids compared to all 16 tile footprints; far uses per-vertex feature IDs. A stepped display mask extends gardenward to clear the mismatched 24.1 m source front wall. Back of the source block remains an estimated mass behind the shorter relief.',
        'near_centroid_max_distance_m':max_distance,'target_near_min_distance_advantage_m':target_gap,
        'source_results':metrics,'other_nearby_source_footprints_checked':len(surrounding),
        'other_source_footprint_clearance_m':min(p.distance(clip) for _,p in surrounding),
        'source_cut_section':{'seam_uv_m':mapping(seam),'length_m':seam.length,'near_far_seam_hausdorff_m':seam.hausdorff_distance(other_seam),'heights_at_source_macro_m':source_roof_heights,'method':'Seven interior cut edges end at the decoded source roof perimeter. The straight original garden wall is not capped. Planes use the coarse-source height, not historical elevation; no model or third-party data bytes are changed.'},
        'ground_method':'Only geometry from the lowest modeled plinth to 2 m above grade; clipped triangle projections buffered 0.025 m and simplified 0.012 m, with uncovered structural area and excess padding checked. Garden ground and the unmodeled building site are excluded.',
        'ground_union_m2':structural.area,'collision_m2':collision.area,
        'clip_uv_m':mapping(clip),'model_uv_bounds_m':full.bounds,'center_rear_m':center_rear,
        'proposed_placement_contract':contract,
    }
    write(output/'footprint-review.json', review)
    write(output/'final-placement-contract.json', contract)
    print(json.dumps(metrics))

if __name__ == '__main__':
    main()
