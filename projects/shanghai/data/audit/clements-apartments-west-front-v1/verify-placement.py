"""Compare the western apartment street wings with the actual owner-scoped near and far urban meshes."""
import argparse
from pathlib import Path
import sys
import numpy as np
import shapely as geo
import subprocess
import tempfile

from shapely.geometry import LineString, MultiLineString, Polygon, Point, box
from shapely.ops import unary_union

AUDIT=Path(__file__).resolve().parent
PROJECT=AUDIT.parents[2]
SOURCE=PROJECT/'source/precise/xuhui-clements-apartments-west-front'
OWNER=1925
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry


def decode_compound_group(mesh,tile):
    """Assign by all three vertices, testing both distance and the competing-owner margin."""
    ids=tile['feature_local_ids'];mesh.link('baseline-far.glb',mesh.files['far.glb'])
    mesh.link('baseline-near.glb.gz',mesh.files[Path(tile['file']).name])
    mesh.link('macro-READY.json',mesh.files['READY.json'])
    write(mesh.work/'context-features.json',[{'localId':v} for v in ids])
    subprocess.run(['node',mesh.decoders/'map-decode-source.mjs'],env=mesh.env,check=True,stdout=subprocess.DEVNULL)
    group={}
    for role in ('near','far'):
        tri=np.fromfile(mesh.work/f'baseline-{role}-triangles.f64',np.float64).reshape(-1,3,3)
        tri[:,:,:2]=tri[:,:,:2]@mesh.axes.T
        if role=='far':
            owners=np.fromfile(mesh.work/'baseline-far-owners.u32',np.uint32);proof={'method':'per-vertex feature ID'}
        else:
            pts=geo.points(tri[:,:,:2].reshape(-1,2))
            ds=np.column_stack([geo.distance(pts,mesh.footprints[v]).reshape(-1,3).max(axis=1)for v in ids])
            owners=np.array(ids)[ds.argmin(axis=1)]
            own=ds[:,ids.index(OWNER)];other=np.delete(ds,ids.index(OWNER),axis=1).min(axis=1)
            worst=float(own[owners==OWNER].max());gap=float((other-own)[owners==OWNER].min())
            next_gap=float((own-other)[owners!=OWNER].min())
            assert worst<.18 and gap>.19 and next_gap>.17,(worst,gap,next_gap)
            proof={'method':'minimax whole-triangle vertex distance with target/peer separation',
                   'worst_target_vertex_distance_m':worst,'nearest_alternative_owner_gap_m':gap,'nearest_target_gap_for_other_triangle_m':next_gap}
        assert set(owners)==set(ids)
        group[role]=(tri[owners==OWNER],tri[owners!=OWNER],proof)
    return group


