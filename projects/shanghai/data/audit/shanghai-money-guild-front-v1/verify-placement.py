"""Compare the Money Guild frontage with both native city meshes and the correct part of the vector fallback."""
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

ID='huangpu-shanghai-money-guild-front'
OWNER=182
PEERS={1088, 2561, 2179, 168, 1450, 2059, 44, 378, 562, 723, 2452, 1876, 182, 727, 216, 157, 2746, 2013}

def inspect(macro,manifest,vector,output):
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    meta=read(manifest)
    pack=read(vector)
    assert pack['sha256']=='2cc557168a2d1e041735028eab34d233a0ed2c3bf04497e91cfa92dbf27cb48c'
    part=next(v for v in pack['nearby_features'] if (v['id'],v['component'])==(1784058740,19))
    north=next(v for v in pack['nearby_features'] if (v['id'],v['component'])==(106284410,1671))
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
        assert abs(bounds['max'][1]-15.695)<.008 and abs(bounds['min'][1]+.004)<.006
        footprint=mesh.footprints[OWNER];north_footprint=mesh.footprints[378]
        vector_foot=transform(shape(part['geometry']),mesh.to_xy);vector_north=transform(shape(north['geometry']),mesh.to_xy)
        assert footprint.symmetric_difference(vector_foot).area/footprint.area<.002
        assert north_footprint.symmetric_difference(vector_north).area/north_footprint.area<.002
        assert footprint.distance(north_footprint)<.05
        # Walking height uses the old host behind the doors and the physical footprint
        # of the new facing and ground piers. The upper balconies remain clear below.
        solid=box(-7.54,0,7.54,.96).difference(box(-1.32,-.01,1.32,.225))
        for x in (-1.45,1.45):
            solid=solid.union(Point(x,-.24).buffer(.235,quad_segs=16))
        for x,half in [(-7.20,.275),(-2.44,.26),(2.44,.26),(7.20,.275)]:
            solid=solid.union(box(x-half,-.14,x+half,.10))
        assert all(solid.disjoint(mesh.footprints[i]) for i in PEERS-{OWNER})
        ground=[]
        for x in (-7.75,-7.20,-5.52,-4.88,-3.2,-2.44,-1.67,-1.45,-1.22,-.60,0,.65,1.22,1.45,1.67,2.44,3.24,4.88,6.10,7.20,7.75):
            for y in (-1.12,-.50,-.32,-.23,-.11,-.06,.10,.32,.88,1.05):
                back=abs(x)<=7.54 and 0<=y<=.96 and (abs(x)>=1.32 or y>=.225)
                column=min((x-u)**2+(y+.24)**2 for u in (-1.45,1.45))<=.235**2
                pier=any(abs(x-u)<half for u,half in [(-7.20,.275),(-2.44,.26),(2.44,.26),(7.20,.275)]) and -.14<=y<=.10
                expected=back or column or pier
                assert solid.covers(Point(x,y))==expected,(x,y)
                ground.append({'x':x,'y':y,'blocked':expected})
        probes=[(x,z)for x in (-7.30,-7.05,-5.75,-4.88,-3.77,-2.44,-1.45,0,1.45,2.44,3.77,4.88,5.75,7.05,7.30)
                for z in (.1,1.2,2.83,4.07,5.81,8.15,9.09,11.77,13.48,14.49,15.39)]
        variants={}
        for name,tri,owners,ties in grouping(mesh,group):
            wall=tri[owners==OWNER];others=tri[owners!=OWNER]
            assert set(np.unique(owners))==PEERS and len(wall)>0 and len(others)>0
            original=[]
            for x,z in probes:
                _,dist,contact=hit(wall,np.array([x,-3,z]),np.array([0.,1.,0.]))
                assert np.isfinite(dist) and .60<contact[1]<.87,(name,x,z,contact)
                original.append({'x':x,'z':z,'original_surface_y':round(float(contact[1]),4)})
            top=float(wall[:,:,2].max());assert abs(top-({'near':22.7,'far':16.0}[name]))<.04
            variants[name]={'retained_owner_triangles':len(wall),'retained_neighbor_triangles':len(others),
                            'per_owner':{int(k):int(np.count_nonzero(owners==k)) for k in np.unique(owners)},
                            'owner_original_height_m':top,'normal_rays':original}
        anchor=review['author_frame'];geometry=mesh.wgs(solid);checked_geometry(geometry,ID+' local solid',collision=True)
        contract={'id':ID,'lng':anchor['anchor']['lng'],'lat':anchor['anchor']['lat'],'heading':anchor['runtime_heading_deg'],
                  'scale':1,'altitude':0,'owner':{'macro_id':review['frozen_macro'],'feature_local_id':OWNER},'source_feature_ids':{'building':[],'building_part':[]},'replacement_geometry':None,
                  'collision_geometry':geometry,'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,
                  'navigation':{'listed':False,'status':'从宁波路查看钱业公会大楼的券柱门、三座悬挑铁栏阳台和穗饰。'},
                  'placement':{'status':'estimated','note':'沿冻结原房182宁波路一侧直边向街侧偏0.64米；门窗退距和侧收边均实查。原房182、共墙378以及同组另16处原房全部保留。'},
                  'partial_model':True,'model_scope':meta['model_scope_zh'],'overviewBearing':334,'overviewPitch':46,'overviewZoom':19.58,
                  'maxDistance':670,'lod_switch_in_m':310,'lod_switch_out_m':450}
        output.mkdir(exist_ok=True,parents=True);write(output/'final-placement-contract.json',contract)
        result={'id':ID,'passed':True,'contract_sha256':sha(output/'final-placement-contract.json'),'checker_sha256':sha(Path(__file__)),
                'asset_hashes':assets,'model_bounds_glb':bounds,'original_geometry_cut':False,'replaced_triangles':0,
                'vector_owner':{'id':1784058740,'component':19,'adjacent_id':106284410,'adjacent_component':1671},'original_building_gap_m':footprint.distance(north_footprint),
                'model_projection_m2':projection.area,'collision_m2':solid.area,'front_shift_street_m':.64,'wall_back_from_front_m':.96,
                'source_variants':variants,'ground_probes':ground,'frozen_bindings':review['frozen_bindings']}
        write(output/'placement-geometry.json',result)
        return result
if __name__=='__main__':
    args=ArgumentParser(description=__doc__);args.add_argument('--macro',type=Path,required=True);args.add_argument('--manifest',type=Path,required=True)
    args.add_argument('--vector',type=Path,required=True);args.add_argument('--out',default=HERE,type=Path);options=args.parse_args()
    result=inspect(options.macro,options.manifest,options.vector,options.out)
    print(len(result['ground_probes']),[(k,len(v['normal_rays']),v['retained_owner_triangles'])for k,v in result['source_variants'].items()])
