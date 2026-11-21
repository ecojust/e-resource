"""Fit the photographed garden elevation to the two city meshes of Donghu House Seven."""
import argparse
import subprocess
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

ID='xuhui-donghu-hotel-house-seven'
OWNER=552


def separate_house(site,group):
    """The north corner is close to another house. Check every near vertex and centroid."""
    work=site.work
    ids=group['feature_local_ids']
    site.link('baseline-far.glb',site.files['far.glb'])
    site.link('baseline-near.glb.gz',site.files[Path(group['file']).name])
    site.link('macro-READY.json',site.files['READY.json'])
    write(work/'context-features.json',[{'localId':i} for i in ids])
    decoder=site.decoders/'map-decode-source.mjs'
    subprocess.run(['node',decoder],env=site.env,check=True,stdout=subprocess.DEVNULL)
    result={}
    for role in ('near','far'):
        tri=np.fromfile(work/f'baseline-{role}-triangles.f64',np.float64).reshape(-1,3,3)
        tri[:,:,:2]=tri[:,:,:2]@site.axes.T
        encoded=np.fromfile(work/f'baseline-{role}-owners.u32',np.uint32)
        if role=='far':
            assert set(encoded)==set(ids)
            own=encoded==OWNER
            evidence={'method':'per-vertex _FEATURE_ID_0'}
        else:
            assert set(encoded)=={0}
            target=ids.index(OWNER)
            checks=[]
            for weights in ([1/3]*3,[1,0,0],[0,1,0],[0,0,1]):
                points=geo.points(np.asarray(weights)@tri[:,:,:2])
                matrix=np.column_stack([geo.distance(points,site.footprints[i]) for i in ids])
                toward=matrix[:,target]
                nearest_other=np.delete(matrix,target,axis=1).min(axis=1)
                current=toward<nearest_other
                if checks:
                    assert np.array_equal(own,current)
                else:
                    assert set(np.asarray(ids)[matrix.argmin(axis=1)])==set(ids)
                    own=current
                error=toward[own].max()
                target_gap=(nearest_other-toward)[own].min()
                neighbor_gap=(toward-nearest_other)[~own].min()
                assert error<.11 and min(target_gap,neighbor_gap)>5*error
                checks.append(dict(weights=weights,max_target_error_m=error,
                                   min_target_lead_m=target_gap,min_neighbor_lead_m=neighbor_gap))
            evidence=dict(method='Every corner and centroid agrees on membership of the target house',
                          decoder_sha256=sha(decoder),group_faces=len(tri),target_faces=int(own.sum()),
                          membership_disagreements=0,samples=checks)
        result[role]=tri[own],tri[~own],evidence
    return result


def model_obstacles():
    # Horizontal circulation follows the door canopy and the five stair treads.
    # The glazed doors and inner wall close the passage beyond the steps.
    parts=[geo.box(-9.56,-.43,-5.30,-.08),geo.box(5.30,-.43,9.56,-.08),
           geo.box(-5.30,.48,5.30,.77),
           geo.box(-9.63,-.23,-9.39,7.47),geo.box(9.39,-.23,9.63,7.47),
           geo.box(-9.45,-3.64,-2.00,-3.48),geo.box(2.00,-3.64,9.45,-3.48),
           geo.box(-2.03,-3.49,2.03,-3.30)]
    for sign in (-1,1):
        x=sign*1.99
        parts.append(geo.box(x-.068,-4.985,x+.068,-4.835))
        x=sign*2.21
        parts.append(geo.box(x-.275,-5.67,x+.275,-5.09))
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
    cut=geo.box(-9.95,-5.98,9.95,7.77)
    assert cut.covers(projection.buffer(-.012)) or projection.difference(cut).area<.15
    collision=model_obstacles()
    assert cut.covers(collision)
    variants={}
    seams={}
    own_heights=[]
    for variant,(own,others,assignment) in separate_house(site,group).items():
        native=site.project_faces(own)
        front=native.intersection(cut)
        remainder=native.difference(cut)
        assert .18<front.area/native.area<.54 and native_poly.intersection(native).area/native.area>.85
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
    samples=[('lawn before steps',0,-6.12,False),('first stone tread',0,-5.78,False),
             ('fourth stone tread',.95,-4.64,False),('under door canopy',0,-4.88,False),
             ('glazed central door',0,-3.40,True),('inside glazed extension',.6,-2.52,False),
             ('inner door',0,.66,True),('upper loggia base',4.6,.63,True),
             ('eastern projecting wing',7.42,-.28,True),('western projecting wing',-7.42,-.28,True),
             ('eastside roof post',1.99,-4.91,True),('east planter',2.21,-5.36,True),
             ('closed west glass wall',-5.21,-3.56,True),('east garden glass',5.84,-3.58,True),
             ('east brick return',9.51,4.66,True),('passage between west planter and door',-1.6,-5.36,False),
             ('retained rear wing',1.2,13,False),('garden outside west end',-10.15,-3.87,False)]
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
        overview_focus_bounds_glb={'min':[-9.58,.12,-2.7],'max':[9.58,10.62,5.24]},
        model_geometry_sha256={k:r['sha256']for k,r in assets.items()},overviewBearing=bearing,overviewPitch=pitch,overviewZoom=20.5,
        maxDistance=500,lod_switch_in_m=505,lod_switch_out_m=650,
        navigation=dict(listed=False,status='可从东湖绿地一侧查看双柱、弧拱窗及玻璃廊。'),
        placement=dict(status='estimated',note='按1110号保护牌与OSM具名552楼体定位，取东南朝向的19.17米长边为基准。玻璃廊进深、沿边距离与正墙位置均据照片估配。'),
        partial_model=True,model_scope=read(args.manifest)['model_scope_zh'])
    checked_geometry(record['collision_geometry'],ID,collision=True)
    checked_geometry(record['replacement_geometry'],ID)
    write(args.out/'final-placement-contract.json',record)
    write(args.out/'placement-geometry.json',dict(id=ID,source_sha256=sha(PROJECT/'source/precise'/ID/'footprint-review.json'),
          manifest_sha256=sha(args.manifest),checker_sha256=sha(Path(__file__)),assets=assets,model_projection_m2=projection.area,
          cut_m2=cut.area,ground_mesh_projection_m2=ground.area,collision_m2=collision.area,variants=variants,
          cap_disagreement_m=seam_delta,cap_length_m=seams['far'].length,ground_probes=probes,neighbor_points_wgs84=neighbors))
    write(args.out/'map-case.json',dict(id=ID,previous='xuhui-zhu-mintang-residence',neighbors=list(map(int,neighbors)),
        existingCandidateOwners=[],existingGroupOwners=[],addedTriangles=2,groupTriangles=2,sourceSectionCount=sum(len(line.coords)-1 for line in seams['far'].geoms),ground=probes,neighborGround=neighbors,
        front=dict(center=[1.35,-.35],elevation=5.82,pitch=62,zoom=21.15,bearingOffset=4),
        roof=dict(center=[-.20,1.35],elevation=8.7,pitch=44,zoom=20.92,bearingOffset=-10)))
    print(variants,seam_delta,flush=True)


if __name__=='__main__':
    main()
