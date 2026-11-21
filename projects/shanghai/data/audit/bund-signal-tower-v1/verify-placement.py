"""Decode the delivered station and both native city mesh levels before registering its present location."""
from argparse import ArgumentParser
from pathlib import Path
import sys,runpy
from shapely.geometry import Point,box
A=Path(__file__).resolve().parent;P=A.parents[2];sys.path.insert(0,str(P/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,sha,write
from build_candidate_city_integrations import checked_geometry
G=runpy.run_path(str(A.parent/'metropole-hotel-v1/verify-placement.py'))['grouped_sources'];B=runpy.run_path(str(A.parent/'savoy-apartments-v1/verify-placement.py'))['bind_prior']
ID='huangpu-bund-signal-tower';OWNER=589

def main():
    p=ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--out',type=Path,default=A);p.add_argument('--previous',type=Path);p.add_argument('--refresh-case',action='store_true');o=p.parse_args();review=read(P/'source/precise'/ID/'footprint-review.json');group=next(g for g in review['near_tiles']if OWNER in g['feature_local_ids']);prior=read(o.previous)if o.previous else {'models':[]}
    if o.refresh_case:
        assert o.previous and sha(o.manifest)==read(o.out/'placement-geometry.json')['manifest_sha256'];write(o.out/'map-case.json',B(read(o.out/'map-case.json'),prior,review['frozen_macro'],group));return
    s=PlacementMeshes(P,o.work,review);assets,bounds,profile,ground=s.decode_model(o.manifest);target={};neighbors={};sources={};ties=[]
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
    points=[('southern doorway',0,-9.87,True),('street before doorway',0,-10.87,False),('western room',-2,-4,True),('eastern room',2,-3,True),('station centre',0,0,True),('tower under mast',0,6.35,True),('round north doorway',0,9.92,True),('northern quay',0,10.56,False),('clear east of tower',4.40,6.35,False),('clear west of tower',-4.40,6.35,False),('river side of station',4.54,-3.18,False),('road side of station',-4.7,-4.6,False),('outside south eave',3.96,-9.74,False)]
    probes=[]
    for name,x,y,expected in points:
        pt=Point(x,y);assert ground.covers(pt)==expected,(name,ground.distance(pt));probes.append(dict(name=name,xy=[x,y],modelObstacle=expected,cut=cut.covers(pt),expected='building'if expected else None))
    c=dict(id=ID,owner=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER),source_feature_ids={'building':[review['owner']['source_key'][9:]],'building_part':[]},lng=s.lon,lat=s.lat,heading=review['author_frame']['runtime_heading_deg'],altitude=0,scale=1,bounds_glb=bounds,model_geometry_sha256={k:v['sha256']for k,v in assets.items()},replacement_geometry=s.wgs(cut),collision_geometry=s.wgs(ground),overviewBearing=-68,overviewPitch=52,overviewZoom=18.6,maxDistance=1250,lod_switch_in_m=850,lod_switch_out_m=1100,navigation={'listed':False,'status':'从江边观看移建后的站房、圆塔和信号横桁。'},placement={'status':'estimated','note':'市登记2A011及现场铭牌定位在1993年东南平移后的外滩江边，号杆与立面尺度据实照估算。'},partial_model=False,model_scope=read(o.manifest)['scope'])
    for field in ['replacement_geometry','collision_geometry']:checked_geometry(c[field],field,collision=field=='collision_geometry')
    case=dict(id=ID,addedTriangles=2,ground=probes,neighbors=ns,neighborGround={i:s.wgs(s.footprints[i].representative_point())['coordinates']for i in ns},front=dict(center=[0,0],bearingOffset=-30,elevation=9.7,pitch=55,zoom=19.15),roof=dict(center=[0,6.35],bearingOffset=-35,elevation=34.4,pitch=48,zoom=20.0));write(o.out/'map-case.json',B(case,prior,review['frozen_macro'],group));write(o.out/'final-placement-contract.json',c);write(o.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(o.manifest),contract_sha256=sha(o.out/'final-placement-contract.json'),assets=assets,original_levels=target,neighbors=neighbors,local_cut_bbox=list(cut.bounds),cut_m2=cut.area,all_height_projection_m2=profile.area,ground_m2=ground.area,ground_probes=probes));print(target,'ground',ground.area,'cut',cut.area,flush=True)
if __name__=='__main__':main()
