"""Check the occupied Pei mansion, garden edge, independent street gates and neighboring buildings."""
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
MODEL='jingan-pei-mansion-garden-front'
SRC=PROJECT/'source/precise'/MODEL
OWNER=3135
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
    # Only the single registered house participates. Other buildings, street gates and garden remain in the city layer.
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
    outline=np.asarray(p['source_local_outline_m'])
    nw,ne,se,sw=outline
    xc=(se[0]+sw[0])/2; y=sw[1]
    offset=lambda u,v:(xc+u,y+v)
    front=[offset(-9.34,1.13),offset(-8.37,0),offset(-5.37,0),offset(-3.71,1.03),offset(3.71,1.03),offset(5.37,0),offset(8.37,0),offset(9.34,1.13)]
    body=Polygon([*front,tuple(ne),tuple(nw)])
    collision=body
    assert collision.difference(ground.buffer(.055)).area<.014
    spots=[]
    def add(label,xy,obstacle,clipped,neighbor=None):
        pnt=Point(xy);assert collision.covers(pnt)==obstacle and cut.covers(pnt)==clipped,(label,xy)
        if neighbor:assert mesh.footprints[neighbor].covers(pnt)
        spots.append(dict(name=label,xy=list(xy),modelObstacle=obstacle,cut=clipped,expected='building' if obstacle or neighbor else None,**({'ownerLocalId':neighbor}if neighbor else {})))
    for label,u,v in [('west bay interior',-6.3,.64),('east bay interior',6.3,.64),('behind hotel door',0,1.65),('house centre',0,10.15),('rear enclosed mass',-2,21)]:
        add(label,offset(u,v),True,True)
    for label,u,v in [('before entrance steps',0,-.89),('garden outside west bay',-6.2,-1.42),('garden outside east bay',6.2,-1.42),('entrance stair lower tread',0,.12),('faceted bay inner return',-4.04,.46)]:
        point=offset(u,v);add(label,point,False,cut.covers(Point(point)))
    for i in [861,579,416]:
        pt=mesh.footprints[i].representative_point();add('independent mapped building '+str(i),pt.coords[0],False,False,i)
    cam=read(SRC/'camera-preflight.json');fr=src['author_frame']
    contract=dict(id=MODEL,**fr['anchor'],heading=fr['runtime_heading_deg'],scale=1,altitude=0,owner={'macro_id':src['frozen_macro'],'feature_local_id':OWNER},
        source_feature_ids={'building':[src['owner']['source_key'].removeprefix('building:')],'building_part':[]},
        replacement_geometry=mesh.wgs(cut),collision_geometry=mesh.wgs(collision),bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},overviewBearing=cam['recommendation'][1]%360,overviewPitch=cam['recommendation'][2],overviewZoom=19.35,
        maxDistance=430,lod_switch_in_m=510,lod_switch_out_m=635,navigation={'listed':False,'status':'从园侧看两列折窗与上下两层回纹栏板。'},
        placement={'status':'estimated','note':'两条道路的地址点与园内正面实照对应独立主楼3135，东侧办公楼及院内设施独立。碰撞沿折面窗和玻璃门的实际围护线，街门、园地与入门前石阶通行。侧后墙、层高和屋顶竖井进深由足迹及照片估算。'},
        partial_model=False,model_scope=m['model_scope_zh'])
    for key in ['replacement_geometry','collision_geometry']:checked_geometry(contract[key],key,collision=key=='collision_geometry')
    args.out.mkdir(exist_ok=True,parents=True)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'footprint-review.json',dict(id=MODEL,source=src['owner'],manifest_sha256=sha(args.manifest),
         source_sha256=sha(SRC/'footprint-review.json'),script_sha256=sha(Path(__file__)),near_group=g,far_and_near=source_stats,nearest_neighbor={'local_id':closest,'m':mindist},
         cut_m2=cut.area,total_collision_m2=collision.area,body_collision_m2=body.area,garden_cutouts_m2=source.difference(collision).area,checked_source_footprint_m2=source.area,
         maximum_model_ground_outside_collision_m2=ground.difference(collision).area,cut_xy=list(cut.exterior.coords),ground=spots))
    print('source count',len(g['feature_local_ids']),'cut vertices',len(cut.exterior.coords)-1,'min gap',mindist,'collision',round(collision.area,2),len(spots),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/MODEL/'manifest.json');ap.add_argument('--macro',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    with tempfile.TemporaryDirectory()as w:evaluate(args,Path(w))
