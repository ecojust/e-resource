"""Limit the replacement to the photographed southern three-bay front below the later storeys."""
from argparse import ArgumentParser
from pathlib import Path
import math
import runpy
import sys

import numpy as np
import shapely as geo
from shapely.geometry import Point, MultiLineString, box

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
section=runpy.run_path(str(HERE.parent/'sino-french-school-v1/verify-placement.py'))['solid_section']
ID='huangpu-china-south-sea-bank-front'
OWNER=53
CUT_HEIGHT=16.58
COLUMNS=(-6.60,-2.20,2.20,6.60)


def cuts(projection, footprint):
    lines=[]
    for piece in geo.get_parts(geo.line_merge(footprint.boundary.intersection(projection))):
        coords=list(piece.coords)
        for a,b in zip(coords,coords[1:]):
            if math.dist(a,b)>.004:
                lines.append([a,b])
    result=MultiLineString(lines)
    assert not result.is_empty and footprint.boundary.buffer(.00002).covers(result)
    return result


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',required=True,type=Path)
    parser.add_argument('--work',required=True,type=Path)
    parser.add_argument('--out',default=HERE,type=Path)
    args=parser.parse_args()
    args.out.mkdir(exist_ok=True,parents=True)
    data=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,data)
    assets,bounds,projection,_=site.decode_model(args.manifest)
    assert 16.56<bounds['max'][1]<CUT_HEIGHT
    cut=box(-8.54,-2.35,8.54,.60)
    source=site.footprints[OWNER]
    ground=[]
    for item in read(site.work/'delivered-decode.json'):
        triangles=np.fromfile(item['triangle_file'],np.float64).reshape(-1,3,3)
        local=triangles[:,:,[0,2,1]]*[1,-1,1]
        ground.append(section(local,.551))
    # A section above the sill keeps the ground open between the paired columns and doors.
    # Keep its geometry within 3 cm of both variants when simplifying the round shafts.
    collision=ground[0].simplify(.022,preserve_topology=True)
    for profile in ground:
        assert collision.hausdorff_distance(profile)<.04
    group=data['near_tiles'][0]
    assert set(group['feature_local_ids'])=={53,539,1718,1782,2201}
    variants={}
    seams={}
    for level,(mesh,other,assignment) in site.decode_group(group,OWNER).items():
        footprint=site.project_faces(mesh)
        seams[level]=cuts(footprint,cut)
        xy=geo.convex_hull(geo.multipoints(mesh[:,:,:2]))
        vertical=mesh[:,:,2]
        in_plan=geo.intersects(xy,cut)
        in_volume=in_plan&(vertical.min(axis=1)<CUT_HEIGHT)&(vertical.max(axis=1)>-.06)
        roof=vertical.max()
        other_distance=float(np.min(geo.distance(cut,geo.convex_hull(geo.multipoints(other[:,:,:2])))))
        retained=100*footprint.difference(cut).area/footprint.area
        assert 98<retained<99 and 25.59<roof<25.61 and other_distance>12
        assert in_volume.any() and (in_plan&(vertical.min(axis=1)>=CUT_HEIGHT)).any()
        variants[level]=dict(original_triangles=len(mesh),horizontal_footprint_retained_pct=retained,
            original_roof_m=float(roof),original_upper_fabric_retained_m=float(roof-CUT_HEIGHT),
            lower_cut_projected_triangles=int(in_volume.sum()),in_plan_triangles_entirely_above_cut=int((in_plan&(vertical.min(axis=1)>=CUT_HEIGHT)).sum()),
            peer_triangles=len(other),nearest_peer_surface_m=other_distance,assignment=assignment)
    agreement=seams['near'].hausdorff_distance(seams['far'])
    assert agreement<.35
    ready=read(site.files['READY.json'])
    reference=[ready['origin_longitude'],ready['origin_latitude']]
    source_key=next(item['key'][9:]for item in data['owners'] if item['local_id']==OWNER)
    owner=dict(macro_id=data['frozen_macro'],feature_local_id=OWNER)
    bounded=dict(id=ID+'-lower-colonnade',owner=owner,geometry=site.wgs(cut),
        source_feature_ids=dict(building=[source_key],building_part=[]),min_height=-.06,max_height=CUT_HEIGHT,
        height_reference=reference,source_section_caps=dict(geometry=site.wgs(seams['far']),base_m=0,roof_m=CUT_HEIGHT,
        height_reference=reference,far_sha256=sha(site.files['far.glb'])))
    contract=dict(id=ID,owner=owner,source_feature_ids=dict(building=[],building_part=[]),replacement_geometry=None,
        site_replacement=bounded,collision_geometry=site.wgs(collision),bounds_glb=bounds,lng=site.lon,lat=site.lat,
        heading=data['author_frame']['runtime_heading_deg'],scale=1,altitude=0,
        model_geometry_sha256={k:v['sha256'] for k,v in assets.items()},
        overviewBearing=-12,overviewPitch=46,overviewZoom=20.10,maxDistance=490,lod_switch_in_m=610,lod_switch_out_m=745,
        navigation=dict(listed=False,status='从汉口路看中央三开间巨柱列及三座门廊。'),
        placement=dict(status='map-aligned',note='依汉口路110号独立地块南边的中央凹口定位。限高承接原上部窗墙，仅替换二至四层柱列及底层门廊所在的一小段。'),
        partial_model=True,model_scope=read(args.manifest)['scope'])
    checked_geometry(bounded['geometry'],'bounded Hankou south front')
    checked_geometry(contract['collision_geometry'],'granite portals and columns',collision=True)
    probes=[]
    def probe(name,x,y,expected,overall):
        pt=Point(x,y)
        solid=collision.covers(pt);old=source.covers(pt) and not cut.covers(pt)
        assert all(p.covers(pt)==expected for p in ground)
        assert solid==expected and (old or solid)==overall,(name,x,y,solid,old)
        probes.append(dict(name=name,xy=[x,y],wgs84=site.to_wgs(np.array([[x,y]]))[0].tolist(),
            model_obstacle=solid,source_cut=cut.covers(pt),expected_map='building' if overall else None))
    for x in COLUMNS:
        for dx in (-.437,.437):
            probe('granite shaft at pedestrian height',x+dx,-1.32,True,True)
        probe('gap between the two column shafts',x,-1.32,False,False)
        probe('wall section beyond the paired columns',x,.18,True,True)
    for x in (-4.4,0,4.4):
        for y in (-2.52,-1.32,-.49,-.05):
            probe('approach and covered threshold',x+.24,y,False,False)
        probe('closed glazed door',x+.24,.312,True,True)
        probe('original room behind the doorway',x+.24,.92,False,True)
    for x in (-10,10):
        probe('retained adjacent stone wing',x,-.25,False,True)
    neighbors=[]
    for i in data['selection']['checked_neighbors']:
        fp=site.footprints[i]
        assert fp.distance(cut)>2.0
        neighbors.append(dict(owner=i,distance_to_cut_m=fp.distance(cut),intersection_m2=fp.intersection(cut).area))
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,source_variants=variants,assets=assets,
        source_m2=source.area,source_cut_m2=source.intersection(cut).area,collision_m2=collision.area,
        model_projection_m2=projection.area,cap_segments=len(seams['far'].geoms),seam_agreement_m=agreement,
        model_collision_max_boundary_error_m=max(collision.hausdorff_distance(p) for p in ground),
        neighbors=neighbors,ground_probes=probes,checker_sha256=sha(Path(__file__)),manifest_sha256=sha(args.manifest)))

if __name__=='__main__':
    main()
