"""Check the measured north façade strip and bevel against both native Shanghai city meshes."""
from argparse import ArgumentParser
from pathlib import Path
import runpy
import sys

import numpy as np
import shapely as geo
from shapely.geometry import Polygon
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

ID='huangpu-yee-tsoong-tobacco-northeast-front'
OWNER=2726


def entrance_cut(a,b,u,width,depth):
    a,b=np.asarray(a),np.asarray(b)
    along=(b-a)/np.linalg.norm(b-a)
    inward=np.array([-along[1],along[0]])
    mid=(a+b)/2+u*along
    p=[mid+along*x+inward*y for x,y in [(-width/2,-.39),(width/2,-.39),(width/2,depth),(-width/2,depth)]]
    return Polygon(p)


def main():
    ap=ArgumentParser(description=__doc__)
    ap.add_argument('--manifest',type=Path,required=True)
    ap.add_argument('--work',type=Path,required=True)
    ap.add_argument('--out',type=Path,default=HERE)
    ap.add_argument('--previous',default='huangpu-royal-asiatic-society-huqiu-front')
    args=ap.parse_args()
    src=PROJECT/'source/precise'/ID
    sys.path.insert(0,str(src/'source'))
    runpy.run_path(str(src/'source/build_model.py'))
    from north_front import EAST_STOP,EAST_NORTH,NORTH_EAST,WEST,OUTLINE,WING_WIDTH
    review=read(src/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,review)
    assets,bounds,model,decoded_ground=site.decode_model(args.manifest)
    # The frozen footprint has a right-angle corner. Remove its urban corner
    # wedge as well as the narrow street band to expose the photographed bevel.
    mask=Polygon([(-22.77,-1.11),(22.05,-1.11),(22.05,3.44),(-16.87,3.44),
                  (-18.25,4.86),(-18.25,9.14),(-22.77,9.14)])
    assert mask.buffer(.02).covers(model),(model.difference(mask).bounds,model.bounds)
    original=site.footprints[OWNER]
    left=NORTH_EAST[0]+WING_WIDTH;right=WEST[0]-WING_WIDTH
    pitch=(right-left)/7
    doors=[(EAST_STOP,EAST_NORTH,0,1.95,.30),(EAST_NORTH,NORTH_EAST,0,1.83,.30),
           (NORTH_EAST,(left,0),0,2.10,.30),((right,0),WEST,-.245,1.15,.30),
           ((left,0),(right,0),2*pitch,pitch-1.09,.44)]
    ground=OUTLINE.buffer(.105,join_style=2).difference(unary_union([entrance_cut(*args)for args in doors]))
    assert ground.is_valid and mask.covers(ground)
    # Direct geometry confirms that there is floor at the new door and nothing
    # left in the clipped-off former rectangle at the northeast footway.
    assert decoded_ground.covers(geo.Point(-19.91,1.83))
    assert not decoded_ground.covers(geo.Point(-21.1,.49))
    neighbors=[1245,2591,3160,2457,778,1599,2770]
    assert min(mask.distance(site.footprints[i])for i in neighbors)>3
    group=review['near_tiles'][0]
    meshes=site.decode_group(group,OWNER)
    results={}
    for kind,(own,other,assignment) in meshes.items():
        source=site.project_faces(own);peers=site.project_faces(other)
        gap=mask.distance(peers);assert gap>3
        roof_z=float(own[:,:,2].max());assert 15.5<roof_z<16.9,roof_z
        after=source.difference(mask)
        assert .79<after.area/source.area<.91
        seams=mask.boundary.intersection(source.buffer(-.025)).simplify(.006)
        lines=list(seams.geoms) if seams.geom_type=='MultiLineString' else [seams]
        assert all(line.geom_type=='LineString' for line in lines)
        results[kind]=dict(group=group['id'],source_group_owners=group['feature_local_ids'],source_triangles=len(own),peer_triangles=len(other),
            assignment=assignment,source_projected_area_m2=source.area,source_projected_retained_m2=after.area,
            retained_percent=after.area/source.area*100,original_roof_height_m=roof_z,model_distance_to_peers_m=model.distance(peers),
            cut_distance_to_peers_m=gap,seams_xy=[list(map(list,line.coords))for line in lines])
        if kind=='far':far_lines=lines;far_roof=roof_z
    ready=read(site.files['READY.json'])
    caps=dict(geometry=site.wgs(geo.MultiLineString(far_lines)),base_m=0,roof_m=far_roof,
              height_reference=[ready['origin_longitude'],ready['origin_latitude']],far_sha256=sha(site.files['far.glb']))
    heading=review['author_frame']['runtime_heading_deg']
    own=next(r for r in review['owners']if r['local_id']==OWNER)
    contract=dict(id=ID,owner=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER),
        source_feature_ids=dict(building=[own['key'][9:]],building_part=[]),replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(ground),
        source_section_caps=caps,lng=site.lon,lat=site.lat,heading=heading,altitude=0,scale=1,bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},overviewBearing=heading+18,overviewPitch=47,overviewZoom=19.57,
        maxDistance=535,lod_switch_in_m=390,lod_switch_out_m=515,navigation=dict(listed=False,status='从南苏州路看七道长券窗和东北抹角门。'),
        placement=dict(status='estimated',note='3A010及关系21785079等同址材料核实原件2726。修正北面与东北真实抹角，保持185号、虎丘路余翼、后部和内院。'),
        partial_model=True,model_scope=read(args.manifest)['model_scope_zh'])
    for field in ['replacement','collision']:checked_geometry(contract[field+'_geometry'],field,collision=field=='collision')
    samples=[]
    def sample(name,x,y,expected):
        pt=geo.Point(x,y);blocked=ground.covers(pt);assert blocked==expected,(name,blocked,expected)
        neighbor=next((i for i in neighbors if site.footprints[i].covers(pt)),None)
        occupied=neighbor is not None or (original.covers(pt) and not mask.covers(pt))
        row=dict(name=name,xy=[x,y],expected='building'if(blocked or occupied)else None,modelObstacle=blocked,cut=mask.covers(pt))
        if neighbor is not None:row['ownerLocalId']=neighbor
        samples.append(row)
    for a,b,u,width,depth in doors:
        aa,bb=np.array(a),np.array(b);t=(bb-aa)/np.linalg.norm(bb-aa);v=np.array([-t[1],t[0]]);center=(aa+bb)/2+t*u
        for dist,expected in [(-.50,False),(.17,False),(depth+.21,True)]:
            sample(f'door at {center.round(2).tolist()}, offset {dist:.2f}',*(center+v*dist),expected)
    for name,x,y,wanted in [('cut former northeast wedge',-21.06,.63,False),('retained north house threshold',10.,1.8,True),
        ('east corner masonry',-20.0,2.56,True),('north roadside pavement',2.,-2.2,False),('Huqiu roadside pavement',-23.7,7.,False),
        ('original eastern wing',-20.2,15.5,False),('original courtyard and rear',5.1,17.,False),('west neighbor side',25.5,1.4,False)]:
        sample(name,x,y,wanted)
    section_count=sum(len(l.coords)-1 for l in far_lines)
    report=dict(id=ID,assets=assets,manifest_sha256=sha(args.manifest),source_surfaces=results,source_owner=OWNER,
         ground_probes=samples,original_ground_area_m2=original.area,source_ground_retained_m2=original.difference(mask).area,
         mask_m2=mask.area,collision_m2=ground.area,section_segments=section_count,clip_xy=list(mask.exterior.coords),
         native_ne_wedge_released=[-21.06,.63],untouched_neighbors=[dict(local_id=i,original_footprint_to_mask_m=mask.distance(site.footprints[i]))for i in neighbors],
         checker_sha256=sha(Path(__file__)))
    case=dict(id=ID,previous=args.previous,neighbors=neighbors,existingGroupOwners=[2457],existingCandidateOwners=[2457],
              groupTriangles=15,addedTriangles=5,residualCutProbe=[10.,1.8],sourceSectionCount=section_count,ground=samples,
              front=dict(center=[-18.8,1.2],elevation=3.5,pitch=60,zoom=21.2,bearingOffset=19),
              roof=dict(center=[-.3,.10],elevation=14.2,pitch=53,zoom=20.90,bearingOffset=6),
              neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates'] for i in neighbors})
    write(args.out/'final-placement-contract.json',contract);write(args.out/'placement-geometry.json',report);write(args.out/'map-case.json',case)
    print(f'Owner {OWNER}, {report["source_ground_retained_m2"]:.2f} m2 retained, {len(samples)} stations and {section_count} section planes.')


if __name__=='__main__':main()
