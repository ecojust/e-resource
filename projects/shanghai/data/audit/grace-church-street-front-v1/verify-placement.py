"""Verify the east street end of Grace Church against both separate Song garden residences."""
import argparse,sys,subprocess
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Point,LineString,MultiLineString,box
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
ID='jingan-grace-church-street-front'
OWNER=519
OTHER=[1770,557]

def read_group(ctx, group, source_id):
    """Resolve near triangles independently by exclusive membership in a 15 cm source envelope."""
    ids=group['feature_local_ids'];ctx.link('baseline-far.glb',ctx.files['far.glb'])
    ctx.link('baseline-near.glb.gz',ctx.files[Path(group['file']).name])
    ctx.link('macro-READY.json',ctx.files['READY.json'])
    write(ctx.work/'context-features.json',[{'localId':i}for i in ids])
    subprocess.run(['node',ctx.decoders/'map-decode-source.mjs'],env=ctx.env,check=True,stdout=subprocess.DEVNULL)
    result={}
    for role in ('near','far'):
        tri=np.fromfile(ctx.work/f'baseline-{role}-triangles.f64',np.float64).reshape(-1,3,3)
        tri[:,:,:2]=tri[:,:,:2] @ ctx.axes.T
        if role=='far':
            owners=np.fromfile(ctx.work/'baseline-far-owners.u32',np.uint32)
            mine=owners==source_id;other=~mine;method={'basis':'Per-vertex _FEATURE_ID_0.'}
        else:
            points=shapely.points(tri.mean(axis=1)[:,:2]);dist=np.stack([shapely.distance(points,ctx.footprints[i])for i in ids],axis=1)
            possible=dist<.15;column=ids.index(source_id);mine=possible[:,column]
            assert mine.any() and np.all(possible.sum(axis=1)>=1), 'A source triangle lacks a footprint assignment'
            peers=np.delete(possible,column,axis=1);assert not np.any(peers[mine]), 'Ambiguous ownership on checked building'
            other=peers.any(axis=1);assert np.all(mine | other) and not np.any(mine & other)
            farthest=float(dist[mine,column].max());nearest_peer=float(np.delete(dist[mine],column,axis=1).min())
            # Verify all three vertices, including overhanging cornices, against the same footprint.
            corners=shapely.points(tri[mine,:,:2].reshape(-1,2));radius=float(shapely.distance(corners,ctx.footprints[source_id]).max())
            assert radius<.22 and nearest_peer>.50,(radius,nearest_peer)
            method={'basis':'Exactly one possible footprint for every checked centroid, within 0.15 m of the source building.','max_own_centroid_m':farthest,'min_other_centroid_m':nearest_peer,'max_own_vertex_m':radius,'ambiguous_checked_triangles':0}
        result[role]=(tri[mine],tri[other],method)
    return result

