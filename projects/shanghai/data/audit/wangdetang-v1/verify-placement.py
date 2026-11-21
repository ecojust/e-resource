"""Measure the limited garden-facing cut and adjacent retained houses at 2 Beijing West Road Lane 1220."""
import argparse
from pathlib import Path
import sys
import numpy as np
import shapely
from shapely.affinity import scale
from shapely.geometry import LineString,MultiLineString,Point,box,shape

AUDIT=Path(__file__).resolve().parent
PROJECT=AUDIT.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
ID='jingan-wangdetang-augustinian-office'
OWNER=786
NEIGHBORS=(773,404)

def verify():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    parser.add_argument('--out',type=Path,default=AUDIT)
    args=parser.parse_args();args.out.mkdir(exist_ok=True,parents=True)
    source=PROJECT/'source/precise'/ID/'footprint-review.json';review=read(source)
    ctx=PlacementMeshes(PROJECT,args.work,review)
    for rec in review['owners']:
        if rec['local_id'] not in ctx.footprints:ctx.footprints[rec['local_id']]=shapely.transform(shape(rec['geometry']),ctx.to_xy)
    assets,bounds,outline,feet=ctx.decode_model(args.manifest)
    sx,sy=12.5463/20.768,.90
    calibrated=lambda g:scale(g,xfact=sx,yfact=sy,origin=(0,0))
    # Cover the photographed western section and the southern roof eave.
    mask=calibrated(shapely.union_all([box(-10.66,-1.92,11.49,5.80),box(8.03,5.78,11.49,14.20)])).simplify(.004)
    assert mask.buffer(.002).covers(outline),(outline.bounds,outline.difference(mask).area)
    occupied=shapely.union_all([box(-10.38,.005,10.38,4.731),box(8.985,4.70,10.38,14.06)])
    # Individual treads and handrails allow a normal approach to the landing.
    # The rear door threshold and the rendered stone jambs remain solid.
    occupied=occupied.difference(box(-1.433,-.12,1.433,1.535))
    occupied=calibrated(occupied)
    group=next(g for g in review['near_tiles']if OWNER in g['feature_local_ids'])
    report={};neighbors={}
    for role,(triangles,peer,assignment) in ctx.decode_group(group,OWNER).items():
        original=ctx.project_faces(triangles);other=ctx.project_faces(peer);remaining=original.difference(mask)
        assert .54 < remaining.area/original.area < .80
        assert other.distance(mask)>1 and other.distance(outline)>1
        report[role]=dict(triangles=len(triangles),original_m2=original.area,replaced_m2=original.intersection(mask).area,retained_m2=remaining.area,
                          peer_triangles=len(peer),peer_cut_m2=other.intersection(mask).area,peer_model_gap_m=other.distance(outline),
                          assignment=assignment,height_m=float(triangles[:,:,2].max()))
        if role=='far':far=original
    for i in NEIGHBORS:
        g=next(g for g in review['near_tiles']if i in g['feature_local_ids'])
        neighbors[i]={'source_key':next(o['key']for o in review['owners'] if o['local_id']==i)}
        for role,(triangles,_,assignment)in ctx.decode_group(g,i).items():
            other=ctx.project_faces(triangles);assert other.distance(mask)>1,other.distance(mask)
            neighbors[i][role]=dict(triangles=len(triangles),distance_to_cut_m=other.distance(mask),distance_to_this_model_m=other.distance(outline),cut_m2=other.intersection(mask).area,assignment=assignment)
    seams=[]
    for start,end in zip(mask.exterior.coords,list(mask.exterior.coords)[1:]):
        crossing=far.intersection(LineString([start,end]))
        seams.extend(x for x in shapely.get_parts(crossing)if isinstance(x,LineString)and x.length>.012)
    assert len(seams)>=3
    meta=read(ctx.files['READY.json'])
    caps=dict(base_m=0,roof_m=report['far']['height_m'],height_reference=[meta['origin_longitude'],meta['origin_latitude']],far_sha256=sha(ctx.files['far.glb']),geometry=ctx.wgs(MultiLineString(seams)))
    tests=[('foot of courtyard steps',0,-2.21,False),('first tread',0,-1.61,False),
           ('portico landing',0,.86,False),('deep reveal before door',.91,1.40,False),
           ('closed threshold',0,1.60,True),('northern stone jamb',-1.57,.087,True),
           ('southern stone jamb',1.57,.087,True),('entrance facade northern bay',-8.06,.40,True),
           ('entrance facade southern bay',8.03,.40,True),('yard in front of window',4.32,-.45,False),
           ('south return wall',9.56,6.42,True),('beside south wall',11.17,6.42,False),
           ('original rear wing remains',0,8.3,True),('central southern original rear wing',0,17.24,True)]
    tests=[(name,x*sx,y*sy,expected)for name,x,y,expected in tests]
    for i in NEIGHBORS:tests.append((f'retained original building {i}',*ctx.footprints[i].representative_point().coords[0],True))
    witnesses=[]
    for name,x,y,expected in tests:
        pt=Point(x,y);own=occupied.covers(pt);ret=ctx.footprints[OWNER].difference(mask).covers(pt)
        others=[i for i,g in ctx.footprints.items() if i!=OWNER and g.covers(pt)]
        assert bool(own or ret or others)==expected,(name,own,ret,others)
        w=dict(name=name,xy=[x,y],point=ctx.to_wgs(np.array([[x,y]]))[0].tolist(),expected='building' if expected else None,modelObstacle=own,cut=mask.covers(pt),retained=ret)
        if others:w['ownerLocalId']=others[0]
        witnesses.append(w)
    frame=review['author_frame'];c=dict(id=ID,**frame['anchor'],heading=frame['runtime_heading_deg'],scale=1,altitude=0,
        owner={'macro_id':review['frozen_macro'],'feature_local_id':OWNER},source_feature_ids={'building':[review['owner']['source_key'].split(':')[1]],'building_part':[]},
        bounds_glb=bounds,model_geometry_sha256={k:v['sha256']for k,v in assets.items()},replacement_geometry=ctx.wgs(mask),collision_geometry=ctx.wgs(occupied),source_section_caps=caps,
        overviewBearing=8,overviewPitch=31,overviewZoom=19.38,lod_switch_in_m=490,lod_switch_out_m=650,maxDistance=690,
        navigation={'listed':False,'status':'观看院内门廊、南侧临街拱窗和两处山墙。后部民居保留原体。'},
        placement={'status':'estimated','note':'市登记门牌、2号楼独立点、两期院内实照、屋面影像、冻结地块786及2021年北京西路两处同向街景共同确认本栋。西侧正面以原短边12.55米校准、南面长边约20.77米，院内通道的高度与山墙进深依照片估算。'},
        partial_model=True,model_scope=read(args.manifest)['model_scope_zh'])
    for key in ('replacement_geometry','collision_geometry'):checked_geometry(c[key],key,collision=key=='collision_geometry')
    write(args.out/'final-placement-contract.json',c)
    write(args.out/'placement-geometry.json',dict(id=ID,source_sha256=sha(source),script_sha256=sha(Path(__file__)),manifest_sha256=sha(args.manifest),
         assets=assets,near_and_far=report,neighbors=neighbors,ground_probes=witnesses,model_projection_m2=outline.area,collision_m2=occupied.area,
         seam_lengths_m=[part.length for part in seams],contract_sha256=sha(args.out/'final-placement-contract.json')))
    print(report,neighbors,len(witnesses),len(seams))
if __name__=='__main__':verify()
