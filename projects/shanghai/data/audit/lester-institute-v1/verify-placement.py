"""Verify the directed main building envelope, actual source owner, and passable seven-arch porch."""
import argparse
import json
from pathlib import Path
import sys
import tempfile

import numpy as np
import shapely as geo
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import polygonize

AUDIT=Path(__file__).resolve().parent
PROJECT=AUDIT.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,sha,write

IDENT='hongkou-lester-institute'
SOURCE=PROJECT/'source/precise'/IDENT
OWNER=1131


def masonry_at_pedestrian_height(triangles):
    height=1.05
    xy=triangles[:,:,:2]
    in_zone=(xy[:,:,1].min(1)<-8.34)&(xy[:,:,1].max(1)>-13.0)
    in_zone&=(xy[:,:,0].min(1)<16.25)&(xy[:,:,0].max(1)>-16.25)
    z=triangles[:,:,2]
    crossing=triangles[in_zone&(z.min(1)<height)&(z.max(1)>height)]
    segments=[]
    for t in crossing:
        hits=[]
        for a,b in zip(t,np.roll(t,-1,axis=0)):
            if (a[2]-height)*(b[2]-height)<0:
                hits.append((a[:2]+(b[:2]-a[:2])*(height-a[2])/(b[2]-a[2])).round(4))
        if len(hits)==2 and np.linalg.norm(hits[1]-hits[0])>.0002:
            segments.append(LineString(hits))
    section=geo.union_all(list(polygonize(geo.union_all(segments,grid_size=.001))))
    return section.intersection(box(-16.25,-13,16.25,-8.34))


def verify_walk(collision,points):
    mid=(points[0][0]+points[1][0])/2
    spacing=(points[1][0]-points[0][0])/7.15
    result=[]
    for i in range(7):
        x=mid+(i-3)*spacing
        for y in [-12.04,-11.10,-9.72]:
            result.append({'witness':'open arcade '+str(i+1),'local_xy_m':[x,y],'expected':False})
    for i in range(6):
        x=mid+(i-2.5)*spacing
        result.append({'witness':'stone pier '+str(i+1),'local_xy_m':[x,-12.06],'expected':True})
    for name,x,y,present in [('garden',0,-18,False),('center behind doors',0,-7.62,True),('door threshold',0,-8.37,True),
            ('west workshop',-31,-5,True),('east workshop',29,-2,True),('rear hall',1,25,True)]:
        result.append({'witness':name,'local_xy_m':[x,y],'expected':present})
    for v in result:
        v['found']=bool(collision.covers(Point(v['local_xy_m'])))
        assert v['found']==v['expected'],v
    return result


