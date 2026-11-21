"""Measure the east portico against both original owner-scoped city meshes and the surrounding campus."""
from argparse import ArgumentParser
from pathlib import Path
import sys,runpy
import numpy as np
from shapely.geometry import Point,box
from shapely.ops import unary_union
A=Path(__file__).resolve().parent;P=A.parents[2];sys.path.insert(0,str(P/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,sha,write
from build_candidate_city_integrations import checked_geometry
G=runpy.run_path(str(A.parent/'metropole-hotel-v1/verify-placement.py'))['grouped_sources'];B=runpy.run_path(str(A.parent/'savoy-apartments-v1/verify-placement.py'))['bind_prior']
ID='jingan-ohel-rachel-synagogue';OWNER=1701

def portico_collision(mesh, slab):
    """Keep the sanctuary solid and derive the two standoff columns from their actual lower triangles."""
    clear=box(-3.0,-14.6,3.0,-10.87)
    occupied=[]
    for variant in read(mesh.work/'delivered-decode.json'):
        triangles=np.fromfile(variant['triangle_file'],np.float64).reshape(-1,3,3)
        local=triangles[:,:,[0,2,1]]*[1,-1,1]
        for x in (-1.86,1.86):
            mask=(np.abs(local[:,:,0]-x)<.56).all(axis=1)&(np.abs(local[:,:,1]+12.89)<.56).all(axis=1)&(local[:,:,2].max(axis=1)>.28)&(local[:,:,2].min(axis=1)<1.75)
            assert mask.sum()>30
            outline=mesh.project_faces(local[mask])
            assert .75 < outline.area < .91
            occupied.append(outline)
    result=unary_union([slab.difference(clear),*occupied]).simplify(.012,preserve_topology=True)
    assert result.is_valid and clear.intersection(result).area<1.82 and clear.intersection(slab).area>13.5
    return result

def main():
    p=ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--out',type=Path,default=A);p.add_argument('--previous',type=Path);p.add_argument('--refresh-case',action='store_true');o=p.parse_args();review=read(P/'source/precise'/ID/'footprint-review.json');group=next(g for g in review['near_tiles']if OWNER in g['feature_local_ids']);prior=read(o.previous)if o.previous else {'models':[]}
    if o.refresh_case:
        assert o.previous and sha(o.manifest)==read(o.out/'placement-geometry.json')['manifest_sha256'];write(o.out/'map-case.json',B(read(o.out/'map-case.json'),prior,review['frozen_macro'],group));return
    s=PlacementMeshes(P,o.work,review);assets,bounds,profile,ground=s.decode_model(o.manifest);slab_area=ground.area;ground=portico_collision(s,ground);target={};neighbors={};sources={};ties=[]
    for tile in review['near_tiles']:
        for variant,tri,owners,ambiguity in G(s,tile):
            if variant=='near' and ambiguity.any():ties.append(s.project_faces(tri[ambiguity]))
            for owner in set(owners):
                faces=tri[owners==owner];outline=s.project_faces(faces);sources[(int(owner),variant)]=outline
                if owner==OWNER:target[variant]=dict(original_m2=outline.area,original_height_m=float(faces[:,:,2].max()),triangles=len(faces))
                else:neighbors.setdefault(int(owner),{})[variant]=dict(triangles=len(faces),model_distance_m=profile.distance(outline))
    assert set(target)=={'near','far'};cut=profile.union(sources[(OWNER,'near')]).union(sources[(OWNER,'far')]).envelope.buffer(.045,join_style=2)
    assert cut.covers(profile)and cut.covers(ground)and all(cut.disjoint(g)for g in ties)
    for key,poly in sources.items():
        owner,variant=key
        if owner==OWNER:assert cut.covers(poly)
        else:
            assert cut.disjoint(poly) and ground.disjoint(poly),(key,poly.intersection(cut).area);neighbors[owner][variant].update(cut_distance_m=cut.distance(poly),overlap_m2=0)
    ns=review['retained_neighbors'];assert all(set(neighbors[x])=={'near','far'} for x in ns)
    points=[('large sanctuary',0,0,True),('north wall',8.72,2.45,True),('south wall',-8.72,-2,True),('west end',0,12.7,True),('recessed entrance sill',0,-10.73,True),('east porch between shafts',0,-12.88,False),('behind the south column',-1.86,-11.79,False),('front of north column',1.86,-13.71,False),('south freestanding Ionic shaft',-1.86,-12.89,True),('north freestanding Ionic shaft',1.86,-12.89,True),('north oculus pier',5.91,-12.74,True),('south oculus pier',-5.91,-12.74,True),('court outside portico',0,-14.13,False),('south campus garden',-9.78,0,False),('north campus garden',9.78,0,False),('outside west wall',0,14.1,False)]
    probes=[]
    for name,x,y,expected in points:
        pt=Point(x,y);assert ground.covers(pt)==expected,(name,ground.distance(pt));probes.append(dict(name=name,xy=[x,y],modelObstacle=expected,cut=cut.covers(pt),expected='building'if expected else None))
    c=dict(id=ID,owner=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER),source_feature_ids={'building':[review['owner']['source_key'][9:]],'building_part':[]},lng=s.lon,lat=s.lat,heading=review['author_frame']['runtime_heading_deg'],altitude=0,scale=1,bounds_glb=bounds,model_geometry_sha256={k:v['sha256']for k,v in assets.items()},replacement_geometry=s.wgs(cut),collision_geometry=s.wgs(ground),overviewBearing=-100,overviewPitch=47,overviewZoom=19.0,maxDistance=1250,lod_switch_in_m=850,lod_switch_out_m=1100,navigation={'listed':False,'status':'从院内东侧观看会堂入口、双柱和拱窗。'},placement={'status':'estimated','note':'按市登记2B014、实照和OSM具名主体206515891第5版，定位院内会堂1701。净距、窗门细部和非测绘高度以照片估算。'},partial_model=False,model_scope=read(o.manifest)['scope'])
    for field in ['replacement_geometry','collision_geometry']:checked_geometry(c[field],field,collision=field=='collision_geometry')
    case=dict(id=ID,addedTriangles=2,ground=probes,neighbors=ns,neighborGround={i:s.wgs(s.footprints[i].representative_point())['coordinates']for i in ns},front=dict(center=[0,-9.6],bearingOffset=8,elevation=4.7,pitch=69,zoom=20.65),roof=dict(center=[0,0],bearingOffset=25,elevation=6.7,pitch=49,zoom=20.25));write(o.out/'map-case.json',B(case,prior,review['frozen_macro'],group));write(o.out/'final-placement-contract.json',c);write(o.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(o.manifest),contract_sha256=sha(o.out/'final-placement-contract.json'),assets=assets,original_levels=target,neighbors=neighbors,local_cut_bbox=list(cut.bounds),cut_m2=cut.area,all_height_projection_m2=profile.area,ground_m2=ground.area,slab_projection_before_portico_m2=slab_area,ground_probes=probes));print(target,'ground',ground.area,'cut',cut.area,flush=True)
if __name__=='__main__':main()
