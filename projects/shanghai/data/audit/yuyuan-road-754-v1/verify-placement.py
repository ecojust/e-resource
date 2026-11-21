"""Compare the lane residence with the actual owner-scoped near and far urban meshes."""
import argparse
from pathlib import Path
import sys
import tempfile

from shapely.geometry import LineString, MultiLineString, Point, box
from shapely.ops import unary_union

AUDIT=Path(__file__).resolve().parent
PROJECT=AUDIT.parents[2]
SOURCE=PROJECT/'source/precise/changning-yuyuan-road-754'
OWNER=277
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
    # The survey-defined front meets the east end of the 26 m-deep coarse extrusion.
    # Retain its western remainder and close only the exposed source roof/wall seam.
    seam_depth=15.16
    source_hull=unary_union([source_plan,*native.values()]).convex_hull.buffer(.2,join_style='mitre')
    cut=source_hull.intersection(box(-18,-5,18,seam_depth))
    collision=unary_union([box(-2.16,0,2.16,4.95),box(-5.12,4.95,1.84,11.58),
                           box(-5.52,11.58,1.84,15.12),box(-4.97,4.92,-2.10,6.01)])
    # Gates and boundary only occupy their actual narrow ground-contact strips.
    posts=[(-4.48,-1.61),(-2.28,-1.38),(1.39,-1.48),(3.62,-1.02)]
    wall_lines=[LineString([(-5.37,1.05),posts[0]]),LineString([posts[1],posts[2]]),
                LineString([posts[3],(3.64,7.36)])]
    pieces=[collision,*[line.buffer(.08,cap_style='flat')for line in wall_lines],
            *[box(x-.16,y-.16,x+.16,y+.16)for x,y in posts]]
    for i in [0,2]:
        pieces.append(LineString([posts[i],posts[i+1]]).buffer(.035,cap_style='flat'))
    collision=unary_union(pieces)
    residual={};summaries={}
    for name,(target,others,assign)in group.items():
        before=native[name];residual[name]=before.difference(cut)
        nearby=mesh.project_faces(others)
        untouched=nearby.intersection(cut).area
        assert untouched<.002,(name,untouched)
        ratio=residual[name].area/before.area
        assert .36<ratio<.72,(name,ratio)
        summaries[name]=dict(original_m2=before.area,retained_m2=residual[name].area,
              retained_fraction=ratio,other_mesh_cut_m2=untouched,other_mesh_clearance_m=nearby.distance(cut),
              other_meshes_model_overlap_m2=nearby.intersection(ground).area,matched_triangles=len(target),
              other_group_triangles=len(others),source_height_m=target[:,:,2].max(),assignment=assign)
    neighbors={i:g for i,g in mesh.footprints.items() if i!=OWNER and g.distance(cut)<30}
    gaps={i:dict(cut_clearance_m=g.distance(cut),model_clearance_m=g.distance(collision),
                 cut_overlap_m2=g.intersection(cut).area,model_overlap_m2=g.intersection(collision).area)
          for i,g in neighbors.items()}
    assert all(g['cut_overlap_m2']<.001 and g['model_overlap_m2']<.001 for g in gaps.values()),gaps
    assert 2870 in gaps and 356 in gaps
    line=LineString([(-18,seam_depth),(18,seam_depth)])
    seams={role:geom.intersection(line)for role,geom in native.items()}
    assert all(v.geom_type=='LineString'and 6.5<v.length<10 for v in seams.values())
    assert seams['near'].hausdorff_distance(seams['far'])<.65
    ready=read(args.macro/'READY.json')
    cap=dict(geometry=mesh.wgs(MultiLineString([seams['far']])),base_m=0,
             roof_m=summaries['far']['source_height_m'],height_reference=[ready['origin_longitude'],ready['origin_latitude']],far_sha256=ready['far']['sha256'])
    spots=[]
    def check(name,xy,hit,owner=None):
        pos=Point(xy);clipped=cut.covers(pos);assert collision.covers(pos)==hit,(name,xy)
        if owner:assert mesh.footprints[owner].covers(pos) and not clipped
        spots.append(dict(name=name,xy=list(xy),modelObstacle=hit,cut=clipped,
                 expected='building'if hit or owner else None,**({'ownerLocalId':owner}if owner else {})))
    for name,x,y in [('inside low arched room',0,1.0),('stepped shoulder',-2.8,6),('rear wing',0,13),('green 754 gate post',-4.48,-1.61),('north front post',3.62,-1.02)]:
        check(name,(x,y),True)
    for name,x,y in [('public lane east of gate',0,-3.35),('court before arch',0,-.64),('clear southern gate approach',-3.4,-2.40),('open north court',2.91,2.84),('lane clear of north wall',4.85,-1)]:
        check(name,(x,y),False)
    old=residual['far'].intersection(residual['near']).intersection(source_plan).representative_point()
    check('retained western part of old 277',(old.x,old.y),False,OWNER)
    for i in [2870,356,2243]:
        pos=mesh.footprints[i].representative_point();check('neighbor '+str(i),pos.coords[0],False,i)
    fr=source['author_frame'];cam=read(SOURCE/'camera-preflight.json');m=read(args.manifest)
    contract=dict(id=m['id'],**fr['anchor'],heading=fr['runtime_heading_deg'],scale=1,altitude=0,
        owner={'macro_id':source['frozen_macro'],'feature_local_id':OWNER},
        source_feature_ids={'building':[source['owner']['source_key'].split(':')[-1]],'building_part':[]},
        replacement_geometry=mesh.wgs(cut),collision_geometry=mesh.wgs(collision),bounds_glb=bounds,
        source_section_caps=cap,model_geometry_sha256={k:r['sha256']for k,r in assets.items()},
        overviewBearing=cam['recommendation'][1]%360,overviewPitch=cam['recommendation'][2],overviewZoom=19.6,
        lod_switch_in_m=500,lod_switch_out_m=660,maxDistance=460,
        navigation={'listed':False,'status':'从里弄观察754号院门、弧纹低房与后部阳台。'},
        placement={'status':'estimated','note':'院门黄牌和多个独立拍摄点定位住宅。保留2870及医院、750弄排屋，277只裁东段；院中空地和里弄通行。后部进深、层高及无照片屋面为估计。'},
        partial_model=True,model_scope=m['model_scope_zh'])
    for key in ['replacement_geometry','collision_geometry']:checked_geometry(contract[key],key,collision=key=='collision_geometry')
    args.out.mkdir(exist_ok=True,parents=True)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'footprint-review.json',dict(id=m['id'],asset_sha256={k:v['sha256']for k,v in assets.items()},
          source_sha256=sha(SOURCE/'footprint-review.json'),script_sha256=sha(Path(__file__)),source=source['owner'],
          near_group=tile,far_and_near=summaries,neighbors=gaps,ground=spots,cut_m2=cut.area,
          collision_m2=collision.area,ground_outside_collision_m2=ground.difference(collision).area,
          original_277_m2=source_plan.area,residual_seam_length_m={k:v.length for k,v in seams.items()}))
    print('Verified clipped owner',OWNER,'and',len(neighbors),'unaffected nearby buildings;',len(spots),'ground probes.',flush=True)


if __name__=='__main__':
    cmd=argparse.ArgumentParser(description=__doc__);cmd.add_argument('--manifest',type=Path,required=True)
    cmd.add_argument('--macro',type=Path,required=True);cmd.add_argument('--out',type=Path,required=True);args=cmd.parse_args()
    with tempfile.TemporaryDirectory()as tmp:evaluate(args,Path(tmp))
