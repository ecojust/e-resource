"""Measure the delivered south veranda against the Hogg House core and the four separately named buildings."""
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
ID='changning-st-johns-administration-building'
OWNER=320
OTHER=[2173,400,1435,2404]

def run():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    parser.add_argument('--out',type=Path,default=HERE)
    a=parser.parse_args();a.out.mkdir(exist_ok=True,parents=True)
    fp=PROJECT/'source/precise'/ID/'footprint-review.json';record=read(fp);ctx=PlacementMeshes(PROJECT,a.work,record)
    # The campus is long, so the western near group also contains coarse owners
    # beyond the standard 0.003-degree neighbourhood used by PlacementMeshes.
    from shapely.geometry import shape
    for row in record['owners']:
        if row['local_id'] not in ctx.footprints:
            ctx.footprints[row['local_id']] = shapely.transform(shape(row['geometry']),ctx.to_xy)
    assets,bounds,model,feet=ctx.decode_model(a.manifest)
    mask=shapely.union_all([box(-14.30,-1.12,14.30,10.22),box(5.98,-6.08,12.28,-.73)])
    assert model.difference(mask.buffer(.005)).area<.00001,(model.bounds,model.difference(mask).area)
    # The sheltered carriage drive, its entrance and the three-metre gallery under the upper sash are open.
    solids=[box(-13.29,3.00,13.29,9.8),box(-13.25,.025,-12.97,3.02),box(12.97,.025,13.25,3.02)]
    for x in np.arange(-13.05,13.20,3.27):solids.append(box(x-.17,-.05,x+.17,.29))
    for x in (6.58,11.66):
        for y in (-5.3,-.08):solids.append(box(x-.205,y-.205,x+.205,y+.205))
        solids.append(box(x-.074,-5.36,x+.074,-4.04))
    collision=shapely.union_all(solids,grid_size=.001)
    source=ctx.footprints[OWNER];grp=next(t for t in record['near_tiles'] if OWNER in t['feature_local_ids']);native={}
    for role,(n,peers,method)in ctx.decode_group(grp,OWNER).items():
        own=ctx.project_faces(n);other=ctx.project_faces(peers);ret=own.difference(mask)
        assert .25<ret.area/own.area<.46 and other.distance(mask)>7,(role,ret.area/own.area,other.distance(mask))
        native[role]={'triangles':len(n),'peer_triangles':len(peers),'assignment':method,'source_m2':own.area,'retained_m2':ret.area,'retained_fraction':ret.area/own.area,'peer_cut_m2':other.intersection(mask).area,'peer_model_distance_m':other.distance(model),'peer_cut_distance_m':other.distance(mask),'height_m':float(n[:,:,2].max())}
        if role=='far':far=own
    # Use the campus table for every separate registered property. The two streamed groups around the lawn
    # are also tested against the detailed mesh of a selected owner in each group.
    neighbors={rid:{'named':next(n['tags']['name']for n in record['ownership']if n['frozen']['id']==rid),'source_distance_m':ctx.footprints[rid].distance(mask)} for rid in OTHER}
    for t in record['near_tiles']:
        if OWNER in t['feature_local_ids']:continue
        anchor=next(i for i in t['feature_local_ids']if i in OTHER)
        for role,(n,peers,method)in ctx.decode_group(t,anchor).items():
            whole=ctx.project_faces(np.concatenate([n,peers]))
            assert whole.distance(mask)>4,(t['id'],whole.distance(mask))
            neighbors[anchor][role+'_group']={'id':t['id'],'includes':t['feature_local_ids'],'triangles':len(n)+len(peers),'min_distance_to_cut_m':whole.distance(mask),'cut_m2':whole.intersection(mask).area}
    seams=[]
    for v,w in zip(mask.exterior.coords,list(mask.exterior.coords)[1:]):
        seams.extend(t for t in shapely.get_parts(far.intersection(LineString([v,w])))if isinstance(t,LineString)and t.length>.005)
    meta=read(ctx.files['READY.json']);caps=dict(base_m=0,roof_m=native['far']['height_m'],height_reference=[meta['origin_longitude'],meta['origin_latitude']],far_sha256=sha(ctx.files['far.glb']),geometry=ctx.wgs(MultiLineString(seams)))
    tests=[('south courtyard',0,-2,False),('carriage approach',9.12,-6.36,False),('open carriage drive',9.12,-3.14,False),('carriage front post',6.58,-5.3,True),('short carriage guard',11.66,-4.70,True),('south veranda sheltered passage',-4.09,1.51,False),('red frontage post',-6.51,.12,True),('back entrance wall',-3.91,3.11,True),('south room',2.1,6.35,True),('north rooms retained',-1.0,12.82,True),('east exterior',15.10,4.50,False)]
    for rid in OTHER:tests.append((neighbors[rid]['named'],*ctx.footprints[rid].representative_point().coords[0],True))
    result=[]
    for name,x,y,expected in tests:
        pt=Point(x,y);ownhit=collision.covers(pt);ret=source.difference(mask).covers(pt);others=[i for i,q in ctx.footprints.items()if i!=OWNER and q.covers(pt)]
        assert bool(ownhit or ret or others)==expected,(name,ownhit,ret,others)
        hit=dict(name=name,xy=[x,y],point=ctx.to_wgs(np.array([[x,y]]))[0].tolist(),expected='building'if expected else None,modelObstacle=ownhit,cut=mask.covers(pt),retained=ret)
        if others:hit['ownerLocalId']=others[0]
        result.append(hit)
    f=record['author_frame'];c=dict(id=ID,**f['anchor'],heading=f['runtime_heading_deg'],scale=1,altitude=0,owner=dict(macro_id=record['frozen_macro'],feature_local_id=OWNER),source_feature_ids=dict(building=[record['owner']['source_key'].removeprefix('building:')],building_part=[]),bounds_glb=bounds,model_geometry_sha256={k:v['sha256']for k,v in assets.items()},replacement_geometry=ctx.wgs(mask),collision_geometry=ctx.wgs(collision),source_section_caps=caps,overviewBearing=-17,overviewPitch=46,overviewZoom=19.5,maxDistance=580,lod_switch_in_m=540,lod_switch_out_m=700,navigation={'listed':False,'status':'南廊与望楼可俯瞰，室内另列。'},placement={'status':'estimated','note':'四号楼位于大草坪南侧，南廊进深3米有校档支撑；望楼与乘车门斗相对主体的距离依影像估算。'},partial_model=True,model_scope=read(a.manifest)['model_scope_zh'])
    for key in ('replacement_geometry','collision_geometry'):checked_geometry(c[key],key,collision=key=='collision_geometry')
    write(a.out/'final-placement-contract.json',c);write(a.out/'placement-geometry.json',dict(id=ID,source_sha256=sha(fp),script_sha256=sha(Path(__file__)),manifest_sha256=sha(a.manifest),assets=assets,native=native,neighboring_campus_buildings=neighbors,model_m2=model.area,ground_projection_m2=feet.area,collision_m2=collision.area,retained_m2=source.difference(mask).area,ground_probes=result,section_lengths_m=[l.length for l in seams],contract_sha256=sha(a.out/'final-placement-contract.json')))
    print(native)
if __name__=='__main__':run()