def run():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    parser.add_argument('--out',type=Path,default=HERE)
    a=parser.parse_args();a.out.mkdir(exist_ok=True,parents=True)
    fp=PROJECT/'source/precise'/ID/'footprint-review.json';record=read(fp);ctx=PlacementMeshes(PROJECT,a.work,record)
    # Import every owner appearing in any of the three immutable source groups.
    from shapely.geometry import shape
    for row in record['owners']:
        if row['local_id'] not in ctx.footprints:
            ctx.footprints[row['local_id']] = shapely.transform(shape(row['geometry']),ctx.to_xy)
    assets,bounds,model,feet=ctx.decode_model(a.manifest)
    # The photographed double entrance is recessed behind the three-window lobby.
    # The remainder of the worship hall is retained by the map.
    mask=box(-6.25,-.41,6.25,4.32)
    assert mask.covers(model),(model.bounds,model.difference(mask).area)
    rear=box(-6.118,.70,6.118,4.23)
    vestibule=box(-2,-.05,3.55,.72)
    occupied=shapely.union_all([rear,vestibule,box(-4.72,.36,-1.68,3.40)])
    for x in (-.825,.775):occupied=occupied.difference(box(x-.435,-.12,x+.435,.529))
    collision=occupied
    source=ctx.footprints[OWNER];grp=next(t for t in record['near_tiles'] if OWNER in t['feature_local_ids']);native={}
    for role,(n,peers,method)in read_group(ctx,grp,OWNER).items():
        own=ctx.project_faces(n);other=ctx.project_faces(peers);ret=own.difference(mask)
        assert .82<ret.area/own.area<.91 and other.distance(mask)>2.0,(role,ret.area/own.area,other.distance(mask))
        native[role]={'triangles':len(n),'peer_triangles':len(peers),'assignment':method,'source_m2':own.area,'retained_m2':ret.area,'retained_fraction':ret.area/own.area,'peer_cut_m2':other.intersection(mask).area,'peer_model_distance_m':other.distance(model),'peer_cut_distance_m':other.distance(mask),'height_m':float(n[:,:,2].max())}
        if role=='far':far=own
    neighbors={}
    for rid in OTHER:
        named={1770:'宋氏花园住宅北幢',557:'宋氏花园住宅另一幢'}[rid]
        group=next(t for t in record['near_tiles'] if rid in t['feature_local_ids'])
        nr=neighbors[rid]={'named':named,'source_distance_m':ctx.footprints[rid].distance(mask)}
        for role,(n,_,assign) in read_group(ctx,group,rid).items():
            other=ctx.project_faces(n)
            assert other.distance(mask)>2.0 and other.intersection(mask).is_empty,(role,rid,other.distance(mask))
            nr[role]={'triangles':len(n),'cut_overlap_m2':0,'distance_m':other.distance(mask),'assignment':assign}
    seams=[]
    for v,w in zip(mask.exterior.coords,list(mask.exterior.coords)[1:]):
        seams.extend(t for t in shapely.get_parts(far.intersection(LineString([v,w])))if isinstance(t,LineString)and t.length>.005)
    meta=read(ctx.files['READY.json']);caps=dict(base_m=0,roof_m=native['far']['height_m'],height_reference=[meta['origin_longitude'],meta['origin_latitude']],far_sha256=sha(ctx.files['far.glb']),geometry=ctx.wgs(MultiLineString(seams)))
    tests=[('Shaanxi Road forecourt',1,-2,False),('south outer setback',-5.61,.45,False),
           ('south shoulder',-5.61,.96,True),('below southeast brick tower',-3.25,.49,True),
           ('outside tower front',-3.25,.15,False),('left door recess',-.825,.30,False),
           ('left door leaf',-.825,.57,True),('right door recess',.775,.35,False),
           ('right door leaf',.775,.57,True),('doorway mullion',0,.18,True),
           ('northern shoulder setback',4.72,.31,False),('northern shoulder',4.72,.99,True),
           ('retained worship hall',0,14.6,True)]
    for rid in OTHER:tests.append((neighbors[rid]['named'],*ctx.footprints[rid].representative_point().coords[0],True))
    result=[]
    for name,x,y,expected in tests:
        pt=Point(x,y);ownhit=collision.covers(pt);ret=source.difference(mask).covers(pt);others=[i for i,q in ctx.footprints.items()if i!=OWNER and q.covers(pt)]
        assert bool(ownhit or ret or others)==expected,(name,ownhit,ret,others)
        hit=dict(name=name,xy=[x,y],point=ctx.to_wgs(np.array([[x,y]]))[0].tolist(),expected='building'if expected else None,modelObstacle=ownhit,cut=mask.covers(pt),retained=ret)
        if others:hit['ownerLocalId']=others[0]
        result.append(hit)
    f=record['author_frame'];c=dict(id=ID,**f['anchor'],heading=f['runtime_heading_deg'],scale=1,altitude=0,owner=dict(macro_id=record['frozen_macro'],feature_local_id=OWNER),source_feature_ids=dict(building=[record['owner']['source_key'].removeprefix('building:')],building_part=[]),bounds_glb=bounds,model_geometry_sha256={k:v['sha256']for k,v in assets.items()},replacement_geometry=ctx.wgs(mask),collision_geometry=ctx.wgs(collision),source_section_caps=caps,overviewBearing=-101,overviewPitch=40,overviewZoom=19.5,maxDistance=580,lod_switch_in_m=540,lod_switch_out_m=700,navigation={'listed':False,'status':'模型展示陕西北路堂面及两扇可辨门扇；堂内未重建。'},placement={'status':'estimated','note':'沿陕西北路短边约12.24米估算街面尺度，钟塔高度、门窗与肩墙取自2006、2013及2026年照片。其余保留原城市体块。'},partial_model=True,model_scope=read(a.manifest)['model_scope_zh'])
    for key in ('replacement_geometry','collision_geometry'):checked_geometry(c[key],key,collision=key=='collision_geometry')
    write(a.out/'final-placement-contract.json',c);write(a.out/'placement-geometry.json',dict(id=ID,source_sha256=sha(fp),script_sha256=sha(Path(__file__)),manifest_sha256=sha(a.manifest),assets=assets,native=native,neighboring_campus_buildings=neighbors,model_m2=model.area,ground_projection_m2=feet.area,collision_m2=collision.area,retained_m2=source.difference(mask).area,ground_probes=result,section_lengths_m=[l.length for l in seams],contract_sha256=sha(a.out/'final-placement-contract.json')))
    print(native)
if __name__=='__main__':run()
