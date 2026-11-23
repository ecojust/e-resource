"""Compare the Salt Bank portico with both native city meshes and the correct part of the vector fallback."""
from argparse import ArgumentParser
from pathlib import Path
from tempfile import TemporaryDirectory
import runpy
import sys

import numpy as np
from shapely import transform
from shapely.geometry import box, Point, shape

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,sha,write
from build_candidate_city_integrations import checked_geometry

ID='huangpu-salt-industry-bank-entrance'
OWNER=718
PEERS={2808,2652,968,718,3201,1082,2550}

def inspect(macro,manifest,vector,output):
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    meta=read(manifest)
    pack=read(vector)
    assert pack['sha256']=='e6a2578dd38fdc6ef28737b68ea1e59181efe7d2fbde1d812f76f0a555833495'
    part=next(v for v in pack['nearby_features'] if (v['id'],v['component'])==(116367860,9))
    north=next(v for v in pack['nearby_features'] if (v['id'],v['component'])==(116293700,4))
    group,=review['near_tiles']
    assert PEERS==set(group['feature_local_ids'])
    grouping=runpy.run_path(str(HERE.parent/'metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    hit=runpy.run_path(str(HERE.parent/'postal-office-v1/independent-glb-review-helpers.py'))['first_hit']
    with TemporaryDirectory() as work:
        root=Path(work)
        for receipt in review['frozen_bindings']:
            name=Path(receipt['repository_path']).name; file=macro/name
            assert sha(file)==receipt['sha256'] and file.stat().st_size==receipt['bytes']
            (root/name).symlink_to(file.resolve())
        mesh=PlacementMeshes(PROJECT,root,review)
        mesh.env['NODE_OPTIONS']=(mesh.env.get('NODE_OPTIONS','')+' --require='+str(HERE.parent/'mitsui-bussan-pediment-front-v1/decode-texture.cjs')).strip()
        assets,bounds,projection,physical=mesh.decode_model(manifest)
        assert abs(bounds['max'][1]-6.87)<.01 and abs(bounds['min'][1])<.002
        footprint=mesh.footprints[OWNER];north_footprint=mesh.footprints[1082]
        vector_foot=transform(shape(part['geometry']),mesh.to_xy);vector_north=transform(shape(north['geometry']),mesh.to_xy)
        assert footprint.symmetric_difference(vector_foot).area/footprint.area<.002
        assert north_footprint.symmetric_difference(vector_north).area/north_footprint.area<.002
        assert 2.0<footprint.distance(north_footprint)<2.6
        # Recessed glass below each arch closes on a vertical plane. The two
        # cylindrical columns stand on square plinths separate from the rear wall.
        solid=box(-3.28,-.30,3.28,.98)
        for cx,half in ((-1.67,.57),(0,.77),(1.67,.57)):
            solid=solid.difference(box(cx-half,-.31,cx+half,-.095))
        bases=[]
        for side in [-1,1]:
            x=side*3.48
            bases.extend([box(x-.49,-1.21,x+.49,-.09),box(x-.41,-.97,x+.41,.98)])
            x=side*2.34;bases.append(box(x-.41,-1.385,x+.41,-.575))
        for base in bases:solid=solid.union(base)
        assert all(solid.disjoint(mesh.footprints[i]) for i in PEERS-{OWNER})
        ground=[]
        for x in (-4.09,-3.47,-2.91,-2.34,-1.67,-.75,-.3,0.,.8,1.67,2.34,2.92,3.48,4.09):
            for y in (-2.12,-1.44,-1.18,-.84,-.49,-.21,-.05,.51,1.06):
                back=-3.28<=x<=3.28 and -.30<=y<=.98
                if y<-.095 and any(abs(x-u)<v for u,v in ((-1.67,.57),(0,.77),(1.67,.57))):back=False
                outer=abs(abs(x)-3.48)<.49 and -1.21<=y<=-.09 or abs(abs(x)-3.48)<.41 and -.97<=y<=.98
                inner=abs(abs(x)-2.34)<.41 and -1.385<=y<=-.575
                expected=back or outer or inner
                assert solid.covers(Point(x,y))==expected,(x,y)
                ground.append({'x':x,'y':y,'blocked':expected})
        probes=[(x,z) for x in (-4.04,-3.48,-2.81,-2.34,-1.67,-.73,0,.75,1.67,2.34,2.82,3.48,4.04)
                for z in (.1,.45,1.7,2.33,3.59,4.22,5.35,6.,6.80)]
        variants={}
        for name,tri,owners,ties in grouping(mesh,group):
            wall=tri[owners==OWNER];others=tri[owners!=OWNER]
            assert set(np.unique(owners))==PEERS and len(wall)>0 and len(others)>0
            original=[]
            for x,z in probes:
                _,dist,contact=hit(wall,np.array([x,-3,z]),np.array([0.,1.,0.]))
                assert np.isfinite(dist) and .688<contact[1]<.948,(name,x,z,contact)
                original.append({'x':x,'z':z,'original_surface_y':round(float(contact[1]),4)})
            top=float(wall[:,:,2].max());assert abs(top-({'near':22.4,'far':22.4}[name]))<.04
            variants[name]={'retained_owner_triangles':len(wall),'retained_neighbor_triangles':len(others),
                            'per_owner':{int(k):int(np.count_nonzero(owners==k)) for k in np.unique(owners)},
                            'owner_original_height_m':top,'normal_rays':original}
        anchor=review['author_frame'];geometry=mesh.wgs(solid);checked_geometry(geometry,ID+' local solid',collision=True)
        contract={'id':ID,'lng':anchor['anchor']['lng'],'lat':anchor['anchor']['lat'],'heading':anchor['runtime_heading_deg'],
                  'scale':1,'altitude':0,'owner':{'macro_id':review['frozen_macro'],'feature_local_id':OWNER},'source_feature_ids':{'building':[],'building_part':[]},'replacement_geometry':None,
                  'collision_geometry':geometry,'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,
                  'navigation':{'listed':False,'status':'从北京东路街面查看盐业大楼门罩、塔司干圆柱与圆孔石栏。'},
                  'placement':{'status':'estimated','note':'原房718南墙中轴向街侧外移0.73米，侧面回接原墙。保留718和同组另六处原房，包括东邻270号中一信托1082；原地图矢量保持。'},
                  'partial_model':True,'model_scope':meta['model_scope_zh'],'overviewBearing':347,'overviewPitch':67,'overviewZoom':20.6,
                  'maxDistance':670,'lod_switch_in_m':310,'lod_switch_out_m':450}
        output.mkdir(exist_ok=True,parents=True);write(output/'final-placement-contract.json',contract)
        result={'id':ID,'passed':True,'contract_sha256':sha(output/'final-placement-contract.json'),'checker_sha256':sha(Path(__file__)),
                'asset_hashes':assets,'model_bounds_glb':bounds,'original_geometry_cut':False,'replaced_triangles':0,
                'vector_owner':{'id':116367860,'component':9,'adjacent_id':116293700,'adjacent_component':4},'original_building_gap_m':footprint.distance(north_footprint),
                'model_projection_m2':projection.area,'collision_m2':solid.area,'front_shift_street_m':.73,'wall_back_from_front_m':.98,
                'source_variants':variants,'ground_probes':ground,'frozen_bindings':review['frozen_bindings']}
        write(output/'placement-geometry.json',result)
        return result
if __name__=='__main__':
    args=ArgumentParser(description=__doc__);args.add_argument('--macro',type=Path,required=True);args.add_argument('--manifest',type=Path,required=True)
    args.add_argument('--vector',type=Path,required=True);args.add_argument('--out',default=HERE,type=Path);options=args.parse_args()
    result=inspect(options.macro,options.manifest,options.vector,options.out)
    print(len(result['ground_probes']),[(k,len(v['normal_rays']),v['retained_owner_triangles'])for k,v in result['source_variants'].items()])
