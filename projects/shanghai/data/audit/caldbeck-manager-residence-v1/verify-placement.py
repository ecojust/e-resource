"""Check the Wukang Road villa, open ground-floor porch, pillars and neighboring city meshes."""
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
MODEL='xuhui-caldbeck-manager-residence'
SRC=PROJECT/'source/precise'/MODEL
OWNER=2729
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
    # Only the primary 1928 house is selected. Other garden structures remain independent.
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
    street_start,street_end=outline[3],outline[2]
    u=(street_end-street_start)/np.linalg.norm(street_end-street_start)
    normal=np.array([u[1],-u[0]]);center=(street_start+street_end)/2
    half=np.linalg.norm(street_end-street_start)/2
    left=-half+.10;right=half-2.21
    pos=lambda t,d:center+t*u+d*normal
    recess=Polygon([pos(t,d)for t,d in [(left,.04),(right,.04),(right,-2.06),(left,-2.06)]])
    body=Polygon(outline).difference(recess)
    posts=[]
    pillars=np.linspace(left+.14,right-.14,4)
    for t in pillars:
        posts.append(Polygon([pos(t+dx,-.045+dy)for dx,dy in [(-.20,-.23),(.20,-.23),(.20,.23),(-.20,.23)]]))
    # An occupied side balcony at the west has two ground-supported brick piers.
    a,b=outline[0],outline[5];west=(b-a)/np.linalg.norm(b-a);street_normal=np.array([west[1],-west[0]])
    for t in (-2.99,3.24):
        foot=(a+b)/2+t*west+.78*street_normal
        posts.append(Polygon([foot+i*.13*west+j*.135*street_normal for i,j in ((-1,-1),(1,-1),(1,1),(-1,1))]))
    supports=unary_union(posts);collision=unary_union([body,supports])
    assert collision.difference(ground.buffer(.055)).area<.014,collision.difference(ground.buffer(.055)).area
    spots=[]
    def add(label,xy,obstacle,clipped,neighbor=None):
        pnt=Point(xy);assert collision.covers(pnt)==obstacle and cut.covers(pnt)==clipped,(label,xy)
        if neighbor:assert mesh.footprints[neighbor].covers(pnt)
        spots.append(dict(name=label,xy=list(xy),modelObstacle=obstacle,cut=clipped,expected='building' if obstacle or neighbor else None,**({'ownerLocalId':neighbor}if neighbor else {})))
    for label,point in [('main occupied floor',(0.,1.0)),('inside projecting west wing',(-5.7,-7.4)),('inside east bay',(10.,-3.7)),('behind garden porch',(3.,-2.7))]:add(label,point,True,True)
    for index,t in enumerate(pillars):add('brick garden porch pier '+str(index+1),pos(t,-.045),True,True)
    for k,(lo,hi)in enumerate(zip(pillars,pillars[1:])):
        add('open passage between brick porch piers '+str(k+1),pos((lo+hi)/2,-.66),False,True)
    for index,post in enumerate(posts[-2:]):
        pos_w=post.representative_point()
        add('supported western balcony pier '+str(index+1),pos_w.coords[0],True,cut.covers(pos_w))
    for label,point in [('unobstructed garden before terrace',(2.,-7.64)),('beyond projecting southwest gable',(-6.,-10.7)),('west garden outside balcony',(-13.2,-1.2))]:
        add(label,point,False,cut.covers(Point(point)))
    for i in [788,4131,1998]:
        pt=mesh.footprints[i].representative_point();add('independent source '+str(i),pt.coords[0],False,False,i)
    cam=read(SRC/'camera-preflight.json');fr=src['author_frame']
    contract=dict(id=MODEL,**fr['anchor'],heading=fr['runtime_heading_deg'],scale=1,altitude=0,owner={'macro_id':src['frozen_macro'],'feature_local_id':OWNER},
        source_feature_ids={'building':[src['owner']['source_key'].removeprefix('building:')],'building_part':[]},
        replacement_geometry=mesh.wgs(cut),collision_geometry=mesh.wgs(collision),bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},overviewBearing=cam['recommendation'][1]%360,overviewPitch=cam['recommendation'][2],overviewZoom=19.35,
        maxDistance=430,lod_switch_in_m=510,lod_switch_out_m=635,navigation={'listed':False,'status':'观察西南山墙、砖柱敞廊及园侧露台。'},
        placement={'status':'estimated','note':'按市房管局2D036、武康路99号原照、地方志、馆藏园侧照片及同址OSM建筑核对。主楼沿自身足印落地，柱间敞廊保留通行。西侧院门、院内附属与其他地块独立。檐高、进深和两处烟囱尺度由照片及屋面影像估计。'},
        partial_model=False,model_scope=m['model_scope_zh'])
    for key in ['replacement_geometry','collision_geometry']:checked_geometry(contract[key],key,collision=key=='collision_geometry')
    args.out.mkdir(exist_ok=True,parents=True)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'footprint-review.json',dict(id=MODEL,source=src['owner'],manifest_sha256=sha(args.manifest),
         source_sha256=sha(SRC/'footprint-review.json'),script_sha256=sha(Path(__file__)),near_group=g,far_and_near=source_stats,nearest_neighbor={'local_id':closest,'m':mindist},
         cut_m2=cut.area,total_collision_m2=collision.area,body_collision_m2=body.area,six_pier_collision_m2=supports.area,open_porch_m2=recess.intersection(Polygon(outline)).area,checked_source_footprint_m2=source.area,
         maximum_model_ground_outside_collision_m2=ground.difference(collision).area,cut_xy=list(cut.exterior.coords),ground=spots))
    print('source count',len(g['feature_local_ids']),'cut vertices',len(cut.exterior.coords)-1,'min gap',mindist,'collision',round(collision.area,2),len(spots),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/MODEL/'manifest.json');ap.add_argument('--macro',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    with tempfile.TemporaryDirectory()as w:evaluate(args,Path(w))
