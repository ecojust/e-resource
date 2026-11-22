"""Register the 522 Jiaozhou Road gate against the measured end of original street building 2100."""
from pathlib import Path
from argparse import ArgumentParser
from contextlib import ExitStack
import gzip,math,os,sys,runpy
import numpy as np
import shapely as geo
from shapely.geometry import Point,LineString,MultiLineString,shape,box
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
MODEL='jingan-gong-residence-jiaozhou-gate'
OWNER=2100
solid_section=runpy.run_path(str(HERE.parent/'sino-french-school-v1/verify-placement.py'))['solid_section']
load_triangles=runpy.run_path(str(HERE.parent/'postal-office-v1/independent-glb-review-helpers.py'))['load_triangles']
line_segments=runpy.run_path(str(HERE.parent/'eye-hospital-building-three-front-v1/verify-placement.py'))['line_segments']
def main():
    arg=ArgumentParser(description=__doc__)
    for k in ('manifest','work','out'):arg.add_argument('--'+k,type=Path,required=True)
    args=arg.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    ref_path=PROJECT/'source/precise'/MODEL/'footprint-review.json';review=read(ref_path)
    site=PlacementMeshes(PROJECT,args.work,review)
    manifest=read(args.manifest);assert manifest['id']==MODEL
    forms=[];sections=[];rec={};bounds=[]
    for delivery,variant,file in [('raw','raw','raw.glb'),('full','web','decoded-full.glb'),('lod','lod','decoded-lod.glb')]:
        geom=manifest['assets'][delivery];assert sha(args.manifest.parent/geom['file'])==geom['sha256']
        tri,_,_,info=load_triangles(args.manifest.parent/file);assert len(tri)==geom['triangles']
        bound=geom['bounds_gltf_m'];bounds.append(bound)
        forms.append(geo.convex_hull(geo.multipoints(tri[:,:,:2].reshape(-1,2))))
        rec[variant]=dict(triangles=len(tri),sha256=geom['sha256'],bytes=geom['bytes'],decoded_sha256=info['sha256'])
        for height in [.085,.098,.115]:sections.append(solid_section(tri,height))
    ground=geo.union_all(sections,grid_size=.00001).simplify(.001,preserve_topology=True)
    form=geo.union_all(forms);mask=box(-2.8,-.14,2.80,4.96)
    assert mask.covers(form) and ground.is_valid
    corridor=box(-1.38,-2,-.13,5.05)
    assert not ground.intersects(corridor)
    results={};tops={};seams={};neighbor_mesh=[]
    # Decode both native city groups; only the known street building is eligible for clipping.
    for grp,owner in zip(review['near_tiles']+review['preserved_near_tiles'],[2100,1778]):
        with ExitStack()as hold:
            for role in ('near','far'):
                for end in ('triangles.f64','owners.u32'):
                    n=args.work/f'baseline-{role}-{end}';fd=os.memfd_create('gong318-city-mesh');hold.callback(os.close,fd);assert not n.is_symlink();n.symlink_to(f'/proc/{os.getpid()}/fd/{fd}');hold.callback(n.unlink)
            native=site.decode_group(grp,owner)
        for role,(own,rest,assign) in native.items():
            src=site.project_faces(own);others=site.project_faces(rest);assert others.distance(mask)>0
            if owner==1778:
                assert src.distance(mask)>.1 and src.distance(corridor)>.15
                neighbor_mesh.append(dict(owner=1778,variant=role,distance_to_mask_m=src.distance(mask),distance_to_walk_m=src.distance(corridor),original_triangles=len(own),other_group_triangles=len(rest),removed=0));continue
            clipped=src.intersection(mask);retained=src.difference(mask)
            touches=np.asarray(geo.intersects(geo.polygons(own[:,:,:2]),mask))
            tops[role]=float(own[touches,:,2].max());seams[role]=line_segments(mask,src)
            assert .70<retained.area/src.area<.84 and retained.distance(corridor)>.1 and 23.80<tops[role]<23.81
            results[role]=dict(assignment=assign,source_triangles=len(own),affected_source_triangles=int(touches.sum()),unchanged_other_group_triangles=len(rest),other_source_distance_m=others.distance(mask),source_projected_m2=src.area,removed_m2=clipped.area,retained_m2=retained.area,retained_percent=100*retained.area/src.area,source_roof_m=tops[role],seam_m=seams[role].length)
            neighbor_mesh.append(dict(owner=owner,variant=role,corridor_clearance_m=retained.distance(corridor),source_material_original_remaining=True))
    gap=seams['far'].hausdorff_distance(seams['near']);assert gap<.2,gap
    ready=read(site.files['READY.json'])
    cap=dict(geometry=site.wgs(seams['far']),base_m=0,roof_m=tops['far'],height_reference=[ready['origin_longitude'],ready['origin_latitude']],far_sha256=sha(site.files['far.glb']))
    probes=[];src=site.footprints[OWNER]
    def record(n,x,y,a,b):
        point=Point(x,y);placed=ground.covers(point);remain=src.covers(point) and not mask.covers(point)
        assert (a,b)==(placed,placed or remain),(n,x,y,a,b,placed,remain)
        probes.append(dict(name=n,xy=[x,y],wgs84=site.to_wgs(np.array([[x,y]]))[0].tolist(),model_obstacle=placed,source_cut=mask.covers(point),expected_map='building'if b else None))
    for y in (-2.,-.5,.10,.55,1.2,2.10,2.55,3.50,4.55,5.05):
        for x in (-1.30,-.75,-.20):record('街边经过左扇自由端向院内通行',x,y,False,False)
    for x in (-2.25,2.25):
        for y in (.08,.37,.72):record('砖门墩底座',x,y,True,True)
    for sign,deg in [(-1,82),(1,7)]:
        for t in np.linspace(.06,.94,6):
            x=3.62*(sign*.487-sign*.48*t*math.cos(math.radians(deg)));y=3.62*(.139+.48*t*math.sin(math.radians(deg)))
            record('开启的左铁扇' if sign<0 else '接近合拢的右铁扇',x,y,True,True)
    for x,y in [(3.2,1.2),(4.2,2.3),(8.,2.6),(11.2,3.2),(12.,4.)]:record('保留的原街边屋身',x,y,False,True)
    neigh=[]
    for i in review['selection']['checked_neighbors']:
        outline=site.footprints[i];assert outline.distance(mask)>0
        c=outline.representative_point();neigh.append(dict(owner=i,source_distance_m=outline.distance(mask),distance_to_gate_m=outline.distance(form),remaining=True,center_wgs84=site.to_wgs(np.array(c.coords))[0].tolist()))
    b=np.array(bounds);cn=dict(id=MODEL,owner=dict(macro_id=review['frozen_macro'],feature_local_id=2100),source_feature_ids={'building':[review['owner']['source_key'][9:]],'building_part':[]},replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(ground),source_section_caps=cap,lng=site.lon,lat=site.lat,heading=review['author_frame']['runtime_heading_deg'],scale=1,altitude=0,model_geometry_sha256={key:v['sha256']for key,v in rec.items()},bounds_glb=dict(min=b[:,0].min(0).tolist(),max=b[:,1].max(0).tolist()),overviewBearing=48.,overviewPitch=57.,overviewZoom=21.5,maxDistance=470,lod_switch_in_m=230,lod_switch_out_m=310,navigation=dict(listed=False,status='从胶州路沿左门扇内侧经拱门进入，接近合拢的右扇按实体阻挡。'),placement=dict(status='estimated',note='由两期四站街景交会定位独立院门。旧街屋2100的北端局部开通，其余街屋和院宅1778保留。'),partial_model=True,model_scope=manifest['scope'])
    checked_geometry(cn['collision_geometry'],MODEL,collision=True);checked_geometry(cn['replacement_geometry'],MODEL)
    write(args.out/'final-placement-contract.json',cn)
    write(args.out/'placement-geometry.json',dict(id=MODEL,passed=True,manifest_sha256=sha(args.manifest),source_sha256=sha(ref_path),contract_sha256=sha(args.out/'final-placement-contract.json'),assets=rec,model_projected_m2=form.area,collision_m2=ground.area,mask_m2=mask.area,source_variants=results,physical_ground_heights_m=[.085,.098,.115],clear_corridor_width_m=1.25,clear_corridor_length_m=7.05,passage_bounds_m=corridor.bounds,retained_other_meshes=neighbor_mesh,cap_segments=len(seams['far'].geoms),cap_near_lod_m=gap,neighbors=neigh,ground_probes=probes))
    print('native',results,'ground',len(probes),'cap',gap,flush=True)
if __name__=='__main__':main()
