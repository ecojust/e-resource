"""Fit the two public street fronts and splayed entrance corner to source 1477, retaining the building behind its front walls."""
from argparse import ArgumentParser
from pathlib import Path
import runpy
import subprocess
import sys

import numpy as np
import shapely as geo

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

ID='huangpu-chekiang-first-commercial-bank'
OWNER=1477


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=HERE)
    parser.add_argument('--previous',default='huangpu-bank-of-taiwan-building')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,review)
    assets,bounds,model,ground=site.decode_model(args.manifest)
    C=np.array([-33.15233,11.16454]);W=np.array([-22.02035,0]);N=np.array([-34.78759,32.15649]);S=np.array([22.02031,0])
    a=np.radians(32);rotation=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])
    origin=np.array([-11.81246,7.38124])
    def model_xy(xy):return (np.asarray(xy)-origin)@rotation.T
    def model_geom(form):return geo.transform(form,model_xy)
    nr=(N-C)/np.linalg.norm(N-C);street=geo.LineString([N+nr*.70,C,W,S+[.75,0]])
    mask=model_geom(geo.union(street.buffer(-.80,single_sided=True,join_style='mitre'),street.buffer(2.57,single_sided=True,join_style='mitre')).simplify(.015))
    ground_strip=geo.LineString([N,C,W,S]).buffer(2.28,single_sided=True,join_style='mitre')
    # Pocket to each set of door leaves. The west portal has 3 shallow entrance steps.
    west_entry=geo.box(-2.14,-.2,2.14,1.32)
    midpoint=C+nr*3.20;inside=np.array([nr[1],-nr[0]])
    north_entry=geo.Polygon([midpoint+nr*d+inside*h for d,h in [(-1.23,-.18),(1.23,-.18),(1.23,.66),(-1.23,.66)]])
    collision=model_geom(ground_strip.difference(geo.union(west_entry,north_entry)))
    assert mask.covers(model) and mask.covers(collision),(mask.covers(model),model.difference(mask).area,mask.covers(collision))
    original=site.footprints[OWNER]
    group=next(row for row in review['near_tiles']if OWNER in row['feature_local_ids']);source={};seams={};resolved_points=[]
    grouped=runpy.run_path(str(PROJECT/'data/audit/metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    for variant,tr,assigned,ties in grouped(site,group):
        resolved=[]
        if variant=='near':
            # Near groups have no per-triangle owner tag. At the eastern party line
            # a slim cornice triangle can have its centre in the neighbouring lot
            # while its tip is almost eleven metres outside that lot. Test all
            # three vertices, then verify the matching explicitly tagged far edge.
            indices=np.flatnonzero(ties)
            vertices=geo.points(tr[indices,:,:2].reshape(-1,2))
            distances=np.column_stack([geo.distance(vertices,site.footprints[i]).reshape(-1,3).max(1)
                                       for i in group['feature_local_ids']])
            target_column=group['feature_local_ids'].index(OWNER)
            own_dist=distances[:,target_column]
            other_dist=np.delete(distances,target_column,axis=1).min(1)
            certified=(own_dist<.16) & (other_dist>1.75)
            for k in np.flatnonzero(certified):
                idx=indices[k];resolved.append(dict(triangle=int(idx),previous_owner=int(assigned[idx]),max_distance_to_owner_m=float(own_dist[k]),min_competing_max_distance_m=float(other_dist[k])))
            resolved_points=tr[indices[certified],:,:2].reshape(-1,2)
            assigned[indices[certified]]=OWNER
            ties[indices[certified]]=False
        protected=tr[(assigned!=OWNER)|ties] if variant=='near' else tr[assigned!=OWNER]
        own=tr[assigned==OWNER];adjacent=site.project_faces(protected);foot=site.project_faces(own)
        assert mask.disjoint(adjacent)
        if variant=='far' and len(resolved_points):
            assert np.all(geo.covers(foot.buffer(.18),geo.points(resolved_points)))
        crossing=foot.intersection(mask.boundary).simplify(.014);assert crossing.geom_type in ('LineString','MultiLineString') and crossing.length>65,crossing.wkt
        seams[variant]=crossing;retained=foot.difference(mask).area/foot.area;assert .65<retained<.94,retained
        source[variant]=dict(three_vertex_owner_resolution=resolved,retained_percent=100*retained,original_area_m2=foot.area,cut_area_m2=foot.intersection(mask).area,coarse_roof_m=float(own[:,:,2].max()),protected_faces=len(protected),owner_faces=len(own),source_section_length_m=crossing.length,source_section_segments=sum(len(line.coords)-1 for line in geo.get_parts(crossing)),cut_to_protected_faces_m=mask.distance(adjacent),protected_ambiguous=int(ties.sum()))
    gap=seams['near'].hausdorff_distance(seams['far']);assert gap<.75, (gap,seams['near'].wkt,seams['far'].wkt)
    independent=[]
    for group in review['near_tiles']:
        if OWNER in group['feature_local_ids']:continue
        site.link('baseline-near.glb.gz',site.files[Path(group['file']).name])
        write(site.work/'context-features.json',[dict(localId=i)for i in group['feature_local_ids']])
        subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
        for variant in ('near','far'):
            triangles=np.fromfile(site.work/('baseline-'+variant+'-triangles.f64'),np.float64).reshape(-1,3,3)
            triangles[:,:,:2]=triangles[:,:,:2]@site.axes.T
            mesh=site.project_faces(triangles)
            assert mask.disjoint(mesh), (variant,mask.intersection(mesh).area)
            independent.append(dict(variant=variant,triangles_preserved=len(triangles),mask_clearance_m=mask.distance(mesh)))
    ready=read(site.files['READY.json']);heading=review['author_frame']['runtime_heading_deg']
    owner=next(r for r in review['owners']if r['local_id']==OWNER)
    own=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER)
    c=seams['far'];pairs=[(a,b)for line in geo.get_parts(c) for a,b in zip(list(line.coords),list(line.coords)[1:])]
    contract=dict(id=ID,owner=own,source_feature_ids=dict(building=[owner['key'][9:]],building_part=[]),lng=site.lon,lat=site.lat,heading=heading,scale=1,altitude=0,bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(collision),source_section_caps=dict(geometry=site.wgs(geo.MultiLineString(pairs)),base_m=0,roof_m=source['far']['coarse_roof_m'],height_reference=[ready['origin_longitude'],ready['origin_latitude']],far_sha256=sha(site.files['far.glb'])),
        overviewBearing=118,overviewPitch=36,overviewZoom=18.93,maxDistance=530,lod_switch_in_m=520,lod_switch_out_m=740,navigation=dict(listed=False,status='江西中路222号西门，汉口路151号北门。'),placement=dict(status='estimated',note='两处入口和斜角的外墙边按冻结1477、现行街边及2019航照定位。三段源背后体块、其余屋面和同组建筑保留。'),partial_model=True,model_scope=read(args.manifest)['scope'])
    for field in ['replacement','collision']:checked_geometry(contract[field+'_geometry'],field,collision=field=='collision')
    neighbors=[2598,1708,2191,406];samples=[('west pavement',0,-1.26,False),('lowest bank step',0,.22,False),('bank landing',0,1.08,False),('closed bank door',0,1.46,True),('west window pier',8.1,.65,True),('retained main block',0,6.1,True)]
    for label,distance,solid in [('north public pavement',-.95,False),('north reveal',.21,False),('closed office door',.79,True)]:
        pos=midpoint+inside*distance;samples.append((label,*pos,solid))
    samples.append(('solid stone north jamb',*(midpoint+inside*.44+nr*1.63),True))
    ground_case=[]
    for label,x,y,solid in samples:
        x,y=model_xy([x,y]);q=geo.Point(x,y);occ=collision.covers(q);cut=mask.covers(q);assert (occ if cut else original.covers(q))==solid,label
        ground_case.append(dict(name=label,xy=[x,y],expected='building'if solid else None,modelObstacle=bool(occ),cut=bool(cut)))
    author_origin=geo.Point(0,0)
    assert original.covers(author_origin) and not mask.covers(author_origin) and not collision.covers(author_origin)
    ground_case.append(dict(name='retained offices at author origin',xy=[0,0],expected='building',modelObstacle=False,cut=False))
    cut_probe=next(row['xy']for row in ground_case if row['name']=='closed bank door')
    tris=len(mask.exterior.coords)-3
    case=dict(id=ID,previous=args.previous,residualCutProbe=cut_probe,neighbors=neighbors,groupTriangles=tris,addedTriangles=tris,sourceSectionCount=len(pairs),front=dict(center=[0,-3],elevation=13.8,pitch=40,zoom=19.04,bearingOffset=116-heading),roof=dict(center=[0,0],elevation=25.0,pitch=28,zoom=18.96,bearingOffset=129-heading),ground=ground_case,neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates']for i in neighbors})
    write(args.out/'map-case.json',case);write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),assets=assets,source=source,near_far_seam_hausdorff_m=gap,independent_groups=independent,full_height_cut_m2=mask.area,modeled_ground_obstacle_m2=collision.area,ground=ground_case,checker_sha256=sha(Path(__file__)),shared_checker_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))

if __name__=='__main__':main()
