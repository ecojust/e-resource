"""Check both source meshes, the retained northern and western house, and the four neighboring owners."""
from argparse import ArgumentParser
from pathlib import Path
import runpy
import sys

import numpy as np
import shapely as geom
from shapely.geometry import LineString, MultiLineString, Point, box

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes, read, sha, write
from build_candidate_city_integrations import checked_geometry

MODEL = 'xuhui-huaihai-road-1634-residence'
OWNER = 2222
GROUPS = runpy.run_path(str(AUDIT.parent/'metropole-hotel-v1/verify-placement.py'))['grouped_sources']
BIND = runpy.run_path(str(AUDIT.parent/'savoy-apartments-v1/verify-placement.py'))['bind_prior']


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=AUDIT)
    parser.add_argument('--previous',type=Path)
    parser.add_argument('--refresh-case',action='store_true')
    a=parser.parse_args()
    review=read(PROJECT/'source/precise'/MODEL/'footprint-review.json')
    group=next(g for g in review['near_tiles'] if OWNER in g['feature_local_ids'])
    previous=read(a.previous) if a.previous else {'models':[]}
    if a.refresh_case:
        assert a.previous and sha(a.manifest)==read(a.out/'placement-geometry.json')['manifest_sha256']
        write(a.out/'map-case.json',BIND(read(a.out/'map-case.json'),previous,review['frozen_macro'],group))
        return
    site=PlacementMeshes(PROJECT,a.work,review)
    assets,bounds,profile,ground=site.decode_model(a.manifest)
    source=site.footprints[OWNER]
    # The clipping rectangle ends at the reconstructed cross sections, leaving
    # the irregular western and northern plan intact in the original mesh.
    # Carry the cut beyond the southern eave to avoid leaving a thin 6.4 m
    # source wall in front of the photographed open veranda.
    cut=box(-4.94,-14.04,9.75,6.34)
    assert cut.covers(profile) and cut.covers(ground)
    near_far={}
    protected={}
    for tile in review['near_tiles']:
        for variant,tri,owners,ties in GROUPS(site,tile):
            if variant=='near' and ties.any():
                assert cut.disjoint(site.project_faces(tri[ties]))
            for ident in sorted(set(owners)):
                faces=tri[owners==ident]
                outline=site.project_faces(faces)
                if ident==OWNER:
                    left=outline.difference(cut)
                    assert 140<left.area<173 and 250<outline.intersection(cut).area<295
                    near_far[variant]=dict(source_area_m2=outline.area,remaining_m2=left.area,
                                           remaining_percent=100*left.area/outline.area,
                                           source_height_m=float(faces[:,:,2].max()))
                    if variant=='far':
                        source_far=outline
                else:
                    assert cut.disjoint(outline) and profile.disjoint(outline),(variant,ident)
                    if ident in review['retained_neighbors']:
                        protected.setdefault(int(ident),{})[variant]=dict(triangles=len(faces),
                            cut_distance_m=cut.distance(outline),cut_overlap_m2=0,model_distance_m=profile.distance(outline))
    assert set(protected)==set(review['retained_neighbors'])
    assert all(set(r)=={'near','far'} for r in protected.values())
    seams=[]
    outline=list(cut.exterior.coords)
    for start,end in zip(outline,outline[1:]):
        for section in geom.get_parts(source_far.intersection(LineString([start,end]))):
            if isinstance(section,LineString) and section.length>.01:
                seams.append(section.simplify(.001))
    ready=read(site.files['READY.json'])
    cap=dict(geometry=site.wgs(MultiLineString(seams)),base_m=0,roof_m=near_far['far']['source_height_m'],
             height_reference=[ready['origin_longitude'],ready['origin_latitude']],far_sha256=sha(site.files['far.glb']))
    points=[('garden before columns',2,-13.95,False),('south gallery plinth',2,-11.91,True),
            ('south gallery floor',2,-10.15,True),('outside east return',9.84,-8,False),
            ('east return base',9.04,-8,True),('east threshold stair',9.37,1.10,True),
            ('middle stair',8.10,1.1,True),('door landing',6.40,1.10,True),
            ('clear beside stair',8.5,2.53,False),('service wing base',8.85,4.4,True),
            ('clear courtyard',11.35,1.13,False),('retained western block',-8.0,5.4,True),
            ('retained northern block',4.2,9.3,True)]
    traits=[]
    for name,x,y,expected in points:
        point=Point(x,y);hit=ground.covers(point);inside=cut.covers(point)
        actual=hit or (not inside and source.covers(point))
        assert actual==expected,(name,actual,expected)
        traits.append(dict(name=name,xy=[x,y],expected='building' if expected else None,modelObstacle=hit,cut=inside))
    ns=review['retained_neighbors'];bearing=-60
    contract=dict(id=MODEL,owner={'macro_id':review['frozen_macro'],'feature_local_id':OWNER},
        source_feature_ids={'building':[review['owner']['source_key'][9:]],'building_part':[]},
        lng=site.lon,lat=site.lat,heading=review['author_frame']['runtime_heading_deg'],altitude=0,scale=1,
        bounds_glb=bounds,model_geometry_sha256={k:v['sha256'] for k,v in assets.items()},
        replacement_geometry=site.wgs(cut),collision_geometry=site.wgs(ground),source_section_caps=cap,
        overviewBearing=bearing,overviewPitch=43,overviewZoom=19.4,maxDistance=650,lod_switch_in_m=550,lod_switch_out_m=720,
        navigation={'listed':False,'status':'从院中观看围廊和两层门口。'},
        placement={'status':'estimated','note':'以市登记2D009和同址OSM足迹定位，红瓦坡屋、方柱与错层门口取自庭院原照。西、北部原城市楼体保留。'},
        partial_model=True,model_scope=read(a.manifest)['scope'])
    for key in ['collision_geometry','replacement_geometry']:
        checked_geometry(contract[key],key,collision=key=='collision_geometry')
    case=dict(id=MODEL,neighbors=ns,addedTriangles=2,sourceSectionCount=sum(len(l.coords)-1 for l in seams),
              front=dict(center=[5,-4],bearingOffset=-39,elevation=3.35,pitch=41,zoom=20.05),
              roof=dict(center=[2,-2],bearingOffset=-44,elevation=4.8,pitch=29,zoom=19.94),
              ground=traits,neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates']for i in ns})
    write(a.out/'map-case.json',BIND(case,previous,review['frozen_macro'],group))
    write(a.out/'final-placement-contract.json',contract)
    write(a.out/'placement-geometry.json',dict(id=MODEL,manifest_sha256=sha(a.manifest),assets=assets,contract_sha256=sha(a.out/'final-placement-contract.json'),
        source_meshes=near_far,protected_neighbors=protected,actual_all_height_projected_m2=profile.area,
        actual_ground_contact_m2=ground.area,model_ground_probes=traits,section_lengths_m=[l.length for l in seams]))
    print(near_far,protected,flush=True)


if __name__=='__main__':
    main()
