"""Register only the low door-and-window patch, preserving the original row above it."""
from argparse import ArgumentParser
from pathlib import Path
import runpy
import sys

import numpy as np
import shapely as geo
from shapely.geometry import MultiLineString

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / 'tools'))
from candidate_placement_meshes import PlacementMeshes, read, sha, write
from build_candidate_city_integrations import checked_geometry
solid_section = runpy.run_path(str(PROJECT / 'data/audit/sino-french-school-v1/verify-placement.py'))['solid_section']
IDENT = 'jingan-mofan-village-no22-entrance'
OWNER = 1275
CUT_TOP = 3.10


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--out', type=Path, default=HERE)
    args = parser.parse_args()
    args.out.mkdir(exist_ok=True, parents=True)
    review = read(PROJECT / 'source/precise' / IDENT / 'footprint-review.json')
    site = PlacementMeshes(PROJECT, args.work, review)
    assets, bounds, projection, _ = site.decode_model(args.manifest)
    assert 3.099 < bounds['max'][1] < 3.101
    # The brick lane apron and sill project outside the existing wall and require no cut.
    cut = geo.box(-1.857, -.14, 1.857, .747)
    source = site.footprints[OWNER]
    assert source.intersection(cut).area / source.area < .012
    models = []
    for item in read(site.work / 'delivered-decode.json'):
        mesh = np.fromfile(item['triangle_file'], np.float64).reshape(-1, 3, 3)[:, :, [0, 2, 1]] * [1, -1, 1]
        models.append(solid_section(mesh, .449))
    collision = models[0]
    assert all(collision.symmetric_difference(poly).area < .003 for poly in models)
    # Reconstruct an independent horizontal plan at 0.449m, above the skirting
    # and below the sill. Include the inner and outer jambs projecting from the returns.
    expected = geo.union_all([geo.box(-1.84, 0, .66, .20), geo.box(1.57, 0, 1.84, .20),
        geo.box(.572, 0, .66, .67), geo.box(1.57, 0, 1.658, .67),
        geo.box(.66, -.022, .71, .068), geo.box(1.52, -.022, 1.57, .068),
        geo.box(.6625, .615, .7075, .689), geo.box(1.5225, .615, 1.5675, .689)])
    assert collision.is_valid and collision.symmetric_difference(expected).area < 1e-5
    group = next(it for it in review['near_tiles'] if OWNER in it['feature_local_ids'])
    surfaces = site.decode_group(group, OWNER)
    variants = {}
    for variant, (mesh, neighbors, assignment) in surfaces.items():
        original_height = float(mesh[:, :, 2].max())
        assert 27.29 < original_height < 27.31
        xy = geo.convex_hull(geo.multipoints(mesh[:, :, :2]))
        heights = mesh[:, :, 2]
        meets_horizontal = geo.intersects(xy, cut)
        touches = meets_horizontal & (heights.min(axis=1) <= CUT_TOP) & (heights.max(axis=1) >= -.06)
        preserved_above = meets_horizontal & (heights.min(axis=1) > CUT_TOP)
        assert np.any(touches)
        distance = float(np.min(geo.distance(cut, geo.convex_hull(geo.multipoints(neighbors[:, :, :2])))))
        assert distance > 1.5
        variants[variant] = dict(owner_triangles=len(mesh), bounding_triangles_intersecting_low_volume=int(touches.sum()),
            triangles_wholly_above_even_within_horizontal_mask=int(preserved_above.sum()),
            other_group_triangles=len(neighbors), closest_other_geometry_m=distance, unchanged_roof_m=original_height,
            upper_wall_retained_m=original_height-CUT_TOP, assignment=assignment)
    ids = dict(building=[next(v['key'][9:] for v in review['owners'] if v['local_id']==OWNER)], building_part=[])
    owner = dict(macro_id=review['frozen_macro'], feature_local_id=OWNER)
    ready = read(site.files['READY.json'])
    reference = [ready['origin_longitude'], ready['origin_latitude']]
    west, _, east, back = cut.bounds
    cap_lines = MultiLineString([[(west, 0), (west, back)], [(west, back), (east, back)], [(east, back), (east, 0)]])
    low_opening = dict(id=IDENT+'-street-opening', owner=owner, geometry=site.wgs(cut), source_feature_ids=ids,
        min_height=-.06, max_height=CUT_TOP, height_reference=reference,
        source_section_caps=dict(geometry=site.wgs(cap_lines), base_m=0, roof_m=CUT_TOP,
            height_reference=reference, far_sha256=sha(site.files['far.glb'])))
    heading = review['author_frame']['runtime_heading_deg']
    contract = dict(id=IDENT, owner=owner, replacement_geometry=None, source_feature_ids=dict(building=[],building_part=[]),
        site_replacement=low_opening, collision_geometry=site.wgs(collision),
        lng=site.lon, lat=site.lat, heading=heading, scale=1, altitude=0, bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256'] for k,v in assets.items()},
        overviewBearing=heading, overviewPitch=68, overviewZoom=21.8, maxDistance=245, lod_switch_in_m=175, lod_switch_out_m=230,
        navigation=dict(listed=False,status='从北侧通道面向22号门牌和凹门廊。'),
        placement=dict(status='map-aligned',note='北门东侧四户排的中部门对，22号位于东扇。保留1275号源3.10米以上的原立面。门槛经纬位置为照片配准估算。'),
        partial_model=True, model_scope=read(args.manifest)['scope'])
    probes=[]
    for x in [.815,1.075,1.37]:
        for y in [-.45,-.06,.15,.38,.61,.72]:
            probes.append(('approach and shallow covered doorstep',[x,y],False,False))
        probes.append(('source beyond the photographed threshold',[x,.81],False,True))
    for x in [-1.61,-.88,-.10,.32,1.74]:
        probes.append(('solid frontage beside the entrance',[x,.11],True,True))
    for x in [-2.03,2.03]:
        probes.append(('retained adjacent frontage',[x,.16],False,True))
    cases=[]
    for label,point,obstacle,blocked in probes:
        pt=geo.Point(*point)
        hit=collision.covers(pt);cut_here=cut.covers(pt)
        assert hit==obstacle and (hit or source.covers(pt) and not cut_here)==blocked,(label,point)
        cases.append(dict(name=label,xy=point,model_obstacle=hit,source_cut=cut_here,expected_map='building' if blocked else None))
    checked_geometry(low_opening['geometry'],'bounded low cut')
    checked_geometry(contract['collision_geometry'],'model collision',collision=True)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=IDENT,manifest_sha256=sha(args.manifest),assets=assets,
          source_m2=source.area,model_projection_m2=projection.area,collision_m2=collision.area,
          source_ground_cut_m2=source.intersection(cut).area,source_ground_retained_percent=100*(1-source.intersection(cut).area/source.area),
          variants=variants,threshold_uncertainty='Relative bay from photographs; not a surveyed doorstep.',
          ground_probes=cases,cap_segments=3,checker_sha256=sha(Path(__file__)),
          decoder_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))


if __name__=='__main__':
    main()
