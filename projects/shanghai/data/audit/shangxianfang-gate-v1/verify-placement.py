"""Verify the measured gap and keep a pedestrian route through the restored entrance."""
import argparse
import math
import runpy
import subprocess
import sys
from pathlib import Path

import mapbox_vector_tile
import numpy as np
import shapely as geo
from shapely.geometry import LineString, Point, box, shape
from shapely.ops import polygonize, unary_union

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha

ID='huangpu-shangxianfang-gate'
PBF_URL='https://tiles.openfreemap.org/planet/20261115_080022_pt/14/13720/6694.pbf'
PBF_SHA='2cc557168a2d1e041735028eab34d233a0ed2c3bf04497e91cfa92dbf27cb48c'
Reader=runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'


def section(triangles,height):
    crossing=triangles[(triangles[:,:,2].min(1)<height)&(triangles[:,:,2].max(1)>height)]
    lines=[]
    for tri in crossing:
        hits=[]
        for a,b in zip(tri,tri[[1,2,0]]):
            if (a[2]<height)!=(b[2]<height):
                hits.append(a[:2]+(b[:2]-a[:2])*(height-a[2])/(b[2]-a[2]))
        if len(hits)==2 and np.linalg.norm(hits[0]-hits[1])>.0002:
            lines.append(LineString(np.round(hits,5)))
    return unary_union(list(polygonize(unary_union(lines))))


def model_variants(manifest,work):
    doc=read(manifest);variants={};receipts={};bounds=[];footprints=[]
    for role in ('raw','full','lod'):
        a=doc['assets'][role];original=manifest.parent/a['file']
        assert sha(original)==a['sha256'] and original.stat().st_size==a['bytes']
        file=original
        if role!='raw':
            file=work/(role+'.glb')
            subprocess.run(['node',UNPACK,original,file,PROJECT/'vendor/meshopt_decoder.module.js'],check=True,stdout=subprocess.DEVNULL)
        scene=Reader(file);tri=scene.tri;hits=[]
        def ray(label,origin,direction,limit,material=None,distance=None):
            found=scene.ray(origin,direction,limit)
            ok=(found is None) if material is None else (found is not None and found['material']==material and abs(found['distance_m']-distance)<.042)
            hits.append({'name':label,'origin':origin,'direction':direction,'limit_m':limit,'expected_material':material,
                         'expected_distance_m':distance,'actual':found,'passed':ok})
        for u in [-.52,0,.52]:
            for z in [.25,.92,1.62,2.15,2.59]:
                ray('clear line through the entire first row',[u,-1,z],[0,1,0],14.1)
        for y in [1.55,4.70,8.50,10.94]:
            ray('covered lane headroom',[0,y,.05],[0,0,1],4,'passage plaster',3.29)
            ray('continuous paving',[0,y,1.80],[0,0,-1],3,'paving',1.759)
        for x in [-.74,.74]:
            ray('recessed iron gate post at opening',[x,-1,1.55],[0,1,0],3,'dark iron',1.715)
        for x in (-1.67,-.17,1.67):
            ray('lower storey sash beyond wall',[x,-2,5.59],[0,1,0],5,'window glass',2.374)
        for x in (-1.39,1.39):
            ray('upper storey sash to either side of tablet',[x,-2,9.39],[0,1,0],5,'window glass',2.374)
        for sign in (-1,1):
            ray('quoined pilaster',[sign*3.265,-2,7.58],[0,1,0],5,'limestone',1.752)
            ray('passage cheek masonry',[0,5.55,1.6],[sign,0,0],4,'passage plaster',2.77)
        ray('vertical tablet head',[.35,-2,11.13],[0,1,0],4,'limestone',1.59)
        ray('pediment surface above inscription',[.176,-2,12.30],[0,1,0],4,'red-brown brick',1.98)
        ray('next shop remains outside the model',[7.5,5.1,18],[0,0,-1],20)
        slices=unary_union([section(tri,z) for z in (.19,.775,1.60)]).simplify(.013,preserve_topology=True)
        # A person cannot step between 13-22cm spaced steel bars. Include the envelope of each
        # evidenced panel but keep the central gap and the full through-route at pedestrian height.
        panels=[slices.intersection(box(lo,.69,hi,.87)).envelope for lo,hi in ((-2.77,-.68),(.68,2.77))]
        assert all(not part.is_empty for part in panels)
        footprint=unary_union([slices,*panels]).simplify(.013,preserve_topology=True)
        assert LineString([(0,-2),(0,13)]).distance(footprint)>.68
        footprints.append(footprint);bounds.append(np.array(a['bounds_gltf_m']))
        key='web' if role=='full' else role
        receipts[key]={'sha256':a['sha256'],'bytes':a['bytes'],'triangles':len(tri)}
        variants[role]={'triangles':len(tri),'checks':hits,'checked':len(hits),'passed':all(h['passed'] for h in hits)}
    extent=np.array(bounds)
    return variants,receipts,{'min':extent[:,0,:].min(0).tolist(),'max':extent[:,1,:].max(0).tolist()},unary_union(footprints).simplify(.014,preserve_topology=True)


