"""Check the complete three-wing footprint and its open court against signed city meshes."""
import argparse
from pathlib import Path
import runpy
import sys

import shapely as geo

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
ID='huangpu-jiangnan-historic-general-office'
OWNER=1335
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--work',required=True,type=Path)
    ap.add_argument('--manifest',required=True,type=Path)
    ap.add_argument('--previous',required=True,type=Path)
    ap.add_argument('--out',type=Path,default=HERE)
    ap.add_argument('--bind-only',action='store_true')
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    group=review['near_tiles'][0];macro=review['frozen_macro']
    bind=runpy.run_path(str(HERE.parent/'empire-mansions-v1/verify-placement.py'))['bind_prior']
    if args.bind_only:
        spec=read(args.out/'map-case.json');write(args.out/'map-case.json',bind(spec,read(args.previous),macro,group));return
    site=PlacementMeshes(PROJECT,args.work,review)
    assets,bounds,model,ground=site.decode_model(args.manifest)
    parcel=site.footprints[OWNER]
    mask=parcel.buffer(1.08,join_style='mitre')
    # Projecting sills and floor-level mouldings create a very fine outline on this long facade.
    # A 40 cm tolerance retains both entrance steps and leaves the courtyard open for walking.
    obstacle=ground.simplify(.40,preserve_topology=True)
    assert obstacle.symmetric_difference(ground).area/ground.area<.035
    assert obstacle.hausdorff_distance(ground)<.51
    print('Ground rings',[(len(part.exterior.coords),len(part.interiors)) for part in geo.get_parts(obstacle)],flush=True)
    surfaces={}
    for variant,(own,others,assignment) in site.decode_group(group,OWNER).items():
        original=site.project_faces(own);adjacent=site.project_faces(others)
        residual=original.difference(mask)
        assert residual.area<.025 and mask.distance(adjacent)>2. and obstacle.distance(adjacent)>2.,(variant,residual.area,mask.distance(adjacent))
        surfaces[variant]={'source_triangles':len(own),'original_m2':original.area,'removed_m2':original.intersection(mask).area,'retained_m2':residual.area,'neighbor_clearance_m':mask.distance(adjacent),'source_top_m':float(own[:,:,2].max()),'assignment':assignment}
    neighbors=[766,1001,1013,777,760,388]
    for n in neighbors:assert mask.distance(site.footprints[n])>2. and obstacle.distance(site.footprints[n])>2.
    owner=review['owner'];heading=review['author_frame']['runtime_heading_deg']
    contract=dict(id=ID,lng=site.lon,lat=site.lat,heading=heading,altitude=0,scale=1,bounds_glb=bounds,
                  owner={'macro_id':macro,'feature_local_id':OWNER},source_feature_ids={'building':[owner['source_key'].removeprefix('building:')],'building_part':[]},model_geometry_sha256={k:v['sha256']for k,v in assets.items()},replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(obstacle),overviewBearing=heading,overviewPitch=38,overviewZoom=17.93,maxDistance=1040,lod_switch_in_m=480,lod_switch_out_m=760,
                  navigation={'listed':False,'status':'从龙华东路看两座门廊、南正面小窗与红瓦三翼屋面。'},placement={'status':'estimated','note':'两期航片与原有1335号凹字地块重合，历史办公楼的整个外廓替换底图同栋的22.17米简化体量，保留北院和周围其他建筑。'},partial_model=True,model_scope=read(args.manifest)['model_scope_zh'])
    for k in ('replacement','collision'):checked_geometry(contract[k+'_geometry'],k,collision=k=='collision')
    samples=[]
    for title,x,y,blocked in [('south pavement',0,-22.6,False),('east pavement',20,-20.9,False),('west pavement',-42,-20.8,False),('west porch step',-22,-19.0,True),('east porch step',36.75,-19.,True),('central frontage',1,-15.,True),('west street wing',-32,-8,True),('east street wing',27,-10.,True),('west wing',-39,13.,True),('west return end',-39.,25.,True),('east wing',34.,12.,True),('east return end',34.,27.,True),('courtyard west',-25,15.,False),('courtyard center',0,9.,False),('courtyard east',17.,15.,False),('north entrance to court',0,29.,False),('beyond west gable',-39,31.6,False),('beyond east gable',34,33.4,False)]:
        point=geo.Point(x,y);cut=mask.covers(point);hit=obstacle.covers(point)
        assert hit==blocked,(title,hit,blocked)
        samples.append(dict(name=title,xy=[x,y],expected='building' if blocked else None,modelObstacle=hit,cut=cut))
    spec=dict(id=ID,addedOwners=[OWNER],residualCutProbe=[0.,-9.],neighbors=neighbors,addedTriangles=len(mask.exterior.coords)-3,sourceSectionCount=0,
              front=dict(center=[0.,-15.3],elevation=4.2,pitch=39,zoom=18.05,bearingOffset=.0),roof=dict(center=[0.,4.],elevation=7.1,pitch=32,zoom=17.99,bearingOffset=8.),ground=samples,neighborGround={n:site.wgs(site.footprints[n].representative_point())['coordinates']for n in neighbors})
    write(args.out/'map-case.json',bind(spec,read(args.previous),macro,group));write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,source_owner=OWNER,manifest_sha256=sha(args.manifest),source_surfaces=surfaces,assets=assets,model_plan_m2=model.area,decoded_ground_m2=ground.area,original_ground_m2=parcel.area,summarized_obstacle_m2=obstacle.area,source_ground_retained_m2=parcel.difference(mask).area,neighboring_plot_clearances_m={n:mask.distance(site.footprints[n])for n in neighbors},ground=samples))
    print('Geometry and courtyard',len(samples),'ground samples,',len(neighbors),'neighbors;',[(v,round(r['retained_m2'],4))for v,r in surfaces.items()])

if __name__=='__main__':main()
