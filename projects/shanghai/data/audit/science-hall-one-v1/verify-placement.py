"""Verify the five southern pavilion roofs and open garden gallery against city source 4396."""
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

ID='huangpu-science-hall-building-one'
OWNER=4396


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=HERE)
    parser.add_argument('--previous',default='xuhui-nanyang-campus-gate')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,review)
    assets,bounds,model,ground=site.decode_model(args.manifest)
    mask=geo.Polygon([(-52.19,5.21),(-6.26,5.21),(-6.26,-1.19),(6.26,-1.19),(6.26,5.21),(52.19,5.21),(52.19,14.46),(-52.19,14.46)])
    fields=[(-51.05,-42.90,'end'),(-42.90,-29.34,'range'),(-29.34,-19.93,'inner'),(-19.93,-6.06,'range'),(-6.06,6.06,'clock'),(6.06,19.93,'range'),(19.93,29.34,'inner'),(29.34,42.90,'range'),(42.90,51.05,'end')]
    components=[]
    for left,right,kind in fields:
        mid=(left+right)/2;length=right-left;front=7.34 if kind=='clock'else 8.14
        solid=geo.box(left,front,right,14.27)
        if kind=='clock':
            entry_widths=[(-3.72,1.95),(0,2.88),(3.72,1.95)]
        elif kind=='range':
            entry_widths=[(o,length/3-.42)for o in (-length/3,0,length/3)]
        else:
            half=length*.79/2
            entry_widths=[(-.68*half,.64*half),(0,.60*half),(.68*half,.64*half)]
        for o,width in entry_widths:
            # The windows and glazed doors have actual deep reveals. Whilst moving
            # around the colonnade the closed glazing forms the obstruction.
            solid=solid.difference(geo.box(mid+o-width/2+.052,front-.02,mid+o+width/2-.052,front+.14))
        components.append(solid)
        if kind!='clock':
            components.extend(geo.box(x-.125,6.425,x+.125,6.715)for x in (left+.11,mid,right-.11))
    components.extend(geo.box(x-.165,y-.185,x+.165,y+.185)for x in (-5.65,5.65)for y in (.29,5.47))
    collision=geo.union_all(components).simplify(.003)
    assert mask.covers(model) and mask.covers(collision),(model.difference(mask).bounds,collision.difference(mask).bounds)
    original=site.footprints[OWNER]
    group=next(row for row in review['near_tiles']if OWNER in row['feature_local_ids']);source={};seams={}
    grouped=runpy.run_path(str(PROJECT/'data/audit/metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    for variant,tr,assigned,ties in grouped(site,group):
        protected=tr[(assigned!=OWNER)|ties] if variant=='near' else tr[assigned!=OWNER]
        own=tr[assigned==OWNER];adjacent=site.project_faces(protected);foot=site.project_faces(own)
        assert mask.disjoint(adjacent) and model.disjoint(adjacent)
        crossing=foot.intersection(mask.boundary).simplify(.014)
        assert crossing.geom_type=='MultiLineString'
        seams[variant]=crossing;retained=foot.difference(mask).area/foot.area;assert .56<retained<.61
        source[variant]=dict(retained_percent=100*retained,original_area_m2=foot.area,cut_area_m2=foot.intersection(mask).area,coarse_roof_m=float(own[:,:,2].max()),protected_faces=len(protected),owner_faces=len(own),source_section_length_m=crossing.length,cut_to_protected_faces_m=mask.distance(adjacent),protected_ambiguous=int(ties.sum()))
    assert seams['near'].hausdorff_distance(seams['far'])<.15
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
            independent.append(dict(variant=variant,group=group['id'],triangles_preserved=len(triangles),mask_clearance_m=mask.distance(mesh)))
    ready=read(site.files['READY.json']);heading=review['author_frame']['runtime_heading_deg']
    owner=next(r for r in review['owners']if r['local_id']==OWNER)
    own=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER)
    pairs=[(c,d)for line in seams['far'].geoms for c,d in zip(list(line.coords),list(line.coords)[1:])]
    contract=dict(id=ID,owner=own,source_feature_ids=dict(building=[owner['key'][9:]],building_part=[]),lng=site.lon,lat=site.lat,heading=heading,scale=1,altitude=0,bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(collision),source_section_caps=dict(geometry=site.wgs(geo.MultiLineString(pairs)),base_m=0,roof_m=source['far']['coarse_roof_m'],height_reference=[ready['origin_longitude'],ready['origin_latitude']],far_sha256=sha(site.files['far.glb'])),
        overviewBearing=8,overviewPitch=48,overviewZoom=18.10,maxDistance=650,lod_switch_in_m=570,lod_switch_out_m=780,navigation=dict(listed=False,status='南昌路47号科学会堂一号楼，从花园看向中央露台和五座红瓦亭顶。'),placement=dict(status='estimated',note='依据一号楼实测中央门廊边、五亭照片及三期影像配准，仅替换南园窗廊与可见半坡。北门、端部低平顶和5号楼等独立建筑保留。'),partial_model=True,model_scope=read(args.manifest)['scope'])
    for field in ['replacement','collision']:checked_geometry(contract[field+'_geometry'],field,collision=field=='collision')
    neighbors=[5083,2308,3695,214,5027]
    samples=[('garden lawn',0,-2.5,False),('first garden step',0,-.90,False),('open terrace',0,3,False),('center closed door',0,7.52,True),('free air in front of door',.30,7.15,False),('southwest square column',-5.65,.29,True),('southeast square column',5.65,.29,True),('western glazed portico side',-24.635,6.55,True),('between colonnade posts',21.84,6.55,False),('shaded west gallery',-33.33,7.51,False),('closed west garden window',-33.33,8.70,True),('retained northern building',0,17.3,True),('west flat end retained',-55.5,4.25,True)]
    ground_case=[]
    for label,x,y,solid in samples:
        q=geo.Point(x,y);occ=collision.covers(q);cut=mask.covers(q);assert (occ if cut else original.covers(q))==solid,label
        ground_case.append(dict(name=label,xy=[x,y],expected='building'if solid else None,modelObstacle=bool(occ),cut=bool(cut)))
    tris=len(mask.exterior.coords)-3
    case=dict(id=ID,previous=args.previous,neighbors=neighbors,groupTriangles=tris,addedTriangles=tris,sourceSectionCount=len(pairs),front=dict(center=[0,3.2],elevation=6.2,pitch=40,zoom=18.72,bearingOffset=350-heading),roof=dict(center=[0,7.30],elevation=11.0,pitch=33,zoom=18.40,bearingOffset=351-heading),ground=ground_case,neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates']for i in neighbors})
    write(args.out/'map-case.json',case);write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),assets=assets,source=source,independent_groups=independent,full_height_cut_m2=mask.area,modeled_ground_obstacle_m2=collision.area,ground=ground_case,checker_sha256=sha(Path(__file__)),shared_checker_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))
if __name__=='__main__':main()
