"""Register the Shanghai Sports Hall and check the two adjacent street properties."""
import argparse
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np
import shapely as geo

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha


def park_envelope(site,review):
    """Bound the complete published Park Hotel model in the Sports Hall frame."""
    key='projects/shanghai/data/candidate-city-integrations.json'
    catalog=json.loads(subprocess.check_output(['git','show',review['baseline_commit']+':'+key],cwd=site.project.parents[1]))
    hotel=next(m for m in catalog['models'] if m['id']=='huangpu-park-hotel')
    assert hotel['owner']['feature_local_id']==1138
    h=math.radians(hotel['heading']);k=6371008.8*math.cos(math.radians(hotel['lat']))
    bounds=hotel['bounds_glb'];points=[]
    for x,z in [(bounds[a][0],bounds[b][2]) for a,b in [('min','min'),('max','min'),('max','max'),('min','max')]]:
        east=x*math.cos(h)-z*math.sin(h);north=-x*math.sin(h)-z*math.cos(h)
        lng=hotel['lng']+math.degrees(east/k)
        lat=math.degrees(math.atan(math.sinh(math.asinh(math.tan(math.radians(hotel['lat'])))+north/k)))
        points.append([lng,lat])
    return hotel,geo.Polygon(site.to_xy(np.asarray(points)))


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--manifest',type=Path,required=True)
    cli.add_argument('--work',type=Path,required=True)
    cli.add_argument('--out',type=Path,default=Path(__file__).resolve().parent)
    args=cli.parse_args();project=Path(__file__).resolve().parents[3];ident='huangpu-foreign-ymca';owner=2846
    review=read(project/'source/precise'/ident/'footprint-review.json');site=PlacementMeshes(project,args.work,review)
    assets,bounds,model,ground=site.decode_model(args.manifest)
    source=site.footprints[owner];mask=source.buffer(.55,join_style='mitre')
    assert len(mask.exterior.coords)==5
    tested={}
    for nearby in [owner,1138]:
        group=next(g for g in review['near_tiles'] if nearby in g['feature_local_ids'])
        for role,(triangles,others,assignment) in site.decode_group(group,nearby).items():
            body=site.project_faces(triangles);context=site.project_faces(others)
            case={'group':group['id'],'local_id':nearby,'others':group['feature_local_ids'],'triangles':len(triangles),
                  'other_triangles':len(others),'ownership':assignment,'body_area_m2':body.area,
                  'context_clearance_to_model_m':model.distance(context),'context_clearance_to_mask_m':mask.distance(context)}
            assert case['context_clearance_to_model_m']>1 and case['context_clearance_to_mask_m']>1
            if nearby==owner:
                assert geo.covers(mask,geo.multipoints(triangles[:,:,:2].reshape(-1,2)))
                case['source_uncovered_m2']=body.difference(mask).area
                assert case['source_uncovered_m2']<1e-7
            else:
                case['park_source_clearance_to_model_m']=model.distance(body)
                case['park_source_clearance_to_mask_m']=mask.distance(body)
                assert min(case['park_source_clearance_to_model_m'],case['park_source_clearance_to_mask_m'])>1
            tested[f'{nearby}-{role}']=case
    hotel,envelope=park_envelope(site,review);park_clearance=model.distance(envelope)
    assert park_clearance>1 and mask.distance(envelope)>1
    for x in [-3.14,0,3.14]:
        assert not ground.intersects(geo.Point(x,.48)) and ground.contains(geo.Point(x,1.15))
    assert ground.area>850 and source.contains(geo.Point(0,.48))
    clear=sorted((mask.distance(p),model.distance(p),i) for i,p in site.footprints.items() if i!=owner)
    assert min(x[0] for x in clear)>1
    row=next(r for r in review['owners'] if r['local_id']==owner)
    contract={'id':ident,'owner':{'macro_id':review['frozen_macro'],'feature_local_id':owner},'source_feature_ids':{'building':[row['key'][9:]],'building_part':[]},
              'replacement_geometry':site.wgs(mask),'collision_geometry':site.wgs(ground),'lng':site.lon,'lat':site.lat,'heading':review['author_frame']['runtime_heading_deg'],'scale':1,'altitude':0,
              'bounds_glb':bounds,'model_geometry_sha256':{k:v['sha256'] for k,v in assets.items()},'overviewBearing':review['author_frame']['runtime_heading_deg'],'overviewPitch':61,'overviewZoom':18.4,
              'maxDistance':520,'lod_switch_in_m':580,'lod_switch_out_m':745,'navigation':{'listed':False,'status':'沿南京西路观察双翼、中央高拱与砖饰。'},
              'placement':{'status':'estimated','note':'按体育大厦的独立街面边线中点配准。保留旁边的国际饭店实建模型、永新广场及其地面。'},
              'partial_model':True,'model_scope':read(args.manifest)['scope']}
    args.out.mkdir(exist_ok=True,parents=True)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',{'id':ident,'assets':assets,'manifest_sha256':sha(args.manifest),'source_checks':tested,'source_area_m2':source.area,'source_mask_m2':mask.area,'profile_m2':model.area,'collision_m2':ground.area,'mask_margin_m':.55,
          'neighbor_clearances':[{'local_id':i,'mask_m':m,'model_m':d} for m,d,i in clear[:8]],
          'park_hotel':{'id':hotel['id'],'owner':1138,'validated_detailed_model_bbox':hotel['bounds_glb'],'model_sha256':hotel['assets']['web']['sha256'],'raw_vertex_envelope_clearance_m':park_clearance,'mask_to_envelope_m':mask.distance(envelope)},
          'checker_sha256':sha(Path(__file__)),'shared_checker_sha256':sha(project/'tools/candidate_placement_meshes.py')})
    print('Ground and Park Hotel clearance',round(ground.area,2),round(park_clearance,2))

if __name__=='__main__':main()
