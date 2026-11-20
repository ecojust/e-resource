"""Check the 1936 field front, the retained library and the separately listed museum."""
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
ID='huangpu-aurora-university-library'
OWNER=1079
OTHER=[1536,1360]

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
    # The shallow cornice projects past the two end bays and the split front wall.
    # All thirteen ground-floor openings have a continuous masonry plinth below.
    mask=box(-29.95,-.37,29.95,4.7)
    assert mask.covers(model), (model.bounds,model.difference(mask).area)
    sections=[(-29.849,-21.70,0),(-21.70,-2.62,.40),(-2.62,2.62,.16),
              (2.62,21.70,.40),(21.70,29.849,0)]
    collision=shapely.union_all([box(x0,y-.005,x1,4.62)for x0,x1,y in sections],grid_size=.001)
    source=ctx.footprints[OWNER];grp=next(t for t in record['near_tiles'] if OWNER in t['feature_local_ids']);native={}
    for role,(n,peers,method)in ctx.decode_group(grp,OWNER).items():
        own=ctx.project_faces(n);other=ctx.project_faces(peers);ret=own.difference(mask)
        assert .60<ret.area/own.area<.88 and other.distance(mask)>5,(role,ret.area/own.area,other.distance(mask))
        native[role]={'triangles':len(n),'peer_triangles':len(peers),'assignment':method,'source_m2':own.area,'retained_m2':ret.area,'retained_fraction':ret.area/own.area,'peer_cut_m2':other.intersection(mask).area,'peer_model_distance_m':other.distance(model),'peer_cut_distance_m':other.distance(mask),'height_m':float(n[:,:,2].max())}
        if role=='far':far=own
    neighbors={}
    for rid in OTHER:
        named={1536:'较高的相邻校舍',1360:'重庆南路225号原震旦博物馆'}[rid]
        group=next(t for t in record['near_tiles'] if rid in t['feature_local_ids'])
        nr=neighbors[rid]={'named':named,'source_distance_m':ctx.footprints[rid].distance(mask)}
        for role,(n,_,assign) in ctx.decode_group(group,rid).items():
            other=ctx.project_faces(n)
            assert other.distance(mask)>5 and other.intersection(mask).is_empty,(role,rid,other.distance(mask))
            nr[role]={'triangles':len(n),'cut_overlap_m2':0,'distance_m':other.distance(mask),'assignment':assign}
    seams=[]
    for v,w in zip(mask.exterior.coords,list(mask.exterior.coords)[1:]):
        seams.extend(t for t in shapely.get_parts(far.intersection(LineString([v,w])))if isinstance(t,LineString)and t.length>.005)
    meta=read(ctx.files['READY.json']);caps=dict(base_m=0,roof_m=native['far']['height_m'],height_reference=[meta['origin_longitude'],meta['origin_latitude']],far_sha256=sha(ctx.files['far.glb']),geometry=ctx.wgs(MultiLineString(seams)))
    tests=[('playing field',0,-7,False),('outside east end',-26,-.18,False),
           ('east end at plinth',-26,.12,True),('east wall setback',-12,.22,False),
           ('east wing at plinth',-12,.50,True),('central window exterior',0,-.08,False),
           ('central plinth',0,.25,True),('west wing exterior',12,.18,False),
           ('west wing at plinth',12,.52,True),('outside west end',26,-.14,False),
           ('west end at grade',26,.26,True),('retained library',0,8,True),('retained west return',25,16,True)]
    for rid in OTHER:tests.append((neighbors[rid]['named'],*ctx.footprints[rid].representative_point().coords[0],True))
    result=[]
    for name,x,y,expected in tests:
        pt=Point(x,y);ownhit=collision.covers(pt);ret=source.difference(mask).covers(pt);others=[i for i,q in ctx.footprints.items()if i!=OWNER and q.covers(pt)]
        assert bool(ownhit or ret or others)==expected,(name,ownhit,ret,others)
        hit=dict(name=name,xy=[x,y],point=ctx.to_wgs(np.array([[x,y]]))[0].tolist(),expected='building'if expected else None,modelObstacle=ownhit,cut=mask.covers(pt),retained=ret)
        if others:hit['ownerLocalId']=others[0]
        result.append(hit)
    f=record['author_frame'];c=dict(id=ID,**f['anchor'],heading=f['runtime_heading_deg'],scale=1,altitude=0,owner=dict(macro_id=record['frozen_macro'],feature_local_id=OWNER),source_feature_ids=dict(building=[record['owner']['source_key'].removeprefix('building:')],building_part=[]),bounds_glb=bounds,model_geometry_sha256={k:v['sha256']for k,v in assets.items()},replacement_geometry=ctx.wgs(mask),collision_geometry=ctx.wgs(collision),source_section_caps=caps,overviewBearing=160,overviewPitch=48,overviewZoom=19.5,maxDistance=580,lod_switch_in_m=540,lod_switch_out_m=700,navigation={'listed':False,'status':'模型展示球场一侧外墙；图书馆室内未重建。'},placement={'status':'estimated','note':'球场侧宽度取自北侧地块边线，两张2020年影像用于估算窗头间距与女儿墙高度。后部为保留的城市底图。'},partial_model=True,model_scope=read(a.manifest)['model_scope_zh'])
    for key in ('replacement_geometry','collision_geometry'):checked_geometry(c[key],key,collision=key=='collision_geometry')
    write(a.out/'final-placement-contract.json',c);write(a.out/'placement-geometry.json',dict(id=ID,source_sha256=sha(fp),script_sha256=sha(Path(__file__)),manifest_sha256=sha(a.manifest),assets=assets,native=native,neighboring_campus_buildings=neighbors,model_m2=model.area,ground_projection_m2=feet.area,collision_m2=collision.area,retained_m2=source.difference(mask).area,ground_probes=result,section_lengths_m=[l.length for l in seams],contract_sha256=sha(a.out/'final-placement-contract.json')))
    print(native)
if __name__=='__main__':run()
