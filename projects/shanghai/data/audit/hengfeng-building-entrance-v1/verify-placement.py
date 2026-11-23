"""Compare the Hengfeng entrance with both native city meshes and the correct part of the vector fallback."""
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

ID='huangpu-hengfeng-building-entrance'
OWNER=163
PEERS={163,1766,2278,2600,1514,651,1802,1580,2094,2929,1588,373,1720,2297,859,152}

def inspect(macro,manifest,vector,output):
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    meta=read(manifest)
    pack=read(vector)
    assert pack['sha256']=='e6a2578dd38fdc6ef28737b68ea1e59181efe7d2fbde1d812f76f0a555833495'
    part=next(v for v in pack['nearby_features'] if (v['id'],v['component'])==(116367960,18))
    north=next(v for v in pack['nearby_features'] if (v['id'],v['component'])==(116293700,5))
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
        assert abs(bounds['max'][1]-13.65)<.01 and abs(bounds['min'][1]+.01)<.002
        footprint=mesh.footprints[OWNER];north_footprint=mesh.footprints[1588]
        vector_foot=transform(shape(part['geometry']),mesh.to_xy);vector_north=transform(shape(north['geometry']),mesh.to_xy)
        assert footprint.symmetric_difference(vector_foot).area/footprint.area<.002
        assert north_footprint.symmetric_difference(vector_north).area/north_footprint.area<.002
        assert footprint.distance(north_footprint)<.02
        # The portal remains open toward the street. Existing collision at the
        # parent building begins at its own old wall, independently of this piece.
        solid=box(-4.18,0,4.18,.82).difference(box(-2.06,-.01,2.06,.65))
        feet=[(-2.38,-.80,.55),(2.38,-.80,.55),(-3.05,-.105,.67),(3.05,-.105,.67)]
        for x,y,radius in feet:
            solid=solid.union(Point(x,y).buffer(radius,quad_segs=7))
        assert all(solid.disjoint(mesh.footprints[i]) for i in PEERS-{OWNER})
        ground=[]
        for x in (-4.00,-3.05,-2.38,-1.66,-.35,0.,1.61,2.38,3.05,4.00):
            for y in (-1.43,-1.09,-.74,-.26,.27,.74):
                wall=(-4.18<=x<=4.18 and 0<=y<=.82 and not (-2.06<x<2.06 and y<.65))
                disks=any((x-u)**2+(y-v)**2<radius**2 for u,v,radius in feet)
                expected=wall or disks
                assert solid.covers(Point(x,y))==expected,(x,y)
                ground.append({'x':x,'y':y,'blocked':expected})
        probes=[(x,z) for x in (-4.10,-3.3,-2.2,-1.,0.,1.,2.2,3.3,4.10)
                for z in (.25,1.25,2.25,4.55,6.65,8.5,10.1,11.2,13.59)]
        variants={}
        for name,tri,owners,ties in grouping(mesh,group):
            wall=tri[owners==OWNER];others=tri[owners!=OWNER]
            assert set(np.unique(owners))==PEERS and len(wall)>0 and len(others)>0
            original=[]
            for x,z in probes:
                _,dist,contact=hit(wall,np.array([x,-3,z]),np.array([0.,1.,0.]))
                assert np.isfinite(dist) and .52<contact[1]<45.0,(name,x,z,contact)
                original.append({'x':x,'z':z,'original_surface_y':round(float(contact[1]),4)})
            top=float(wall[:,:,2].max());assert abs(top-({'near':19.2,'far':19.2}[name]))<.04
            variants[name]={'retained_owner_triangles':len(wall),'retained_neighbor_triangles':len(others),
                            'per_owner':{int(k):int(np.count_nonzero(owners==k)) for k in np.unique(owners)},
                            'owner_original_height_m':top,'normal_rays':original}
        anchor=review['author_frame'];geometry=mesh.wgs(solid);checked_geometry(geometry,ID+' local solid',collision=True)
        contract={'id':ID,'lng':anchor['anchor']['lng'],'lat':anchor['anchor']['lat'],'heading':anchor['runtime_heading_deg'],
                  'scale':1,'altitude':0,'owner':{'macro_id':review['frozen_macro'],'feature_local_id':OWNER},'source_feature_ids':{'building':[],'building_part':[]},'replacement_geometry':None,
                  'collision_geometry':geometry,'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,
                  'navigation':{'listed':False,'status':'从江西中路街面查看恒丰大楼题名、弧形门罩和两对柱。'},
                  'placement':{'status':'estimated','note':'原房163西墙中段按三个全景测点确定沿墙位置，门罩与柱列在原墙街侧。保留原163和北邻1588、1766以及道路对面的2729。'},
                  'partial_model':True,'model_scope':meta['model_scope_zh'],'overviewBearing':48,'overviewPitch':33,'overviewZoom':20.55,
                  'maxDistance':670,'lod_switch_in_m':310,'lod_switch_out_m':450}
        output.mkdir(exist_ok=True,parents=True);write(output/'final-placement-contract.json',contract)
        result={'id':ID,'passed':True,'contract_sha256':sha(output/'final-placement-contract.json'),'checker_sha256':sha(Path(__file__)),
                'asset_hashes':assets,'model_bounds_glb':bounds,'original_geometry_cut':False,'replaced_triangles':0,
                'vector_owner':{'id':116367960,'component':18,'north_id':116293700,'north_component':5},'original_building_gap_m':footprint.distance(north_footprint),
                'model_projection_m2':projection.area,'collision_m2':solid.area,'front_shift_street_m':.60,'wall_back_from_front_m':.82,
                'source_variants':variants,'ground_probes':ground,'frozen_bindings':review['frozen_bindings']}
        write(output/'placement-geometry.json',result)
        return result
if __name__=='__main__':
    args=ArgumentParser(description=__doc__);args.add_argument('--macro',type=Path,required=True);args.add_argument('--manifest',type=Path,required=True)
    args.add_argument('--vector',type=Path,required=True);args.add_argument('--out',default=HERE,type=Path);options=args.parse_args()
    result=inspect(options.macro,options.manifest,options.vector,options.out)
    print(len(result['ground_probes']),[(k,len(v['normal_rays']),v['retained_owner_triangles'])for k,v in result['source_variants'].items()])
