"""Check the separate private house and gate against the actual native city triangles."""
import argparse
import tempfile
import sys
from pathlib import Path
import numpy as np
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import unary_union
from shapely import get_parts
AUDIT=Path(__file__).resolve().parent
PROJECT=AUDIT.parents[2]
MODEL='xuhui-yicun-no2-street-front'
SRC=PROJECT/'source/precise'/MODEL
OWNER=2940
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

def evaluate(args,work):
    src=read(SRC/'footprint-review.json');p=read(SRC/'source/parameters.json');m=read(args.manifest)
    for record in src['frozen_bindings']:
        rel=record['repository_path'].split(src['frozen_macro']+'/')[1]
        (work/Path(rel).name).symlink_to((args.macro/rel).resolve())
    mesh=PlacementMeshes(PROJECT,work,src)
    assets,bounds,profile,ground=mesh.decode_model(args.manifest)
    g=src['near_tiles'][0];triangles=mesh.decode_group(g,OWNER)
    source=mesh.footprints[OWNER]
    old={k:mesh.project_faces(data[0]) for k,data in triangles.items()}
    # Surround all of the real coarse owner's reliefs. The separate gate and garden are outside this cut.
    cut=unary_union([source,*old.values()]).convex_hull.simplify(.10).buffer(.27,join_style=2)
    cut=cut.simplify(.10,preserve_topology=True)
    if not all(cut.covers(v)for v in [source,*old.values()]):raise ValueError('Incomplete previous owner cut')
    source_stats={}
    for role,(target,others,assignment)in triangles.items():
        neighbor=mesh.project_faces(others);gap=neighbor.distance(cut)
        assert gap>.65 and neighbor.intersection(cut).area<.001
        source_stats[role]=dict(affected_triangles=len(target),other_triangles=len(others),nearest_other_m=gap,source_m2=old[role].area,
            retained_source_m2=old[role].difference(cut).area,other_cut_overlap_m2=neighbor.intersection(cut).area,source_peak_m=float(target[:,:,2].max()),assignment=assignment)
    mindist,closest=min((sh.distance(cut),i)for i,sh in mesh.footprints.items()if i!=OWNER)
    assert mindist>.65
    body=Polygon(p['source_local_outline_m'])
    start,end=np.asarray(p['private_gate_ends_m']);d=(end-start)/np.linalg.norm(end-start);n=np.array([d[1],-d[0]])
    barrier=unary_union([LineString([start,end]).buffer(.030,cap_style='flat'),*
        [Polygon([v+.211*i*d+.211*j*n for i,j in ((-1,-1),(1,-1),(1,1),(-1,1))])for v in (start,end)]])
    collision=unary_union([body,barrier]);assert collision.difference(ground.buffer(.055)).area<.012
    spots=[]
    def add(label,xy,obstacle,clipped,neighbor=None):
        pnt=Point(xy);assert collision.covers(pnt)==obstacle and cut.covers(pnt)==clipped,(label,xy)
        if neighbor:assert mesh.footprints[neighbor].covers(pnt)
        spots.append(dict(name=label,xy=list(xy),modelObstacle=obstacle,cut=clipped,expected='building' if obstacle or neighbor else None,**({'ownerLocalId':neighbor}if neighbor else {})))
    for label,point in [('registered core',(0.,0.)),('inside front gable',(2.3,-6.35)),('inside recessed wing',(-4.3,-5.2)),('north roof mass',(0.,5.2))]:add(label,point,True,True)
    add('closed private double gate',(start+end)/2,True,False)
    for i,v in enumerate((start,end)):add('private gate pier '+str(i+1),v,True,False)
    for label,xy in [('open garden',(0.,-10.1)),('between porch and gate',(-3.2,-12.2)),('outside private gate',(-3.1,-17.5)),('beyond east pier',(1.,-15.8))]:add(label,xy,False,False)
    for id in [2927,*[o for o in g['feature_local_ids']if o not in (OWNER,2927)][:2]]:
        v=mesh.footprints[id].representative_point();add('independent neighboring building '+str(id),v.coords[0],False,False,id)
    cam=read(SRC/'camera-preflight.json');fr=src['author_frame']
    contract=dict(id=MODEL,**fr['anchor'],heading=fr['runtime_heading_deg'],scale=1,altitude=0,owner={'macro_id':src['frozen_macro'],'feature_local_id':OWNER},
        source_feature_ids={'building':[src['owner']['source_key'].removeprefix('building:')],'building_part':[]},
        replacement_geometry=mesh.wgs(cut),collision_geometry=mesh.wgs(collision),bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},overviewBearing=cam['recommendation'][1],overviewPitch=cam['recommendation'][2],overviewZoom=19.35,
        maxDistance=430,lod_switch_in_m=510,lod_switch_out_m=635,navigation={'listed':False,'status':'观察临街园侧窗墙与本户铁门。'},
        placement={'status':'estimated','note':'逸村淮海中路1610弄2号按区政府资料、公开门牌记录、分栋原地块和多时期街面照片定位。花铁门单独落在院界，院内留出开敞空间。立面高度、后侧屋面和园墙间距按图估计。'},
        partial_model=False,model_scope=m['model_scope_zh'])
    for key in ['replacement_geometry','collision_geometry']:checked_geometry(contract[key],key,collision=key=='collision_geometry')
    args.out.mkdir(exist_ok=True,parents=True)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'footprint-review.json',dict(id=MODEL,source=src['owner'],manifest_sha256=sha(args.manifest),
         source_sha256=sha(SRC/'footprint-review.json'),script_sha256=sha(Path(__file__)),near_group=g,far_and_near=source_stats,nearest_neighbor={'local_id':closest,'m':mindist},
         cut_m2=cut.area,total_collision_m2=collision.area,body_collision_m2=body.area,private_gate_collision_m2=barrier.area,checked_source_footprint_m2=source.area,
         maximum_model_ground_outside_collision_m2=ground.difference(collision).area,cut_xy=list(cut.exterior.coords),ground=spots))
    print('source count',len(g['feature_local_ids']),'cut vertices',len(cut.exterior.coords)-1,'min gap',mindist,'collision',round(collision.area,2),len(spots),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/MODEL/'manifest.json');ap.add_argument('--macro',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    with tempfile.TemporaryDirectory()as w:evaluate(args,Path(w))
