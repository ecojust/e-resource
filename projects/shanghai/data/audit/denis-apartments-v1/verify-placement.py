"""Compare the two-street masonry section with the actual owner-scoped near and far urban meshes."""
import argparse
from pathlib import Path
import sys
import tempfile

from shapely.geometry import LineString, MultiLineString, Polygon, Point
from shapely.ops import unary_union

AUDIT=Path(__file__).resolve().parent
PROJECT=AUDIT.parents[2]
SOURCE=PROJECT/'source/precise/jingan-denis-apartments'
OWNER=993
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry


def evaluate(args,work):
    source=read(SOURCE/'footprint-review.json')
    for receipt in source['frozen_bindings']:
        rel=receipt['repository_path'].split(source['frozen_macro']+'/')[1]
        (work/Path(rel).name).symlink_to((args.macro/rel).resolve())
    mesh=PlacementMeshes(PROJECT,work,source)
    assets,bounds,profile,ground=mesh.decode_model(args.manifest)
    tile=source['near_tiles'][0]
    group=mesh.decode_group(tile,OWNER)
    native={role:mesh.project_faces(tris[0]) for role,tris in group.items()}
    source_plan=mesh.footprints[OWNER]
    parameters=read(SOURCE/'source/parameters.json')
    street=LineString(parameters['street_path_xy'])
    source_hull=unary_union([source_plan,*native.values()]).buffer(.22,join_style='mitre')
    cut=source_hull.intersection(street.buffer(5.09,cap_style='square',join_style='mitre')).simplify(.16,preserve_topology=True)
    collision=Polygon(parameters['strip_xy'])
    residual={};summaries={}
    for name,(target,others,assign)in group.items():
        before=native[name];residual[name]=before.difference(cut)
        nearby=mesh.project_faces(others)
        untouched=nearby.intersection(cut).area
        assert untouched<.002,(name,untouched)
        ratio=residual[name].area/before.area
        assert .30<ratio<.75,(name,ratio)
        summaries[name]=dict(original_m2=before.area,retained_m2=residual[name].area,
              retained_fraction=ratio,other_mesh_cut_m2=untouched,other_mesh_clearance_m=nearby.distance(cut),
              other_meshes_model_overlap_m2=nearby.intersection(ground).area,matched_triangles=len(target),
              other_group_triangles=len(others),source_height_m=target[:,:,2].max(),assignment=assign)
    neighbors={i:g for i,g in mesh.footprints.items() if i!=OWNER and g.distance(cut)<30}
    gaps={i:dict(cut_clearance_m=g.distance(cut),model_clearance_m=g.distance(collision),
                 cut_overlap_m2=g.intersection(cut).area,model_overlap_m2=g.intersection(collision).area)
          for i,g in neighbors.items()}
    assert all(g['cut_overlap_m2']<.001 and g['model_overlap_m2']<.001 for g in gaps.values()),gaps
    assert 322 in gaps and 617 in gaps
    seams={role:cut.boundary.intersection(geom) for role,geom in native.items()}
    def lines(g):
        if g.geom_type=='LineString':return [g]
        if hasattr(g,'geoms'):return [piece for child in g.geoms for piece in lines(child)]
        return []
    far_lines=[g.simplify(.08)for g in lines(seams['far']) if g.length>.25]
    assert far_lines and all(65<v.length<120 for v in seams.values()),{k:v.length for k,v in seams.items()}
    ready=read(args.macro/'READY.json')
    cap=dict(geometry=mesh.wgs(MultiLineString(far_lines)),base_m=0,
             roof_m=summaries['far']['source_height_m'],height_reference=[ready['origin_longitude'],ready['origin_latitude']],far_sha256=ready['far']['sha256'])
    spots=[]
    def check(name,xy,hit,owner=None):
        pos=Point(xy);clipped=cut.covers(pos);assert collision.covers(pos)==hit,(name,xy)
        if owner:assert mesh.footprints[owner].covers(pos) and not clipped
        spots.append(dict(name=name,xy=list(xy),modelObstacle=hit,cut=clipped,
                 expected='building'if hit or owner else None,**({'ownerLocalId':owner}if owner else {})))
    path=parameters['street_path_xy']
    for idx in (0,1,2,3,4,5):
        start,end=path[idx:idx+2];d=LineString([start,end]);mid=d.interpolate(.5,normalized=True)
        tx=(end[0]-start[0])/d.length;ty=(end[1]-start[1])/d.length
        check('inside photographed shop or bay '+str(idx),(mid.x-2*ty,mid.y+2*tx),True)
        check('unobstructed pavement '+str(idx),(mid.x+2.3*ty,mid.y-2.3*tx),False)
    old=residual['far'].intersection(residual['near']).intersection(source_plan).representative_point()
    check('retained inner rooms of 993',(old.x,old.y),False,OWNER)
    for i in [322,617,2103,1964]:
        pos=mesh.footprints[i].representative_point();check('neighbor '+str(i),pos.coords[0],False,i)
    fr=source['author_frame'];cam=read(SOURCE/'camera-preflight.json');m=read(args.manifest)
    contract=dict(id=m['id'],**fr['anchor'],heading=fr['runtime_heading_deg'],scale=1,altitude=0,
        owner={'macro_id':source['frozen_macro'],'feature_local_id':OWNER},
        source_feature_ids={'building':[source['owner']['source_key'].split(':')[-1]],'building_part':[]},
        replacement_geometry=mesh.wgs(cut),collision_geometry=mesh.wgs(collision),bounds_glb=bounds,
        source_section_caps=cap,model_geometry_sha256={k:r['sha256']for k,r in assets.items()},
        overviewBearing=cam['recommendation'][1]%360,overviewPitch=cam['recommendation'][2],overviewZoom=19.6,
        lod_switch_in_m=500,lod_switch_out_m=660,maxDistance=460,
        navigation={'listed':False,'status':'从南京西路和石门二路观察公寓商铺、转角石带和褐砖竖向凸肋。'},
        placement={'status':'estimated','note':'实名地块与778号门牌点相合。993仅替换可由2013至2020年照片确认的街面，保留内侧原城市体量、对面同孚大楼与道路。临街截面厚度和遮挡的屋面为估计。'},
        partial_model=True,model_scope=m['model_scope_zh'])
    for key in ['replacement_geometry','collision_geometry']:checked_geometry(contract[key],key,collision=key=='collision_geometry')
    args.out.mkdir(exist_ok=True,parents=True)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'footprint-review.json',dict(id=m['id'],asset_sha256={k:v['sha256']for k,v in assets.items()},
          source_sha256=sha(SOURCE/'footprint-review.json'),script_sha256=sha(Path(__file__)),source=source['owner'],
          near_group=tile,far_and_near=summaries,neighbors=gaps,ground=spots,cut_m2=cut.area,
          collision_m2=collision.area,ground_outside_collision_m2=ground.difference(collision).area,
          original_993_m2=source_plan.area,residual_seam_length_m={k:v.length for k,v in seams.items()}))
    print('Verified clipped owner',OWNER,'and',len(neighbors),'unaffected nearby buildings;',len(spots),'ground probes.',flush=True)


if __name__=='__main__':
    cmd=argparse.ArgumentParser(description=__doc__);cmd.add_argument('--manifest',type=Path,required=True)
    cmd.add_argument('--macro',type=Path,required=True);cmd.add_argument('--out',type=Path,required=True);args=cmd.parse_args()
    with tempfile.TemporaryDirectory()as tmp:evaluate(args,Path(tmp))