def evaluate(args,work):
    source=read(SOURCE/'footprint-review.json')
    for receipt in source['frozen_bindings']:
        rel=receipt['repository_path'].split(source['frozen_macro']+'/')[1]
        (work/Path(rel).name).symlink_to((args.macro/rel).resolve())
    mesh=PlacementMeshes(PROJECT,work,source)
    assets,bounds,profile,ground=mesh.decode_model(args.manifest)
    tile=source['near_tiles'][0]
    group=decode_compound_group(mesh,tile)
    native={role:mesh.project_faces(tris[0]) for role,tris in group.items()}
    source_plan=mesh.footprints[OWNER]
    parameters=read(SOURCE/'source/parameters.json')
    xy=parameters['street_path_xy']
    source_hull=unary_union([source_plan,*native.values()]).buffer(.17,join_style='mitre')
    cut=source_hull.intersection(box(-22,-2,22,14.50)).simplify(.09)
    # Isolate the court screen and its real opening. The public passage at the
    # eastern end of the west block is independent and is never filled here.
    obstructions=ground.buffer(.035,join_style='mitre').simplify(.025)
    collision=obstructions
    residual={};summaries={}
    for name,(target,others,assign)in group.items():
        before=native[name];residual[name]=before.difference(cut)
        nearby=mesh.project_faces(others)
        untouched=nearby.intersection(cut).area
        assert untouched<.002,(name,untouched)
        ratio=residual[name].area/before.area
        assert .30<ratio<.79,(name,ratio)
        summaries[name]=dict(original_m2=before.area,retained_m2=residual[name].area,
              retained_fraction=ratio,other_mesh_cut_m2=untouched,other_mesh_clearance_m=nearby.distance(cut),
              other_meshes_model_overlap_m2=nearby.intersection(ground).area,matched_triangles=len(target),
              other_group_triangles=len(others),source_height_m=target[:,:,2].max(),assignment=assign)
    neighbors={i:g for i,g in mesh.footprints.items() if i!=OWNER and g.distance(cut)<30}
    gaps={i:dict(cut_clearance_m=g.distance(cut),model_clearance_m=g.distance(collision),
                 cut_overlap_m2=g.intersection(cut).area,model_overlap_m2=g.intersection(collision).area)
          for i,g in neighbors.items()}
    assert all(g['cut_overlap_m2']<.001 and g['model_overlap_m2']<.001 for g in gaps.values()),gaps
    assert 507 in gaps and 3746 in gaps
    seams={role:cut.boundary.intersection(geom) for role,geom in native.items()}
    def lines(g):
        if g.geom_type=='LineString':return [g]
        if hasattr(g,'geoms'):return [piece for child in g.geoms for piece in lines(child)]
        return []
    far_lines=[g.simplify(.08)for g in lines(seams['far']) if g.length>.25]
    assert far_lines and all(24<v.length<62 for v in seams.values()),{k:v.length for k,v in seams.items()}
    ready=read(args.macro/'READY.json')
    cap=dict(geometry=mesh.wgs(MultiLineString(far_lines)),base_m=0,
             roof_m=summaries['far']['source_height_m'],height_reference=[ready['origin_longitude'],ready['origin_latitude']],far_sha256=ready['far']['sha256'])
    spots=[]
    def check(name,xy,hit,owner=None):
        pos=Point(xy);clipped=cut.covers(pos);assert collision.covers(pos)==hit,(name,xy)
        if owner:assert mesh.footprints[owner].covers(pos) and not clipped
        spots.append(dict(name=name,xy=list(xy),modelObstacle=hit,cut=clipped,
                 expected='building'if hit or owner else None,**({'ownerLocalId':owner}if owner else {})))
    for name,x,y,hit in [
            ('east projecting wing',-13.,3.6,True),('west projecting wing',12.,4.1,True),
            ('recessed frontage',.05,12.5,True),('courtyard masonry screen',-1.58,.00,True),
            ('opening through private wall',2.79,.0,False),('free private court',.05,6.,False),
            ('east end pavement',-15.3,-2.1,False),('west end pavement',14.75,-2.1,False),
            ('opening between the two registered fronts',-23.5,2.1,False)]:
        check(name,(x,y),hit)
    old=residual['far'].intersection(residual['near']).intersection(source_plan).representative_point()
    check('retained rear of western block 1925',(old.x,old.y),False,OWNER)
    for i in [507,3746,3238,964,134]:
        pos=mesh.footprints[i].representative_point();check('neighbor '+str(i),pos.coords[0],False,i)
    fr=source['author_frame'];cam=read(SOURCE/'camera-preflight.json');m=read(args.manifest)
    contract=dict(id=m['id'],**fr['anchor'],heading=fr['runtime_heading_deg'],scale=1,altitude=0,
        owner={'macro_id':source['frozen_macro'],'feature_local_id':OWNER},
        source_feature_ids={'building':[source['owner']['source_key'].split(':')[-1]],'building_part':[]},
        replacement_geometry=mesh.wgs(cut),collision_geometry=mesh.wgs(collision),bounds_glb=bounds,
        source_section_caps=cap,model_geometry_sha256={k:r['sha256']for k,r in assets.items()},
        overviewBearing=cam['recommendation'][1]%360,overviewPitch=cam['recommendation'][2],overviewZoom=19.6,
        lod_switch_in_m=500,lod_switch_out_m=660,maxDistance=460,
        navigation={'listed':False,'status':'由复兴中路观察西前楼两翼、凹院及坡顶。'},
        placement={'status':'estimated','note':'1925只裁面向复兴中路的西前楼前段，保留后部及东前楼3746、弄内其余三楼、公共弄门和道路。街角屋面与凹院深处按可见范围估算。'},
        partial_model=True,model_scope=m['model_scope_zh'])
    for key in ['replacement_geometry','collision_geometry']:checked_geometry(contract[key],key,collision=key=='collision_geometry')
    args.out.mkdir(exist_ok=True,parents=True)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'footprint-review.json',dict(id=m['id'],asset_sha256={k:v['sha256']for k,v in assets.items()},
          source_sha256=sha(SOURCE/'footprint-review.json'),script_sha256=sha(Path(__file__)),source=source['owner'],
          near_group=tile,far_and_near=summaries,neighbors=gaps,ground=spots,cut_m2=cut.area,
          collision_m2=collision.area,ground_outside_collision_m2=ground.difference(collision).area,
          original_1925_m2=source_plan.area,residual_seam_length_m={k:v.length for k,v in seams.items()}))
    print('Verified clipped owner',OWNER,'and',len(neighbors),'unaffected nearby buildings;',len(spots),'ground probes.',flush=True)


if __name__=='__main__':
    cmd=argparse.ArgumentParser(description=__doc__);cmd.add_argument('--manifest',type=Path,required=True)
    cmd.add_argument('--macro',type=Path,required=True);cmd.add_argument('--out',type=Path,required=True);args=cmd.parse_args()
    with tempfile.TemporaryDirectory()as tmp:evaluate(args,Path(tmp))
