"""Measure the named V-shaped Washington Apartments, its two street faces and original courtyard."""
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
ID='xuhui-washington-apartments'
OWNER=131
NEIGHBORS=(2018,2513,642,4120)

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
    sys.path.insert(0,str(PROJECT/'source/precise'/ID/'source'))
    sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
    from street_fronts import section_footprint, section_lines
    from shapely.geometry import Polygon
    outer,_=section_lines()
    mask=section_footprint(depth=3.35,street_overhang=1.27).buffer(.18,join_style='mitre')
    assert mask.buffer(.003).covers(outline),(outline.bounds,outline.difference(mask).area)
    occupied=section_footprint()
    def point(side,distance,depth):
        # Distances on each long frontage start at the junction with the north chamfer.
        if side==0:a,b=outer[1],outer[0]
        else:a,b=outer[2],outer[3]
        tangent=(b-a)/np.linalg.norm(b-a)
        inside=np.array([tangent[1],-tangent[0]]) * (1 if side==0 else -1)
        return a+distance*tangent+depth*inside
    for side,centre,width,depth in [(0,31.35,2.34,.895),(2,10.72,2.17,.522)]:
        # An approach into each recess remains clear up to the closed leaf.
        occupied=occupied.difference(Polygon([point(side,centre+offset,d) for offset,d in [(-width/2,-.16),(width/2,-.16),(width/2,depth),(-width/2,depth)]]))
    group=next(g for g in review['near_tiles']if OWNER in g['feature_local_ids'])
    report={};neighbors={}
    for role,(triangles,peer,assignment) in ctx.decode_group(group,OWNER).items():
        original=ctx.project_faces(triangles);other=ctx.project_faces(peer);remaining=original.difference(mask)
        assert .64 < remaining.area/original.area < .85
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
    tests=[]
    for side,centre,depth,name in [(0,31.35,.895,'48 Gaoan entrance'),(2,10.72,.522,'Hengshan shop recess')]:
        for d,state,part in [(-2,False,'street'),(-.13,False,'at opening'),(.28,False,'inside reveal'),(depth-.06,False,'in front of leaf'),(depth+.07,True,'closed leaf')]:
            tests.append((name+' '+part,*point(side,centre,d),state))
        for offset in (-1.52,1.52):
            tests.append((name+' side jamb',*point(side,centre+offset,.24),True))
    for side,dist in [(0,2.8),(0,18.5),(0,47),(2,3.5),(2,15.8)]:
        tests.append(('visible section at street edge',*point(side,dist,.54),True))
        tests.append(('sidewalk on street side',*point(side,dist,-1.79),False))
    tests.extend([('original west wing beyond authored corner return',8.0,31.0,True),('original court behind short northern tip',-1.68,29.,False)])
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
        overviewBearing=218,overviewPitch=38,overviewZoom=18.95,lod_switch_in_m=490,lod_switch_out_m=650,maxDistance=690,
        navigation={'listed':False,'status':'观看北端街角、高安路48号花饰入口及凸窗。院内与衡山路西翼保留原体。'},
        placement={'status':'estimated','note':'房管局登记衡山路303号，原生131的中英文名称与现行OSM相符。高安路48号实牌、街景三站和独立门牌点约束其距转角的位置。高度、窗框宽度及凸窗进深为估值。'},
        partial_model=True,model_scope=read(args.manifest)['model_scope_zh'])
    for key in ('replacement_geometry','collision_geometry'):checked_geometry(c[key],key,collision=key=='collision_geometry')
    write(args.out/'final-placement-contract.json',c)
    write(args.out/'placement-geometry.json',dict(id=ID,source_sha256=sha(source),script_sha256=sha(Path(__file__)),manifest_sha256=sha(args.manifest),
         assets=assets,near_and_far=report,neighbors=neighbors,ground_probes=witnesses,model_projection_m2=outline.area,collision_m2=occupied.area,
         seam_lengths_m=[part.length for part in seams],contract_sha256=sha(args.out/'final-placement-contract.json')))
    print(report,neighbors,len(witnesses),len(seams))
if __name__=='__main__':verify()
