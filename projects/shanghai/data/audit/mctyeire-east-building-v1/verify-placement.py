"""Measure the garden facade against the eastern hall and the separate north hall."""
import argparse,sys
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Point,LineString,MultiLineString,box
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
ID='changning-mctyeire-east-building'
OWNER=2885
OTHER=[733]

def run():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    parser.add_argument('--out',type=Path,default=HERE)
    a=parser.parse_args();a.out.mkdir(exist_ok=True,parents=True)
    fp=PROJECT/'source/precise'/ID/'footprint-review.json';record=read(fp);ctx=PlacementMeshes(PROJECT,a.work,record)
    # The complete group is shared by both independently named school buildings.
    from shapely.geometry import shape
    for row in record['owners']:
        if row['local_id'] not in ctx.footprints:
            ctx.footprints[row['local_id']] = shapely.transform(shape(row['geometry']),ctx.to_xy)
    assets,bounds,model,feet=ctx.decode_model(a.manifest)
    mask=shapely.union_all([box(-34.24,1.42,36.54,11.77),box(-10.48,-3.90,10.48,2.26)])
    assert model.difference(mask.buffer(.005)).area<.00001,(model.bounds,model.difference(mask).area)
    solids=[box(-10.16,.41,10.16,11.65),box(-3.73,-.36,3.73,.43)]
    for s in (-1,1):
        x=s*2.62
        for y in (-3.21,-.54):solids.append(box(x-.30,y-.30,x+.30,y+.30))
    for x0,x1,y in [(-34.2,-10.16,4.00),(10.16,36.49,3.76)]:
        w=x1-x0;front=y-1.83;spacing=w/6
        solids.append(box(x0,front+3.19,x1,11.65))
        for i in range(7):
            x=x0+i*spacing
            solids.append(box(max(x0,x-.30),front,min(x1,x+.30),front+.61))
    collision=shapely.union_all(solids,grid_size=.001)
    source=ctx.footprints[OWNER];grp=next(t for t in record['near_tiles'] if OWNER in t['feature_local_ids']);native={}
    for role,(n,peers,method)in ctx.decode_group(grp,OWNER).items():
        own=ctx.project_faces(n);other=ctx.project_faces(peers);ret=own.difference(mask)
        assert .60<ret.area/own.area<.88 and other.distance(mask)>7,(role,ret.area/own.area,other.distance(mask))
        native[role]={'triangles':len(n),'peer_triangles':len(peers),'assignment':method,'source_m2':own.area,'retained_m2':ret.area,'retained_fraction':ret.area/own.area,'peer_cut_m2':other.intersection(mask).area,'peer_model_distance_m':other.distance(model),'peer_cut_distance_m':other.distance(mask),'height_m':float(n[:,:,2].max())}
        if role=='far':far=own
    assert OTHER[0] in grp['feature_local_ids']
    neighbors={}
    for rid in OTHER:
        named=next(n['name'] for n in record['ownership'] if n['best']['id']==rid)
        nr=neighbors[rid]={'named':named,'source_distance_m':ctx.footprints[rid].distance(mask)}
        for role,(n,_,assign) in ctx.decode_group(grp,rid).items():
            other=ctx.project_faces(n)
            assert other.distance(mask)>7 and other.intersection(mask).is_empty,(role,rid,other.distance(mask))
            nr[role]={'triangles':len(n),'cut_overlap_m2':0,'distance_m':other.distance(mask),'assignment':assign}
    seams=[]
    for v,w in zip(mask.exterior.coords,list(mask.exterior.coords)[1:]):
        seams.extend(t for t in shapely.get_parts(far.intersection(LineString([v,w])))if isinstance(t,LineString)and t.length>.005)
    meta=read(ctx.files['READY.json']);caps=dict(base_m=0,roof_m=native['far']['height_m'],height_reference=[meta['origin_longitude'],meta['origin_latitude']],far_sha256=sha(ctx.files['far.glb']),geometry=ctx.wgs(MultiLineString(seams)))
    tests=[('court lawn',0,-8.5,False),('under the projecting porch',0,-2.30,False),('stone porch corner',2.62,-3.20,True),('recessed entrance',0,.75,True),('NW open arcade',-20.18,3.5,False),('SE open arcade',25.52,3.01,False),('NW stone pier',-22.18,2.4,True),('SE stone pier',23.32,2.2,True),('NW gallery rear rooms',-26.71,8.6,True),('rear rooms retained',1,17.65,True),('NW wing retained',-40.33,-5.33,True),('SE wing retained',44.15,-7.6,True)]
    for rid in OTHER:tests.append((neighbors[rid]['named'],*ctx.footprints[rid].representative_point().coords[0],True))
    result=[]
    for name,x,y,expected in tests:
        pt=Point(x,y);ownhit=collision.covers(pt);ret=source.difference(mask).covers(pt);others=[i for i,q in ctx.footprints.items()if i!=OWNER and q.covers(pt)]
        assert bool(ownhit or ret or others)==expected,(name,ownhit,ret,others)
        hit=dict(name=name,xy=[x,y],point=ctx.to_wgs(np.array([[x,y]]))[0].tolist(),expected='building'if expected else None,modelObstacle=ownhit,cut=mask.covers(pt),retained=ret)
        if others:hit['ownerLocalId']=others[0]
        result.append(hit)
    f=record['author_frame'];c=dict(id=ID,**f['anchor'],heading=f['runtime_heading_deg'],scale=1,altitude=0,owner=dict(macro_id=record['frozen_macro'],feature_local_id=OWNER),source_feature_ids=dict(building=[record['owner']['source_key'].removeprefix('building:')],building_part=[]),bounds_glb=bounds,model_geometry_sha256={k:v['sha256']for k,v in assets.items()},replacement_geometry=ctx.wgs(mask),collision_geometry=ctx.wgs(collision),source_section_caps=caps,overviewBearing=53,overviewPitch=49,overviewZoom=19.5,maxDistance=580,lod_switch_in_m=540,lod_switch_out_m=700,navigation={'listed':False,'status':'庭院正面开放观察，侧翼及室内未重建。'},placement={'status':'estimated','note':'东楼位于草坪东侧。中央突出段的宽度来自同名地块，西南院面高程、廊深与屋顶轮廓参照2017年影像估算。'},partial_model=True,model_scope=read(a.manifest)['model_scope_zh'])
    for key in ('replacement_geometry','collision_geometry'):checked_geometry(c[key],key,collision=key=='collision_geometry')
    write(a.out/'final-placement-contract.json',c);write(a.out/'placement-geometry.json',dict(id=ID,source_sha256=sha(fp),script_sha256=sha(Path(__file__)),manifest_sha256=sha(a.manifest),assets=assets,native=native,neighboring_campus_buildings=neighbors,model_m2=model.area,ground_projection_m2=feet.area,collision_m2=collision.area,retained_m2=source.difference(mask).area,ground_probes=result,section_lengths_m=[l.length for l in seams],contract_sha256=sha(a.out/'final-placement-contract.json')))
    print(native)
if __name__=='__main__':run()
