"""Verify the concave seven-plane Development Building street front and each adjacent city mesh."""
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

ID='huangpu-development-building'
OWNER=2551


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=HERE)
    parser.add_argument('--previous',default='huangpu-chung-wei-bank-building')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,review)
    assets,bounds,model,ground=site.decode_model(args.manifest)
    edges=np.array([[-17.67,-.39],[-12.06,-5.70],[-5.16,-.66],[-3.23,-.14],[1.83,-.15],[3.87,-1.12],[9.83,-5.70],[16.18,1.02]])
    depth=np.array([4.35,4.85,3.55,2.78,2.78,3.55,4.85,4.35])
    along=np.diff(edges,axis=0);along/=np.linalg.norm(along,axis=1)[:,None]
    normals=np.column_stack([-along[:,1],along[:,0]])
    def parallel_chain(width):
        chain=[edges[0]+width[0]*normals[0]]
        for i in range(1,len(edges)-1):
            bisector=normals[i-1]+normals[i]
            chain.append(edges[i]+width[i]*bisector/(bisector@normals[i]))
        return np.array([*chain,edges[-1]+width[-1]*normals[-1]])
    rear=parallel_chain(depth+.11);front=parallel_chain(np.full(8,-.55))
    for chain in [rear,front]:
        chain[0]-=.025*along[0];chain[-1]+=.025*along[-1]
    mask=geo.Polygon([*front,*reversed(rear)])
    center=(edges[3]+edges[4])/2
    def portal_point(x,y):
        return center+along[3]*x+normals[3]*y
    portal=geo.Polygon([portal_point(x,y)for x,y in [(-1.62,-.5),(1.62,-.5),(1.62,.98),(-1.62,.98)]])
    collision=geo.Polygon([*edges,*reversed(parallel_chain(depth))]).difference(portal)
    assert mask.covers(model) and mask.covers(collision),(model.difference(mask).area,collision.difference(mask).area)
    original=site.footprints[OWNER]
    group=next(row for row in review['near_tiles']if OWNER in row['feature_local_ids'])
    source={};seams={};ids=group['feature_local_ids']
    assert ids[0]==OWNER and set(ids)=={2551,1908,2642,1415,1844}
    grouped=runpy.run_path(str(PROJECT/'data/audit/metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    for variant,tr,assigned,ties in grouped(site,group):
        own=tr[assigned==OWNER];certified=np.zeros(len(tr),dtype=bool);above_count=vertex_count=0
        if variant=='near':
            centroids=geo.points(tr[:,:,:2].mean(1))
            inside=geo.contains(site.footprints[1908].buffer(-.55),centroids)
            neighbor_roof=float(tr[inside,:,2].max());assert abs(neighbor_roof-24.6)<.04
            # Party-wall triangles whose centroids cannot distinguish the two owners
            # are kept unless their height or all three vertices identify the tower.
            near=np.flatnonzero(ties & geo.intersects(geo.polygons(tr[:,:,:2]),mask))
            points=geo.points(tr[near,:,:2].reshape(-1,2))
            distances=np.stack([geo.distance(points,site.footprints[i]).reshape(-1,3).max(1)for i in ids],axis=1)
            above=tr[near,:,2].min(1)>neighbor_roof+.20
            inside_tower=distances[:,0]<.001
            unique_foot=distances[:,1:].min(1)>.43
            # The only other tall source in this group is across the street.
            assert all(mask.distance(site.footprints[i])>12 for i in ids if i not in (OWNER,1908))
            certified[near]=inside_tower & (above|unique_foot) & (assigned[near]==OWNER)
            assert certified[near].all()
            above_count=int(above.sum());vertex_count=int((unique_foot&~above).sum())
        else:
            neighbor_roof=float(tr[assigned==1908,:,2].max());assert abs(neighbor_roof-24.6)<.04
        other=tr[(assigned!=OWNER)|(ties & ~certified)]
        adjacent=site.project_faces(other);foot=site.project_faces(own)
        assert mask.disjoint(adjacent) and model.disjoint(adjacent)
        crossing=foot.intersection(mask.boundary).simplify(.012)
        assert crossing.geom_type=='LineString';seams[variant]=crossing
        retained=foot.difference(mask).area/foot.area;assert .55<retained<.60
        source[variant]=dict(retained_percent=100*retained,original_area_m2=foot.area,cut_area_m2=foot.intersection(mask).area,coarse_roof_m=float(own[:,:,2].max()),neighbor_1908_roof_m=neighbor_roof,protected_faces=len(other),owner_faces=len(own),source_section_length_m=crossing.length,source_section_segments=len(crossing.coords)-1,cut_to_protected_faces_m=mask.distance(adjacent),model_to_protected_faces_m=model.distance(adjacent),ambiguous_protected=int((ties&~certified).sum()),certified_above_neighbor=above_count,certified_by_three_vertices=vertex_count)
    assert seams['near'].hausdorff_distance(seams['far'])<.13
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
            independent.append(dict(variant=variant,triangles_preserved=len(triangles),mask_clearance_m=mask.distance(mesh),group=group['id']))
    ready=read(site.files['READY.json']);heading=review['author_frame']['runtime_heading_deg']
    owner=next(r for r in review['owners']if r['local_id']==OWNER)
    own=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER)
    c=seams['far'];pairs=[(a,b)for a,b in zip(list(c.coords),list(c.coords)[1:])]
    contract=dict(id=ID,owner=own,source_feature_ids=dict(building=[owner['key'][9:]],building_part=[]),lng=site.lon,lat=site.lat,heading=heading,scale=1,altitude=0,bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(collision),source_section_caps=dict(geometry=site.wgs(geo.MultiLineString(pairs)),base_m=0,roof_m=source['far']['coarse_roof_m'],height_reference=[ready['origin_longitude'],ready['origin_latitude']],far_sha256=sha(site.files['far.glb'])),
        overviewBearing=213,overviewPitch=42,overviewZoom=18.93,maxDistance=660,lod_switch_in_m=560,lod_switch_out_m=780,navigation=dict(listed=False,status='江西中路福州路口建设大楼面向街心的塔楼、转角与入口。'),placement=dict(status='estimated',note='按街心凹入弧段及外侧两截街墙配准。工程高度67.97米，原57.6米办公体量保留在界面之后，东西两侧独立邻楼保留。'),partial_model=True,model_scope=read(args.manifest)['scope'])
    for field in ['replacement','collision']:checked_geometry(contract[field+'_geometry'],field,collision=field=='collision')
    neighbors=[1908,1844,2805,358,1554]
    samples=[('public plaza',-.70,-2,False),('plaza outside black portal',-.70,-.30,False),('inside granite portal',-.70,.50,False),('closed recessed glazing',-.70,.91,True),('black granite jamb',1.15,.20,True),('left shoulder',-9.46,-2.65,True),('right shoulder',8.50,-2.7,True),('low return',-14.9,-.6,True),('retained original offices',0,5.15,True)]
    ground_case=[]
    for label,x,y,solid in samples:
        q=geo.Point(x,y);occ=collision.covers(q);cut=mask.covers(q);assert (occ if cut else original.covers(q))==solid,label
        ground_case.append(dict(name=label,xy=[x,y],expected='building'if solid else None,modelObstacle=bool(occ),cut=bool(cut)))
    hamilton=read(PROJECT/'data/audit/hamilton-house-v1/final-placement-contract.json')
    old_triangles=len(hamilton['replacement_geometry']['coordinates'][0])-3
    tris=len(mask.exterior.coords)-3
    case=dict(id=ID,previous=args.previous,neighbors=neighbors,existingGroupOwners=[1844],existingCandidateOwners=[1844,2805,358],adjacentModel='huangpu-hamilton-house',groupTriangles=tris+old_triangles,addedTriangles=tris,sourceSectionCount=len(pairs),front=dict(center=[0,0],elevation=22.5,pitch=36,zoom=19.25,bearingOffset=205-heading),roof=dict(center=[0,1.3],elevation=56,pitch=29,zoom=19.0,bearingOffset=222-heading),ground=ground_case,neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates']for i in neighbors})
    write(args.out/'map-case.json',case);write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),assets=assets,source=source,independent_groups=independent,full_height_cut_m2=mask.area,modeled_ground_obstacle_m2=collision.area,ground=ground_case,checker_sha256=sha(Path(__file__)),shared_checker_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))
if __name__=='__main__':main()