def run(args,work):
    src=read(SOURCE/'footprint-review.json')
    params=read(SOURCE/'source/parameters.json')
    group=src['near_tiles'][0]
    for r in src['frozen_bindings']:
        rel=r['repository_path'].split(src['frozen_macro']+'/')[1]
        source=(args.macro/rel).resolve();assert sha(source)==r['sha256'] and source.stat().st_size==r['bytes']
        (work/Path(rel).name).symlink_to(source)
    mesh=PlacementMeshes(PROJECT,work,src)
    assets,bounds,model,ground=mesh.decode_model(args.manifest)
    local_owner=mesh.footprints[OWNER]
    assert model.difference(local_owner).area<.08
    porch=Polygon(params['plans_m']['porch'])
    from_variants={}
    for result in read(work/'delivered-decode.json'):
        tri=np.fromfile(result['triangle_file'],np.float64).reshape(-1,3,3)
        local=tri[:,:,[0,2,1]]*[1,-1,1]
        section=masonry_at_pedestrian_height(local)
        assert not section.is_empty and section.area>1
        from_variants[result['variant']]=section
    piers=from_variants['raw']
    assert max(g.symmetric_difference(piers).area for g in from_variants.values())<.10
    structural_base=ground.difference(porch.buffer(.02,join_style='mitre')).union(ground.intersection(Polygon(params['plans_m']['center'])))
    collision=geo.union_all([structural_base,piers],grid_size=.001)
    collision=collision.buffer(.001,join_style='mitre').simplify(.012,preserve_topology=True)
    probes=verify_walk(collision,params['plans_m']['porch'])
    tiles=mesh.decode_group(group,OWNER)
    geometry={}
    for kind,(own,others,info) in tiles.items():
        geo_own=mesh.project_faces(own)
        other=mesh.project_faces(others)
        geometry[kind]=(geo_own,other,{'source_triangles':len(own),'other_triangles':len(others),
                         'source_height_m':float(own[:,:,2].max()),'assignment':info})
    # A tight source-scoped mask replaces the single named but oversized generic hull.
    # A building-wide rectangle could reach the north annexes, especially on the eastern side.
    visual=local_owner.buffer(.16,join_style='mitre')
    for expected,_,_ in geometry.values():
        assert expected.difference(visual).area<.10,expected.difference(visual).area
    assert len(visual.exterior.coords)<=65
    clearances={}
    for local_id in [749,115,1577,1068,209,460]:
        adj=mesh.footprints[local_id]
        clearances[local_id]={'clip_overlap_m2':visual.intersection(adj).area,
            'mesh_overlap_m2':model.intersection(adj).area,'clip_clearance_m':visual.distance(adj),
            'collision_clearance_m':collision.distance(adj)}
        assert visual.intersection(adj).area<.0001,clearances[local_id]
    outcomes={}
    for kind,(g,n,record) in geometry.items():
        outcomes[kind]={**record,'source_horizontal_projection_m2':g.area,'source_mask_miss_m2':g.difference(visual).area,
                        'same_group_other_clip_m2':n.intersection(visual).area,'same_group_clearance_m':n.distance(visual)}
        assert n.intersection(visual).area<.0001
    owned={**src['owner'],'local_id':OWNER,'key':src['owner']['source_key']}
    camera_trial=read(SOURCE/'garden-camera-preflight.json')['recommended_trial']
    contract={'id':IDENT,'lng':mesh.lon,'lat':mesh.lat,'heading':params['author_frame']['runtime_heading_deg'],
              'scale':1,'altitude':0,'owner':{'macro_id':src['frozen_macro'],'feature_local_id':OWNER},
              'source_feature_ids':{'building':[owned['key'].split(':')[-1]],'building_part':[]},
              'model_geometry_sha256':{v:r['sha256']for v,r in assets.items()},'bounds_glb':bounds,
              'replacement_geometry':mesh.wgs(visual),'collision_geometry':mesh.wgs(collision),
              'overviewBearing':camera_trial[1],'overviewPitch':camera_trial[2],'overviewZoom':18.8,'maxDistance':510,
              'lod_switch_in_m':540,'lod_switch_out_m':700,
              'navigation':{'listed':False,'status':'东长治路505号工学院主楼、园侧尖券和中央穹顶的俯瞰。'},
              'placement':{'status':'estimated','note':'当前研究院具名多边形与1934平面、修缮正面及屋面对应。仅消除1131的粗略单栋；北侧楼、园侧匿名地块与道路源完整。七孔门廊保留通行，背部和屋顶标高含推定。'},
              'partial_model':False,'model_scope':'东长治路505号雷氏德工学院主楼的双折翼、七尖券、钢窗、中央塔穹及东北锯齿屋面。背面、局部标高和转角按图估计。'}
    report={'id':IDENT,'assets':assets,'bounds_glb':bounds,'source_id':OWNER,'source_bindings':src['frozen_bindings'],
            'source_footprint_m2':local_owner.area,'model_projection_m2':model.area,'actual_ground_projection_m2':ground.area,
            'structural_walking_collision_m2':collision.area,'removed_walkable_porch_paving_m2':ground.difference(collision).area,
            'structural_piers_cross_section_m2':piers.area,'horizontal_cut_elevation_m':1.05,
            'model_area_outside_named_owner_m2':model.difference(local_owner).area,'clip_m2':visual.area,'clip_triangle_count':len(visual.exterior.coords)-3,
            'neighbours':clearances,'source_variants':outcomes,'walking_witnesses':probes,'proposed_placement_contract':contract}
    args.out.mkdir(exist_ok=True,parents=True)
    write(args.out/'footprint-review.json',report)
    write(args.out/'final-placement-contract.json',contract)
    print(assets,report['clip_triangle_count'],len(probes),collision.area,clearances)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/IDENT/'manifest.json')
    parser.add_argument('--macro',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=AUDIT)
    options=parser.parse_args()
    with tempfile.TemporaryDirectory() as scratch:run(options,Path(scratch))
