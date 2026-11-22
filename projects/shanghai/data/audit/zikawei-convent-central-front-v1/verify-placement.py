"""Bind the photographed upper garden wall to its own source, keeping the ground floor."""
from argparse import ArgumentParser
from pathlib import Path
import sys

import numpy as np
import shapely as geo
from shapely.geometry import MultiLineString, Point, box, mapping

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / 'tools'))
from candidate_placement_meshes import PlacementMeshes, read, sha, write
from build_candidate_city_integrations import checked_geometry

ID = 'xuhui-zikawei-convent-central-front'
OWNER = 673
BASE = 5.48
CUT = box(-10.12, -.10, 10.12, 3.97)


def verify_ground(source, collision):
    cases = []
    for x in (-5.9, -4.9, -3.9, -2.7, -1.7, -.8):
        cases.extend([
            ('garden in front of glazing', x, -2.25, False, False),
            ('closed glazed porch', x, -1.15, True, True),
            ('retained ground floor below the upper cut', x, 1.35, True, True)])
    for x in (-8.2, .65, 3.15, 6.2, 8.7):
        cases.extend([
            ('garden in front of preserved ground floor', x, -.4, False, False),
            ('unmodelled original lower wall below the new facade', x, 1.28, True, True)])
    for x in (-11.3, 11.3):
        cases.append(('adjoining existing wing outside the facade cut', x, 3.18, False, True))
    out = []
    for name, x, y, obstacle, blocked in cases:
        pt = Point(x, y)
        actual = collision.covers(pt)
        under_cut = CUT.covers(pt)
        assert actual == obstacle and (actual or source.covers(pt) and not under_cut) == blocked, (name,x,y,actual)
        out.append(dict(name=name, xy=[x,y], source_cut=under_cut, model_obstacle=actual,
                        expected_map='building' if blocked else None))
    return out


def main():
    args = ArgumentParser(description=__doc__)
    args.add_argument('--manifest', required=True, type=Path)
    args.add_argument('--work', required=True, type=Path)
    args.add_argument('--out', default=HERE, type=Path)
    options = args.parse_args()
    review = read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site = PlacementMeshes(PROJECT, options.work, review)
    assets, bounds, projection, physical = site.decode_model(options.manifest)
    source = site.footprints[OWNER]
    group = next(r for r in review['near_tiles'] if OWNER in r['feature_local_ids'])
    # The enclosed area behind the two photographed glazed bays is solid for walking.
    # Under the four high windows, the original source remains solid below 5.48 m.
    veranda = box(-6.62, -1.77, -.25, 1.05)
    original_ground = source.intersection(CUT)
    collision = geo.union_all([physical, veranda, original_ground], grid_size=.001).simplify(.005)
    assert collision.is_valid and original_ground.difference(collision).area < .003
    original = site.decode_group(group, OWNER)
    native = {}
    seams = {}
    heights = []
    for variant, (mesh, others, assignment) in original.items():
        z = mesh[:,:,2]
        top = float(z.max())
        assert 15.85 < top < 15.87
        heights.append(top)
        profile = site.project_faces(mesh)
        projected = geo.convex_hull(geo.multipoints(mesh[:,:,:2]))
        references = geo.intersects(projected, CUT)
        intersects = references & (z.max(axis=1) >= BASE) & (z.min(axis=1) <= top+.05)
        entirely_below = references & (z.max(axis=1) < BASE)
        assert intersects.any()
        other_distance = site.project_faces(others).distance(CUT)
        assert other_distance > 1.35
        retained = 100 * profile.difference(CUT).area / profile.area
        assert retained > 93
        seam = profile.intersection(CUT.boundary)
        assert seam.geom_type=='LineString' and len(seam.coords)==4
        seams[variant] = seam
        native[variant] = dict(owned_triangles=len(mesh), other_group_triangles=len(others),
            triangles_intersecting_height_limited_cut=int(intersects.sum()),
            triangles_wholly_below_cut_in_window=int(entirely_below.sum()), retained_percent=retained,
            owner_source_height_m=top, other_geometry_clearance_m=other_distance, assignment=assignment)
    assert max(heights)-min(heights)<.001
    differential = seams['near'].hausdorff_distance(seams['far'])
    assert differential < .08
    coords = list(seams['far'].coords)
    cap = MultiLineString([[a,b] for a,b in zip(coords,coords[1:])])
    roof = heights[1]
    ready = read(site.files['READY.json'])
    ref = [ready['origin_longitude'], ready['origin_latitude']]
    owner = {'macro_id':review['frozen_macro'], 'feature_local_id':OWNER}
    key = next(r['key'] for r in review['owners'] if r['local_id']==OWNER)
    assert key.startswith('building:')
    ids = {'building':[key.split(':',1)[1]], 'building_part':[]}
    volume = dict(id=ID+'-upper-garden-front', owner=owner, geometry=site.wgs(CUT), source_feature_ids=ids,
        min_height=BASE,max_height=roof+.05,height_reference=ref,
        source_section_caps=dict(geometry=site.wgs(cap),base_m=BASE,roof_m=roof,
                                 height_reference=ref,far_sha256=sha(site.files['far.glb'])))
    heading = review['author_frame']['runtime_heading_deg']
    contract = dict(id=ID,owner=owner,replacement_geometry=None,source_feature_ids={'building':[],'building_part':[]},
        site_replacement=volume,collision_geometry=site.wgs(collision),lng=site.lon,lat=site.lat,heading=heading,
        scale=1,altitude=0,bounds_glb=bounds,model_geometry_sha256={k:v['sha256'] for k,v in assets.items()},
        overviewBearing=40,overviewPitch=43,overviewZoom=19.55,maxDistance=500,lod_switch_in_m=260,lod_switch_out_m=350,
        navigation=dict(listed=False,status='从庭院看旧主楼中央四开间山花和西侧玻璃廊。'),
        placement=dict(status='map-aligned',note='按屋面影像将四轴中央山花对准第673号源庭院侧。位置和绝对尺度为估计。两侧原翼与中央下层保留。'),
        partial_model=True,model_scope=read(options.manifest)['scope'])
    checked_geometry(contract['collision_geometry'],'garden porch and retained ground floor',collision=True)
    checked_geometry(volume['geometry'],'upper garden wall rectangle')
    ground = verify_ground(source,collision)
    options.out.mkdir(exist_ok=True, parents=True)
    write(options.out/'final-placement-contract.json',contract)
    write(options.out/'placement-geometry.json',dict(id=ID,assets=assets,manifest_sha256=sha(options.manifest),
        source_area_m2=source.area,model_projection_m2=projection.area,glazed_veranda_m2=veranda.area,
        kept_lower_floor_under_upper_cut_m2=original_ground.area,collision_m2=collision.area,source_variants=native,
        source_ground_retained_percent=100, source_vertical_window_m=[BASE,roof+.05],cap_segments=len(cap.geoms),
        cap_near_far_horizontal_difference_m=differential,ground_probes=ground,
        estimate='2016 photograph, central roofline and 2013 and 2026 street photographs; absolute setting is approximate.',
        checker_sha256=sha(Path(__file__)), decoder_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))


if __name__=='__main__':
    main()
