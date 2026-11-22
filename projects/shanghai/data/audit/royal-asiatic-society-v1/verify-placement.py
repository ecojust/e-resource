"""Check the actual two city meshes and the historic west front of the Royal Asiatic Society museum."""
import argparse
from pathlib import Path
import runpy
import sys
import subprocess

import numpy as np
import shapely as geo

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes, read, write, sha
from build_candidate_city_integrations import checked_geometry

ID='huangpu-royal-asiatic-society-huqiu-front'
OWNER=2274
NEIGHBORS=[539,3122,2981,1125]

def main():
    args=argparse.ArgumentParser(description=__doc__)
    args.add_argument('--manifest',type=Path,required=True)
    args.add_argument('--work',type=Path,required=True)
    args.add_argument('--out',type=Path,default=HERE)
    args.add_argument('--previous',default='huangpu-electric-company-corner-tower')
    a=args.parse_args()
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,a.work,review)
    assets,bounds,model,ground=site.decode_model(a.manifest)
    half=12.28167895/2
    mask=geo.box(-half-.09,-1.08,half+.09,2.385)
    assert mask.buffer(.0001).covers(model),model.bounds
    # Front thresholds remain walkable to the real grille, 0.21 m behind the stone wall.
    collision=geo.box(-half,0,half,2.34)
    for x in (-2.04,0,2.04):
        collision=collision.difference(geo.box(x-.715,-.01,x+.715,.207))
    assert mask.covers(collision)
    source={};nearby={};seams={}
    all_groups=runpy.run_path(str(PROJECT/'data/audit/metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    for g in review['near_tiles']:
        for variant,tr,assigned,ties in all_groups(site,g):
            for oid in set([OWNER,*NEIGHBORS]).intersection(g['feature_local_ids']):
                own=tr[assigned==oid]
                assert len(own)>0
                form=site.project_faces(own)
                if oid==OWNER:
                    cut_area=form.intersection(mask).area
                    residual=form.difference(mask)
                    assert .85<residual.area/form.area<.98,(variant,form.area,cut_area)
                    seam=form.intersection(mask.boundary).simplify(.025)
                    segments=[seam]if seam.geom_type=='LineString' else list(seam.geoms)
                    seams[variant]=[s for s in segments if s.geom_type=='LineString'and s.length>.04]
                    source[variant]=dict(triangles=len(own),area_m2=form.area,replaced_m2=cut_area,remaining_m2=residual.area,retained_percent=100*residual.area/form.area,coarse_height_m=float(own[:,:,2].max()),seam_total_m=sum(s.length for s in seams[variant]))
                else:
                    assert form.intersection(model).area<.003,(oid,variant,'model intrudes',form.intersection(model).area)
                    assert form.intersection(mask).area<.003,(oid,variant,'cut intrudes',form.intersection(mask).area)
                    nearby.setdefault(str(oid),{})[variant]=dict(triangles=len(own),mask_clearance_m=mask.distance(form),model_clearance_m=model.distance(form),mask_overlap_m2=mask.intersection(form).area)
            if OWNER in g['feature_local_ids']:
                protected=site.project_faces(tr[assigned!=OWNER])
                assert protected.intersection(mask).area<.003,(variant,'other same-group face intersects',protected.intersection(mask).area)
                source[variant]['all_other_group_faces']=int(np.count_nonzero(assigned!=OWNER))
                source[variant]['all_other_group_clearance_m']=protected.distance(mask)
    assert set(source)=={'near','far'} and set(nearby)==set(map(str,NEIGHBORS))
    cap=geo.MultiLineString(seams['far']);heading=review['author_frame']['runtime_heading_deg']
    o=next(v for v in review['owners']if v['local_id']==OWNER);ready=read(site.files['READY.json'])
    contract=dict(id=ID,owner=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER),
        source_feature_ids=dict(building=[o['key'][9:]],building_part=[]),lng=site.lon,lat=site.lat,heading=heading,scale=1,altitude=0,
        bounds_glb=bounds,model_geometry_sha256={k:v['sha256'] for k,v in assets.items()},
        replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(collision),source_section_caps=dict(geometry=site.wgs(cap),
            base_m=0,roof_m=source['far']['coarse_height_m'],height_reference=[ready['origin_longitude'],ready['origin_latitude']],far_sha256=sha(site.files['far.glb'])),
        overviewBearing=heading%360,overviewPitch=37,overviewZoom=20.05,maxDistance=1050,lod_switch_in_m=400,lod_switch_out_m=500,
        navigation=dict(listed=False,status='虎丘路20号原亚洲文会博物院历史门外。'),
        placement=dict(status='estimated',note='虎丘路20号具名地块2274。仅以浅进深细化历史西门，保留原楼后部、博物院广场和紧邻地块。'),
        partial_model=True,model_scope=read(a.manifest)['scope'])
    for field in ('replacement','collision'):checked_geometry(contract[field+'_geometry'],field,collision=field=='collision')
    points=[('Huqiu Road pavement',0,-1.65,False),('west foot of plinth',4.44,-.21,False),
        ('wall beside north octagon',-4.45,.30,True),('wall beside south octagon',4.45,.47,True),
        ('solid pier between door one and two',-1.05,.27,True),('solid pier between door two and three',1.03,.24,True),
        ('inside front section',0,2.08,True),('existing eastern part of museum',0,5.70,True)]
    for x in (-2.04,0,2.04):
        points.extend([(f'street step at {x}',x,-.20,False),(f'behind threshold at {x}',x,.13,False),(f'behind gate at {x}',x,.29,True)])
    probes=[]
    for name,x,y,blocked in points:
        q=geo.Point(x,y);cut=mask.covers(q);occupies=collision.covers(q)
        assert (occupies if cut else site.footprints[OWNER].covers(q))==blocked,name
        probes.append(dict(name=name,xy=[x,y],expected='building'if blocked else None,modelObstacle=bool(occupies),cut=bool(cut)))
    neighbors={i:site.wgs(site.footprints[i].representative_point())['coordinates']for i in NEIGHBORS}
    case=dict(id=ID,previous=a.previous,neighbors=NEIGHBORS,existingGroupOwners=[1125],existingCandidateOwners=[1125],
        groupTriangles=4,addedTriangles=2,sourceSectionCount=sum(len(line.coords)-1 for line in seams['far']),front=dict(center=[0,0],elevation=5.2,pitch=56,zoom=20.50,bearingOffset=-7),
        roof=dict(center=[0,.40],elevation=17.2,pitch=37,zoom=20.3,bearingOffset=-14),ground=probes,neighborGround=neighbors)
    write(a.out/'map-case.json',case);write(a.out/'final-placement-contract.json',contract)
    write(a.out/'ground-witnesses.json',dict(points=probes,independent_neighbors=nearby))
    write(a.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(a.manifest),assets=assets,source=source,neighbors=nearby,
        seam_lines=[list(s.coords) for s in seams['far']],footprint_area_m2=collision.area,mask_area_m2=mask.area,checker_sha256=sha(Path(__file__))))
if __name__=='__main__':main()
