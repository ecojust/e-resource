"""Check the actual two city meshes and the photographed Ampire street slice."""
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

ID='huangpu-ampire-and-co-building'
OWNER=1125
NEIGHBORS=[2981,1067,2175]

def main():
    args=argparse.ArgumentParser(description=__doc__)
    args.add_argument('--manifest',type=Path,required=True)
    args.add_argument('--work',type=Path,required=True)
    args.add_argument('--out',type=Path,default=HERE)
    args.add_argument('--previous',default='huangpu-carlowitz-jiujiang-front')
    a=args.parse_args()
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,a.work,review)
    assets,bounds,model,ground=site.decode_model(a.manifest)
    mask=geo.box(-16.30,-1.43,16.24,3.805)
    assert mask.covers(model),model.bounds
    # Use the two curved end wings. The public entry remains open to its recessed door.
    arc=[(2.67*np.sin(v),1.62-2.67*np.cos(v))for v in np.linspace(-np.pi/2,np.pi/2,25)]
    corners=[(x-13.33,y)for x,y in arc]+[(-10.66,0),(10.66,0)]+[(x+13.33,y)for x,y in arc]+[(16,3.76),(-16,3.76)]
    collision=geo.Polygon(corners).difference(geo.box(-.93,-.05,.93,.75))
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
                    assert .70<residual.area/form.area<.88,(variant,form.area,cut_area)
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
        overviewBearing=heading%360,overviewPitch=43,overviewZoom=19.75,maxDistance=1050,lod_switch_in_m=400,lod_switch_out_m=500,
        navigation=dict(listed=False,status='圆明园路97号安培洋行东立面。'),
        placement=dict(status='estimated',note='门牌兴趣点和带名地块1125配对。东侧临街浅切保留原地块后部及北侧115号圆明园公寓。'),
        partial_model=True,model_scope=read(a.manifest)['scope'])
    for field in ('replacement','collision'):checked_geometry(contract[field+'_geometry'],field,collision=field=='collision')
    points=[('pedestrian street',0,-1.09,False),('open threshold',0,.25,False),('within doorway recess',.76,.67,False),
        ('recessed door',0,.80,True),('brick jamb',1.16,.25,True),('north wall',7.12,.41,True),
        ('open frontage ahead of curved wing',15.0,-.75,False),('mass behind curved wing',15.0,3.38,True),
        ('south wing sidewalk',-14,-1.19,False),('retained rear of number 97',.36,5.0,True)]
    probes=[]
    for name,x,y,blocked in points:
        q=geo.Point(x,y);cut=mask.covers(q);occupies=collision.covers(q)
        assert (occupies if cut else site.footprints[OWNER].covers(q))==blocked,name
        probes.append(dict(name=name,xy=[x,y],expected='building'if blocked else None,modelObstacle=bool(occupies),cut=bool(cut)))
    neighbors={i:site.wgs(site.footprints[i].representative_point())['coordinates']for i in NEIGHBORS}
    case=dict(id=ID,previous=a.previous,neighbors=NEIGHBORS,existingGroupOwners=[],existingCandidateOwners=[],
        groupTriangles=2,addedTriangles=2,sourceSectionCount=sum(len(line.coords)-1 for line in seams['far']),front=dict(center=[0,.0],elevation=8.3,pitch=66,zoom=20.1,bearingOffset=0),
        roof=dict(center=[0,.33],elevation=13.9,pitch=35,zoom=20.15,bearingOffset=-15),ground=probes,neighborGround=neighbors)
    write(a.out/'map-case.json',case);write(a.out/'final-placement-contract.json',contract)
    write(a.out/'ground-witnesses.json',dict(points=probes,independent_neighbors=nearby))
    write(a.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(a.manifest),assets=assets,source=source,neighbors=nearby,
        seam_lines=[list(s.coords) for s in seams['far']],footprint_area_m2=collision.area,mask_area_m2=mask.area,checker_sha256=sha(Path(__file__))))
if __name__=='__main__':main()