def city_meshes(site,review,envelope):
    out=[];w=site.work
    site.link('macro-READY.json',site.files['READY.json'])
    site.link('baseline-far.glb',site.files['far.glb'])
    for gp in review['near_tiles']:
        site.link('baseline-near.glb.gz',site.files[Path(gp['file']).name])
        write(w/'context-features.json',[{'localId':i} for i in gp['feature_local_ids']])
        subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
        for role in ('near','far'):
            tr=np.fromfile(w/('baseline-'+role+'-triangles.f64'),np.float64).reshape(-1,3,3)
            xy=tr[:,:,:2] @ site.axes.T
            faces=geo.box(xy[:,:,0].min(1),xy[:,:,1].min(1),xy[:,:,0].max(1),xy[:,:,1].max(1))
            dist=geo.distance(faces,envelope);pos=int(np.argmin(dist))
            out.append({'tile':gp['id'],'variant':role,'triangles':len(tr),'minimum_native_triangle_envelope_distance_m':float(dist[pos]),
                        'nearest_triangle_xy_m':xy[pos].tolist()})
            assert dist[pos]>2
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,required=True);parser.add_argument('--pbf',type=Path,required=True)
    parser.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    parser.add_argument('--out',type=Path,default=HERE);args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True);src=PROJECT/'source/precise'/ID/'footprint-review.json'
    review=read(src);site=PlacementMeshes(PROJECT,args.work,review)
    envelope=geo.transform(shape(review['model_footprint']),site.to_xy)
    variants,receipts,bounds,collision=model_variants(args.manifest,args.work)
    fallback=mapbox_vector_tile.decode(args.pbf.read_bytes(),default_options={'y_coord_down':True})['building']
    assert sha(args.pbf)==PBF_SHA
    def proj(points):
        extent=fallback['extent'];x=(points[:,0]/extent+13720)/16384*360-180
        y=np.degrees(np.arctan(np.sinh(np.pi*(1-2*(points[:,1]/extent+6694)/16384))))
        return site.to_xy(np.column_stack((x,y)))
    osm=sorted((geo.transform(shape(f['geometry']),proj).distance(envelope),f['id']) for f in fallback['features'])
    overture=sorted((p.distance(envelope),i) for i,p in site.footprints.items())
    assert osm[0][0]>2 and overture[0][0]>3
    native=city_meshes(site,review,envelope)
    witnesses=[]
    for name,xy,blocked in [('street',(0,-2),False),('central opening',(0,.78),False),('under gatehouse',(0,6),False),
                            ('rear threshold',(0,11.68),False),('rear lane',(0,13),False),('west gate screen',(-1.6,.78),True),
                            ('east gate screen',(1.6,.78),True),('west wall',(-3,5.2),True),('east wall',(3,5.2),True)]:
        assert collision.covers(Point(xy))==blocked
        witnesses.append({'name':name,'xy':list(xy),'wgs84':site.to_wgs(np.array([xy]))[0].tolist(),'blocked':blocked})
    heading=review['author_frame']['runtime_heading_deg']
    contract={'id':ID,'lng':site.lon,'lat':site.lat,'heading':heading,'altitude':0,'scale':1,
              'replacement_geometry':None,'source_feature_ids':{'building':[],'building_part':[]},
              'collision_geometry':site.wgs(collision),'bounds_glb':bounds,'model_geometry_sha256':{k:v['sha256'] for k,v in receipts.items()},
              'overviewBearing':300,'overviewPitch':61,'overviewZoom':20,'maxDistance':450,'lod_switch_in_m':500,'lod_switch_out_m':640,
              'navigation':{'listed':False,'status':'主弄穿楼门洞保持贯通；两侧墙体和铁栅保持阻挡。'},
              'placement':{'status':'estimated','note':'淮海中路第一排主弄门楼，对齐保护地块街边及航片主弄轴线；原底图在此留空。'},
              'partial_model':True,'model_scope':read(args.manifest)['scope']}
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',{'id':ID,'source_review_sha256':sha(src),'manifest_sha256':sha(args.manifest),'script_sha256':sha(Path(__file__)),
          'contract_sha256':sha(args.out/'final-placement-contract.json'),'model_assets':receipts,'variants':variants,'native_sources':native,
          'vector_sources':{'overture_local_checked':len(overture),'overture_nearest_ids_and_distance_m':[[i,d] for d,i in overture[:7]],
          'openmaptiles_url':PBF_URL,'openmaptiles_sha256':PBF_SHA,'openmaptiles_buildings':len(osm),'nearest_openmaptiles_id':osm[0][1],
          'nearest_openmaptiles_distance_m':osm[0][0]},'ground':{'section_altitudes_m':[.19,.775,1.60],'area_m2':collision.area,
          'clearance_from_centreline_m':LineString([(0,-2),(0,13)]).distance(collision),'witnesses':witnesses},
          'passed':all(v['passed'] for v in variants.values())})
    print({k:[h['name'] for h in v['checks'] if not h['passed']] for k,v in variants.items()})
    assert all(v['passed'] for v in variants.values())


if __name__=='__main__':main()
