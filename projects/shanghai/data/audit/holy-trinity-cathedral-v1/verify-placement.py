"""Register the main church with frozen city meshes and verify the three open walks."""
from argparse import ArgumentParser
from pathlib import Path
import sys
import numpy as np
import shapely as geo

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
sys.path.insert(0, str(PROJECT / 'tools'))
from candidate_placement_meshes import PlacementMeshes, read, write, sha
from build_candidate_city_integrations import checked_geometry

ID = 'huangpu-holy-trinity-cathedral'
OWNER = 587
NEIGHBORS = [616, 1810, 119, 1555]


def ground_geometry(site):
    """Only vertical obstacles and occupied floor plates should block the open arcades."""
    candidates = []
    for v in read(site.work / 'delivered-decode.json'):
        tris = np.fromfile(v['triangle_file'], np.float64).reshape(-1, 3, 3)
        local = tris[:, :, [0, 2, 1]] * [1, -1, 1]
        material = np.fromfile(v['triangle_material_ids_file'], np.uint16)
        paving = v['material_names'].index('porch pavement')
        candidates.append(site.ground_faces(local[material != paving]))
    result = geo.union_all(candidates, grid_size=.001).simplify(.055, preserve_topology=True)
    return result, [p.area for p in candidates]


def main():
    cli = ArgumentParser(description=__doc__)
    cli.add_argument('--manifest', type=Path, required=True)
    cli.add_argument('--work', type=Path, required=True)
    cli.add_argument('--out', type=Path, default=AUDIT)
    args = cli.parse_args()
    args.out.mkdir(exist_ok=True, parents=True)
    src = read(PROJECT / 'source/precise' / ID / 'footprint-review.json')
    site = PlacementMeshes(PROJECT, args.work, src)
    assets, bounds, profile, _ = site.decode_model(args.manifest)
    collision, areas = ground_geometry(site)
    source = site.footprints[OWNER]
    # The 0.50 m uniform offset encloses the city's projecting low-poly window sills.
    mask = source.buffer(.50, join_style='mitre')
    group = next(g for g in src['near_tiles'] if OWNER in g['feature_local_ids'])
    variants = {}
    for variant, (target, nearby, assignment) in site.decode_group(group, OWNER).items():
        target_shape = site.project_faces(target)
        other = site.project_faces(nearby)
        missed = target_shape.difference(mask).area
        covers = bool(geo.covers(mask, geo.multipoints(target[:, :, :2].reshape(-1, 2))))
        assert covers and missed < .00001 and mask.disjoint(other) and profile.disjoint(other), (variant, missed, covers)
        variants[variant] = dict(target_triangles=len(target), target_projected_m2=target_shape.area,
            uncovered_source_m2=missed, all_source_vertices_in_mask=covers, owner_assignment=assignment,
            other_owners=sorted(i for i in group['feature_local_ids'] if i != OWNER), other_triangles=len(nearby),
            mask_to_nearest_other_decoded_owner_m=mask.distance(other),
            model_to_nearest_other_decoded_owner_m=profile.distance(other))
    clearances = sorted((mask.distance(p), i, profile.distance(p)) for i, p in site.footprints.items() if i != OWNER)
    assert clearances[0][0] > 2 and min(c[2] for c in clearances) > 2
    part = next(o for o in src['owners'] if o['local_id'] == OWNER)
    heading = src['author_frame']['runtime_heading_deg']
    ground = []
    for name, xy, solid in [
        ('enclosed nave', [0,12], True), ('enclosed sanctuary', [0,43], True),
        ('occupied garden portal pier', [5.25,-4.25], True), ('open central garden portal', [0,-2.8], False),
        ('north covered walk', [10.78,12.03], False), ('south covered walk', [-10.78,12.03], False),
        ('garden approach', [0,-6.5], False)]:
        point = geo.Point(*xy)
        assert collision.covers(point) == solid, (name, collision.distance(point))
        ground.append(dict(name=name, xy=xy, expected='building' if solid else None, cut=bool(mask.covers(point))))
    case = dict(id=ID, previous='huangpu-shanghai-municipal-council', neighbors=NEIGHBORS,
        groupTriangles=len(mask.exterior.coords)-3,
        front=dict(center=[0,0], elevation=3.6, pitch=45, zoom=19.45, bearingOffset=32),
        roof=dict(center=[0,24], elevation=10, pitch=32, zoom=19.05, bearingOffset=34), ground=ground,
        neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates'] for i in NEIGHBORS})
    contract = dict(id=ID, owner=dict(macro_id=src['frozen_macro'],feature_local_id=OWNER),
        source_feature_ids=dict(building=[part['key'][9:]], building_part=[]), replacement_geometry=site.wgs(mask),
        collision_geometry=site.wgs(collision), lng=site.lon, lat=site.lat, heading=heading, scale=1, altitude=0,
        bounds_glb=bounds, model_geometry_sha256={k:v['sha256'] for k,v in assets.items()},
        overviewBearing=heading+32, overviewPitch=45, overviewZoom=18.8, maxDistance=480,
        lod_switch_in_m=550,lod_switch_out_m=700, navigation=dict(listed=False,status='江西中路花园一侧俯瞰主堂。'),
        placement=dict(status='estimated',note='原点取东山墙边线中点。主堂替换587，保留钟塔、旧校楼和周围建筑；门廊及南北敞廊保留地面通行。'),
        partial_model=True,model_scope=read(args.manifest)['scope'])
    for kind in ['collision','replacement']:
        checked_geometry(contract[kind+'_geometry'],kind,collision=kind=='collision')
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'map-case.json',case)
    write(args.out/'placement-geometry.json', dict(model=ID,manifest_sha256=sha(args.manifest),variants=assets,
        macro=src['frozen_macro'],nearTile=group,owner=OWNER,scope='近远景完整替换源587，保留校楼1810、钟塔位置616及东侧庭园。',
        source=variants, source_mask_m2=mask.area, candidate_projection_m2=profile.area, collision_m2=collision.area,
        ground_m2_by_variant=areas, collision_method='按三个 GLB 的地面上方两米投影取并集。剔除有顶敞廊的步道铺面，保留独立石柱、实墙和封闭教堂地板；轮廓简化容差0.055米。',
        ground_witnesses=ground, neighbor_clearances=[dict(local_id=i,mask_m=d,model_m=c) for d,i,c in clearances[:10]],
        retained_blocks=NEIGHBORS,script_sha256=sha(Path(__file__)),shared_checker_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))


if __name__ == '__main__':
    main()
