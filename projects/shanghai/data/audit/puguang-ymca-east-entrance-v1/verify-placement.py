"""Place two height-limited facade bands and preserve the native roof, upper additions and vector footprint."""
from argparse import ArgumentParser
from pathlib import Path
import sys
import numpy as np
import shapely as geo
from shapely.geometry import Point,Polygon,box
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry,checked_height_clips
ID='huangpu-puguang-ymca-east-entrance'
OWNER=2382

def verify(args):
    root=PROJECT/'source/precise'/ID
    review=read(root/'footprint-review.json');reg=read(root/'source/frontage-registration.json')
    cut=read(args.cut);assert cut['passed'] and cut['id']==ID and cut['source_review_sha256']==sha(root/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,review)
    decoder=HERE.parent/'mitsui-bussan-pediment-front-v1/decode-texture.cjs'
    site.env['NODE_OPTIONS']=((site.env.get('NODE_OPTIONS') or '')+' --require='+str(decoder)).strip()
    assets,bounds,projection,physical=site.decode_model(args.manifest)
    dom=read(args.manifest);source=site.footprints[OWNER];ready=read(site.files['READY.json'])
    owner=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER)
    ref=[ready['origin_longitude'],ready['origin_latitude']]
    ranges=cut['source_levels']['far']['heights'];near=cut['source_levels']['near']['heights']
    masks=[];geom=[]
    for name,band,low,high in zip(('ground-portal-and-shops','upper-original-window-axes'),reg['height_bands'],ranges,near):
        assert low['range_xyz_m']==high['range_xyz_m']and low['foreign_hits']==high['foreign_hits']==0
        polygon=Polygon(low['mask_local_m']);geom.append(polygon)
        masks.append(dict(id=ID+'-'+name,owner=owner,geometry=site.wgs(polygon),min_height=band['base'],max_height=band['top'],height_reference=ref))
    checked_height_clips(masks,ID)
    # The original unmodified vector polygon still closes the door and shops. The physical
    # model supplies the front edges of the stone plinths and steps outside that footprint.
    ground=geo.union_all([source.intersection(geom[0]),physical],grid_size=.001).simplify(.006,preserve_topology=True)
    assert ground.is_valid and ground.area>18 and ground.difference(source).area>1
    assert abs(ground.area-ground.intersection(geom[0].buffer(.46)).area)<.15
    assert abs(bounds['max'][1]-15.04)<.03
    tests=[]
    for x in [-8.5,-6.9,-4.9,-3.15,-2.04,0,2.05,3.10,4.99,6.98,8.6]:
        for label,y,blocked in [('公共人行道',-1.36,False),('关闭门窗后',.92,True),('保留房体',3.2,True)]:
            q=Point(x,y);model=ground.covers(q);native=source.covers(q);assert (model or native)==blocked,(label,x,y,model,native)
            tests.append(dict(name=label,xy=[x,y],model_obstacle=model,source_obstacle=native,expected_map='building' if blocked else None))
    for x in (-12.6,12.6):
        q=Point(x,1.22);assert source.covers(q)and not ground.covers(q)
        tests.append(dict(name='左右保留店券后',xy=[x,1.22],model_obstacle=False,source_obstacle=True,expected_map='building'))
    for x,z,want in [(0,2,True),(0,7.01,True),(0,12,True),(0,15.1,False),(0,21.9,False),(-8.8,4,True),(-8.8,8,False),(8.8,4,True),(8.8,8,False),(-12.65,4,False),(12.55,2,False)]:
        affected=any(g.covers(Point(x,0)) and b['min_height']<=z<=b['max_height']for g,b in zip(geom,masks))
        assert affected==want
    c=dict(id=ID,owner=owner,source_feature_ids={'building':[],'building_part':[]},replacement_geometry=None,
           display_height_clips=masks,collision_geometry=site.wgs(ground),lng=site.lon,lat=site.lat,heading=reg['runtime_heading_deg'],altitude=0,scale=1,
           model_geometry_sha256={k:v['sha256']for k,v in assets.items()},bounds_glb=bounds,overviewBearing=-107.4,overviewPitch=52,overviewZoom=19.70,
           maxDistance=470,lod_switch_in_m=570,lod_switch_out_m=735,navigation=dict(listed=False,status='沿四川中路看钟门、两侧店券和复原的断山花。'),
           placement=dict(status='map-aligned',note='据4A001名录、具名底图2382及历史和修缮后实照对应门轴。保留原楼后部、整段街墙的其余开间及15.04米以上加层。'),
           partial_model=True,model_scope=dom['scope'])
    checked_geometry(c['collision_geometry'],'closed entrances and physically projecting masonry',collision=True)
    args.out.mkdir(parents=True,exist_ok=True)
    write(args.out/'final-placement-contract.json',c);write(args.out/'placement-geometry.json',
         dict(id=ID,passed=True,original_vector_replaced=False,native_face_ranges=cut['source_levels'],corrected_areas_m2=[g.area for g in geom],
              ground_obstacle_m2=ground.area,model_ground_m2=physical.area,projection_m2=projection.area,ground_probes=tests,
              native_indices_checked=len(review['near_tiles'][0]['feature_local_ids']),source_cut_sha256=sha(args.cut),manifest_sha256=sha(args.manifest),checker_sha256=sha(Path(__file__)),assets=assets))
if __name__=='__main__':
    p=ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--work',type=Path,required=True)
    p.add_argument('--cut',type=Path,default=HERE/'source-cut.json');p.add_argument('--out',type=Path,default=HERE);verify(p.parse_args())
