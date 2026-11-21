"""Check the garden-facing setback tower, cantilever and retained Picardie wings."""
import argparse
from pathlib import Path
import sys
import numpy as np
import shapely
from shapely.ops import unary_union
from shapely.geometry import LineString,MultiLineString,Point,box,shape

AUDIT=Path(__file__).resolve().parent
PROJECT=AUDIT.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
ID='xuhui-picardie-apartments-south-front'
OWNER=1958
NEIGHBORS=(1834,774,1920,1504)

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
    mask=unary_union([box(-15.64,-.79,15.64,4.56),box(-8.02,-4.62,8.02,-.78)])
    assert mask.buffer(.003).covers(outline),(outline.bounds,outline.difference(mask).area)
    wall=box(-15.5,0,15.5,4.4)
    openings=[box(x-w/2,-.03,x+w/2,.44) for x,w in ((-4.15,1.55),(0.,3.35),(4.15,1.55))]
    occupied=wall.difference(unary_union(openings))
    group=next(g for g in review['near_tiles']if OWNER in g['feature_local_ids'])
    report={};neighbors={}
    for role,(triangles,peer,assignment) in ctx.decode_group(group,OWNER).items():
        original=ctx.project_faces(triangles);other=ctx.project_faces(peer);remaining=original.difference(mask)
        assert .94 < remaining.area/original.area < .99
        assert other.distance(mask)>1 and other.distance(outline)>1
        report[role]=dict(triangles=len(triangles),original_m2=original.area,replaced_m2=original.intersection(mask).area,retained_m2=remaining.area,
                          peer_triangles=len(peer),peer_cut_m2=other.intersection(mask).area,peer_model_gap_m=other.distance(outline),
                          assignment=assignment,height_m=float(triangles[:,:,2].max()))
        if role=='far':far=original
    for i in NEIGHBORS:
        g=next(g for g in review['near_tiles']if i in g['feature_local_ids'])
        neighbors[i]={'source_key':next(o['key']for o in review['owners'] if o['local_id']==i)}
        if i in (774,1920):
            from source_meshes import house_meshes
            variants=house_meshes(ctx,g,i)
        else:
            variants=ctx.decode_group(g,i)
        for role,(triangles,_,assignment) in variants.items():
            other=ctx.project_faces(triangles);assert other.distance(mask)>1,other.distance(mask)
            neighbors[i][role]=dict(triangles=len(triangles),distance_to_cut_m=other.distance(mask),distance_to_this_model_m=other.distance(outline),cut_m2=other.intersection(mask).area,assignment=assignment)
    seams=[]
    for start,end in zip(mask.exterior.coords,list(mask.exterior.coords)[1:]):
        crossing=far.intersection(LineString([start,end]))
        seams.extend(x for x in shapely.get_parts(crossing)if isinstance(x,LineString)and x.length>.012)
    assert len(seams)>=3
    meta=read(ctx.files['READY.json'])
    caps=dict(base_m=0,roof_m=report['far']['height_m'],height_reference=[meta['origin_longitude'],meta['origin_latitude']],far_sha256=sha(ctx.files['far.glb']),geometry=ctx.wgs(MultiLineString(seams)))
    tests=[]
    for x,width in ((-4.15,1.55),(0.,3.35),(4.15,1.55)):
        for y,label,solid in ((-5,'garden approach',False),(-3.8,'under restored cantilever',False),(-.2,'before reveal',False),(.28,'inside reveal',False),(.52,'closed timber leaves',True)):
            tests.append((label,x,y,solid))
        for side in (-1,1):tests.append(('pale portal pier',x+side*(width/2+.13),.2,True))
    for x in (-14.,-9.,9.,14.):
        tests += [('beneath south wing wall',x,.6,True),('garden outside wing',x,-2.5,False)]
    tests += [('original rear of hotel',0,19.,True),('side wing east of authored frontage',19.1,2.,True)]
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
        overviewBearing=2,overviewPitch=70,overviewZoom=18.75,lod_switch_in_m=490,lod_switch_out_m=650,maxDistance=690,
        navigation={'listed':False,'status':'从南花园望向两列深阳台、上部退台和534号无外柱的雨篷。原楼后部与其余各翼保留。'},
        placement={'status':'estimated','note':'2D022登记衡山路534号，酒店及主楼入口点均在原生1958范围。2022、2024两期影像雨篷与原楼南边共同估算轴线。未取得竣工标高，檐高、层高与进深按照片比例估计。'},
        partial_model=True,model_scope=read(args.manifest)['model_scope_zh'])
    for key in ('replacement_geometry','collision_geometry'):checked_geometry(c[key],key,collision=key=='collision_geometry')
    write(args.out/'final-placement-contract.json',c)
    write(args.out/'placement-geometry.json',dict(id=ID,source_sha256=sha(source),script_sha256=sha(Path(__file__)),manifest_sha256=sha(args.manifest),
         assets=assets,near_and_far=report,neighbors=neighbors,ground_probes=witnesses,model_projection_m2=outline.area,collision_m2=occupied.area,
         seam_lengths_m=[part.length for part in seams],contract_sha256=sha(args.out/'final-placement-contract.json')))
    print(report,neighbors,len(witnesses),len(seams))
if __name__=='__main__':verify()
