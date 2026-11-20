"""Retain both ends of the source row, the lane gate and the neighboring roofs at Lane 200."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
from shapely.geometry import box, Point, Polygon, LineString, MultiLineString
from shapely.ops import unary_union

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
MODEL = 'xuhui-yueyang-lane-200-east-row'
SOURCE = PROJECT / 'source/precise' / MODEL
OWNER = 4352
sys.path.insert(0, str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry


def verify(args, scratch):
    source=read(SOURCE/'footprint-review.json')
    params=read(SOURCE/'source/parameters.json')
    for row in source['frozen_bindings']:
        rel=row['repository_path'].split(source['frozen_macro']+'/')[1]
        f=args.macro/rel
        assert f.stat().st_size==row['bytes'] and sha(f)==row['sha256']
        (scratch/f.name).symlink_to(f.resolve())
    mesh=PlacementMeshes(PROJECT,scratch,source)
    assets,bounds,profile,ground=mesh.decode_model(args.manifest)
    low,high=-11.34,11.27
    cut=box(low,-2.02,high,16.70)
    window_row=Polygon([*params['front_xy_m'],*params['rear_xy_m']])
    assert 300<window_row.area<320 and window_row.difference(cut).area<.001
    assert ground.is_valid and ground.geom_type=='MultiPolygon'
    components=sorted(ground.geoms,key=lambda g:g.area,reverse=True)
    assert len(components)==2 and 306<components[0].area<312 and 3.0<components[1].area<7.5
    assert components[0].difference(cut).area<.001 and components[1].distance(components[0])>1.0
    evidence={};native={};group=mesh.decode_group(source['near_tiles'][0],OWNER)
    for name,(own,others,assignment)in group.items():
        orig=mesh.project_faces(own);neighbors=mesh.project_faces(others);res=orig.difference(cut)
        assert res.geom_type=='MultiPolygon'and len(res.geoms)==2 and all(k.area>2. for k in res.geoms)
        assert .10<res.area/orig.area<.36 and neighbors.intersection(cut).area<.001
        assert neighbors.intersection(ground).area<.001 and neighbors.distance(cut)>2.
        assert abs(own[:,:,2].max()-27.4)<.09 and components[1].distance(orig)>2.0
        native[name]=orig
        evidence[name]={'owner_triangles':len(own),'other_triangles':len(others),'source_height_m':float(own[:,:,2].max()),
                        'original_area_m2':orig.area,'retained_m2':res.area,'retained_fraction':res.area/orig.area,
                        'retained_ends_m2':sorted(k.area for k in res.geoms),'neighbor_clearance_m':neighbors.distance(cut),
                        'neighbor_collision_overlap_m2':neighbors.intersection(ground).area,'method':assignment}
    gaps={i:{'cut_clearance_m':g.distance(cut),'model_clearance_m':g.distance(ground)}
          for i,g in mesh.footprints.items() if i!=OWNER and g.distance(cut)<28}
    assert all(row['cut_clearance_m']>2 for row in gaps.values())
    assert {4575,1858,5547}.issubset(gaps) and gaps[4575]['model_clearance_m']>5
    caps=[];seams=[]
    for x in [low,high]:
        line=LineString([(x,-2.02),(x,16.70)])
        far=native['far'].intersection(line);near=native['near'].intersection(line)
        assert far.geom_type=='LineString'and near.geom_type in ('LineString','MultiLineString')
        assert far.hausdorff_distance(near)<.43 and 5.0<far.length<13.
        caps.append(far);seams.append({'x':x,'near_m':near.length,'far_m':far.length,'survey_difference_m':far.hausdorff_distance(near)})
    ready=read(args.macro/'READY.json')
    section={'geometry':mesh.wgs(MultiLineString(caps)),'height_reference':[ready['origin_longitude'],ready['origin_latitude']],
             'base_m':0,'roof_m':float(group['far'][0][:,:,2].max()),'far_sha256':ready['far']['sha256']}
    owner_area=mesh.footprints[OWNER]
    spots=[]
    def test(label,x,y,bld,clipped,original=None):
        q=Point(x,y)
        assert ground.covers(q)==bld and cut.covers(q)==clipped,(label,bld,clipped)
        if original is not None:assert mesh.footprints[original].covers(q)
        spots.append({'name':label,'xy':[x,y],'modelObstacle':bld,'cut':clipped,
                      'expected':'building'if bld or original is not None else None,
                      **({'ownerLocalId':original}if original is not None else {})})
    for i,(a,b)in enumerate(zip(params['front_xy_m'][::2],params['front_xy_m'][1::2])):
        u=(a[0]+b[0])/2;v=(a[1]+b[1])/2
        test('solid wall below window group '+str(i+1),u,v+.28,True,True)
    test('central occupied floor',0,6,True,True)
    test('open planted yard',0,-3.1,False,False)
    test('street side of the fence',0,-7.25,False,False)
    post=components[1].representative_point();test('observed garden fence',post.x,post.y,True,False)
    for i,poly in enumerate(native['far'].difference(cut).geoms):
        q=poly.intersection(owner_area).representative_point();test('retained original row end '+str(i+1),q.x,q.y,False,False,OWNER)
    for id in [4575,1858,5547]:
        q=mesh.footprints[id].representative_point();test('independent prior source '+str(id),q.x,q.y,False,False,id)
    m=read(args.manifest);fr=source['author_frame'];cam=read(SOURCE/'camera-preflight.json')
    contract={'id':MODEL,**fr['anchor'],'heading':fr['runtime_heading_deg'],'scale':1,'altitude':0,
              'owner':{'macro_id':source['frozen_macro'],'feature_local_id':OWNER},
              'source_feature_ids':{'building':[source['owner']['source_key'].split(':')[1]],'building_part':[]},
              'model_geometry_sha256':{k:r['sha256']for k,r in assets.items()},'bounds_glb':bounds,
              'replacement_geometry':mesh.wgs(cut),'collision_geometry':mesh.wgs(ground),'source_section_caps':section,
              'overviewBearing':cam['recommendation'][1],'overviewPitch':cam['recommendation'][2],
              'overviewZoom':19.5,'maxDistance':500,'lod_switch_in_m':550,'lod_switch_out_m':700,
              'navigation':{'listed':False,'status':'岳阳路一侧住宅外观，供俯瞰。'},
              'placement':{'status':'estimated','note':'2013、2020临街照与早期无遮挡屋照对位。4352仅代表本排局部，保留其南北两端、内侧住宅和门卫房。模型高度和截面按照片比例估算。'},
              'partial_model':True,'model_scope':m['model_scope_zh']}
    for key in ['replacement_geometry','collision_geometry']:checked_geometry(contract[key],key,collision=key=='collision_geometry')
    args.out.mkdir(exist_ok=True,parents=True);write(args.out/'final-placement-contract.json',contract)
    write(args.out/'footprint-review.json',{'model':MODEL,'assets':assets,'source_variants':evidence,'registered_source':source['owner'],
          'source_hashes':source['frozen_bindings'],'other_sources':gaps,'ground':spots,'seams':seams,'profile_m2':profile.area,
          'ground_m2':ground.area,'building_ground_m2':components[0].area,'fence_ground_m2':components[1].area,
          'scope':'The five-fold central row and its garden fence have separate collisions. The planted yard and public street remain open. The 27.4m height belongs to the older source mesh.'})
    print(evidence,{'ground':len(spots),'fence_m2':components[1].area,'all_m2':ground.area},flush=True)


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--macro',type=Path,required=True)
    cli.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/MODEL/'manifest.json')
    cli.add_argument('--out',type=Path,default=AUDIT)
    a=cli.parse_args()
    with tempfile.TemporaryDirectory()as d: verify(a,Path(d))
