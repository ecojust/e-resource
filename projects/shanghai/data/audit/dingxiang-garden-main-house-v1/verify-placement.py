"""Measure the pictured garden entrance against the two city meshes and retain the rest of House One."""
import argparse
from pathlib import Path
import sys

import numpy as np
import shapely as geo
from shapely.geometry import LineString, MultiLineString

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes, read, write, sha
from build_candidate_city_integrations import checked_geometry

ID='xuhui-dingxiang-garden-main-house'
OWNER=1353


def model_obstacles():
    # Walkable steps and the landing sit below both open side arches.
    parts=[geo.box(-3.93,0,3.93,.27),geo.box(-3.93,.27,-3.71,3.8),
           geo.box(3.71,.27,3.93,3.8)]
    center=1.14
    for sign in (-1,1):
        l,r=sorted([center+sign*.9516,center+sign*1.56])
        parts.append(geo.box(l,-2.43,r,-2.195))
    for x in (center-1.56,center+1.56-.235):
        for l,r in ((-2.195,-1.215-.74115),(-1.215+.74115,0)):
            parts.append(geo.box(x,l,x+.235,r))
    angles=np.radians(np.linspace(177,290,21))
    arc=LineString([(-4.38+1.30*np.cos(a),1.56+1.30*np.sin(a))for a in angles])
    parts.append(arc.buffer(.107,cap_style=2))
    wing=LineString([(3.93,.68),(4.81,-.16),(6.11,.02),(6.86,1.10),(6.68,2.56)])
    parts.append(wing.buffer(.225,single_sided=True,join_style=2))
    return geo.union_all(parts,grid_size=.001)


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    cli.add_argument('--work',required=True,type=Path)
    cli.add_argument('--out',default=HERE,type=Path)
    args=cli.parse_args()
    args.out.mkdir(exist_ok=True,parents=True)
    ref=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,ref)
    assets,bounds,projection,ground=site.decode_model(args.manifest)
    group,=ref['near_tiles']
    native_poly=site.footprints[OWNER]
    cut=geo.box(-6.12,-3.31,7.16,3.86)
    assert cut.covers(projection.buffer(-.012)) or projection.difference(cut).area<.15
    collision=model_obstacles()
    assert cut.covers(collision)
    variants={}
    seams={}
    own_heights=[]
    for variant,(own,others,assignment) in site.decode_group(group,OWNER).items():
        native=site.project_faces(own)
        front=native.intersection(cut)
        remainder=native.difference(cut)
        assert .045<front.area/native.area<.16 and native_poly.intersection(native).area/native.area>.85
        common=cut.boundary.intersection(native)
        segments=[line for line in geo.get_parts(common) if line.geom_type=='LineString' and line.length>.12]
        assert segments
        seams[variant]=MultiLineString(segments)
        close=others[(np.abs(others[:,:,:2].mean(axis=1))<75).all(axis=1)]
        clearance=site.project_faces(close).distance(cut)
        assert clearance>1
        maximum=float(own[:,:,2].max())
        own_heights.append(maximum)
        faces=geo.polygons(own[:,:,:2])
        variants[variant]=dict(owner_triangles=len(own),affected_faces=int(geo.intersects(faces,cut).sum()),
                               original_area_m2=native.area,retained_area_m2=remainder.area,
                               retained_fraction=remainder.area/native.area,original_height_m=maximum,
                               crop_to_nearest_other_mesh_m=clearance,assignment=assignment)
    seam_delta=seams['far'].hausdorff_distance(seams['near'])
    assert seam_delta<2.2,seam_delta
    origin=read(site.files['READY.json'])
    reference=[origin['origin_longitude'],origin['origin_latitude']]
    cap=dict(geometry=site.wgs(seams['far']),base_m=0,roof_m=min(own_heights),height_reference=reference,far_sha256=sha(site.files['far.glb']))
    samples=[('front outside',1.14,-3.60,False),('first entrance tread',1.14,-3.10,False),
             ('porch interior',1.14,-1.2,False),('right arch passage',2.70,-1.21,False),
             ('left arch passage',-.42,-1.21,False),('right abutment',2.44,-2.33,True),
             ('left abutment',-.14,-2.33,True),('through arch toward door',1.14,-.15,False),
             ('closed inner door',1.14,.13,True),('main wall below paired upper windows',-1.48,.15,True),
             ('gable return',3.82,2.69,True),('right bay wall',5.44,.064,True),
             ('grass beside landing',3.36,-2.65,False),('beyond rounded wing',-6.0,.95,False),
             ('retained interior',1,6.0,False),('retained main body',-8.7,12.2,False)]
    probes=[]
    for name,x,y,want in samples:
        pos=geo.Point(x,y);blocked=collision.covers(pos);assert blocked==want,(name,blocked)
        retained=native_poly.covers(pos) and not cut.covers(pos)
        probes.append(dict(name=name,xy=[x,y],cut=cut.covers(pos),modelObstacle=blocked,expected='building' if blocked or retained else None))
    neighbors={}
    for i in group['feature_local_ids']:
        if i!=OWNER:
            poly=site.footprints[i]
            assert poly.distance(cut)>1.0
            pos=poly.representative_point()
            neighbors[str(i)]=site.to_wgs(np.array([[pos.x,pos.y]]))[0].tolist()
    camera=read(PROJECT/'source/precise'/ID/'camera-preflight.json')
    _,bearing,pitch=camera['recommendation']
    record=dict(id=ID,owner=dict(macro_id=ref['frozen_macro'],feature_local_id=OWNER),
        source_feature_ids={'building':[ref['registration']['owner_key'].removeprefix('building:')],'building_part':[]},
        replacement_geometry=site.wgs(cut),collision_geometry=site.wgs(collision),source_section_caps=cap,
        lng=site.lon,lat=site.lat,heading=ref['author_frame']['runtime_heading_deg'],scale=1,altitude=0,bounds_glb=bounds,
        overview_focus_bounds_glb={'min':[-5.8,.10,-1.4],'max':[6.86,11.4,2.45]},
        model_geometry_sha256={k:r['sha256']for k,r in assets.items()},overviewBearing=bearing,overviewPitch=pitch,overviewZoom=20.5,
        maxDistance=500,lod_switch_in_m=505,lod_switch_out_m=650,
        navigation=dict(listed=False,status='可从庭院一侧查看入口拱廊与山墙。'),
        placement=dict(status='estimated',note='依有一号门牌的2013年照片及相机方向，估配到底图1353西北328.6度折边，保留其余旧屋体。沿墙的精确位置尚无测绘。'),
        partial_model=True,model_scope=read(args.manifest)['model_scope_zh'])
    checked_geometry(record['collision_geometry'],ID,collision=True)
    checked_geometry(record['replacement_geometry'],ID)
    write(args.out/'final-placement-contract.json',record)
    write(args.out/'placement-geometry.json',dict(id=ID,source_sha256=sha(PROJECT/'source/precise'/ID/'footprint-review.json'),
          manifest_sha256=sha(args.manifest),checker_sha256=sha(Path(__file__)),assets=assets,model_projection_m2=projection.area,
          cut_m2=cut.area,ground_mesh_projection_m2=ground.area,collision_m2=collision.area,variants=variants,
          cap_disagreement_m=seam_delta,cap_length_m=seams['far'].length,ground_probes=probes,neighbor_points_wgs84=neighbors))
    write(args.out/'map-case.json',dict(id=ID,previous='xuhui-guo-dihuo-west-house',neighbors=list(map(int,neighbors)),
        existingCandidateOwners=[],existingGroupOwners=[],addedTriangles=2,groupTriangles=2,sourceSectionCount=sum(len(line.coords)-1 for line in seams['far'].geoms),ground=probes,neighborGround=neighbors,
        front=dict(center=[1.14,-2.45],elevation=3.12,pitch=62,zoom=21.15,bearingOffset=4),
        roof=dict(center=[-.20,.45],elevation=8.7,pitch=44,zoom=20.92,bearingOffset=-10)))
    print(variants,seam_delta,flush=True)


if __name__=='__main__':
    main()
