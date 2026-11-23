"""Compare the southern office with both native city meshes and the correct part of the vector fallback."""
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

ID='huangpu-zili-waterworks-office-front'
OWNER=1588
PEERS={163,1766,2278,2600,1514,651,1802,1580,2094,2929,1588,373,1720,2297,859,152}

def inspect(macro,manifest,vector,output):
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    meta=read(manifest)
    pack=read(vector)
    assert pack['sha256']=='e6a2578dd38fdc6ef28737b68ea1e59181efe7d2fbde1d812f76f0a555833495'
    part=next(v for v in pack['nearby_features'] if (v['id'],v['component'])==(116293700,5))
    north=next(v for v in pack['nearby_features'] if (v['id'],v['component'])==(116293700,6))
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
        assert abs(bounds['max'][1]-11.25)<.01 and abs(bounds['min'][1])<.005
        footprint=mesh.footprints[OWNER];north_footprint=mesh.footprints[1766]
        vector_foot=transform(shape(part['geometry']),mesh.to_xy);vector_north=transform(shape(north['geometry']),mesh.to_xy)
        assert footprint.symmetric_difference(vector_foot).area/footprint.area<.002
        assert north_footprint.symmetric_difference(vector_north).area/north_footprint.area<.002
        assert 26.2<footprint.distance(north_footprint)<26.9
        # The gate is closed in the reference photograph. Its leaf stands 0.19 m inside the front brickwork.
        gate_left,gate_right=(855-918)*28.12/1150,(954-918)*28.12/1150
        solid=box(-5.66,-.025,5.66,.89).difference(box(gate_left+.045,-.028,gate_right-.045,.170))
        # At the party wall the source boundary slopes across the last 29 mm
        # of the rear right return. This area already belongs to its neighbor.
        contact_area=solid.intersection(mesh.footprints[163]).area
        assert .005 < contact_area < .007
        solid=solid.difference(mesh.footprints[163].buffer(.001))
        assert all(solid.disjoint(mesh.footprints[i]) for i in PEERS-{OWNER})
        ground=[]
        for x in (-5.2,-3.2,-2.1,-.45,0,.6,2.0,3.9,5.2):
            for y in (-.35,.075,.33):
                expected=y>=-.025 and not (gate_left+.045<x<gate_right-.045 and y<.17)
                assert solid.covers(Point(x,y))==expected
                ground.append({'x':x,'y':y,'blocked':expected})
        assert footprint.intersection(solid).area>1.5 and footprint.intersection(solid).area<4.5
        probes=[]
        for x in (-5.35,-4,-3,-1.5,0,1.5,3,4,5.35):
            for z in (.25,1.25,2.25,4.55,6.65,8.5,10.1,11.2):probes.append((x,z))
        variants={}
        for name,tri,owners,ties in grouping(mesh,group):
            wall=tri[owners==OWNER];others=tri[owners!=OWNER]
            assert set(np.unique(owners))==PEERS and len(wall)>0 and len(others)>0
            original=[]
            for x,z in probes:
                _,dist,contact=hit(wall,np.array([x,-3,z]),np.array([0.,1.,0.]))
                assert np.isfinite(dist) and .52<contact[1]<1.03,(name,x,z,contact)
                original.append({'x':x,'z':z,'original_surface_y':round(float(contact[1]),4)})
            top=float(wall[:,:,2].max());assert abs(top-({'near':19.2,'far':16.0}[name]))<.04
            variants[name]={'retained_owner_triangles':len(wall),'retained_neighbor_triangles':len(others),
                            'per_owner':{int(k):int(np.count_nonzero(owners==k)) for k in np.unique(owners)},
                            'owner_original_height_m':top,'normal_rays':original}
        anchor=review['author_frame'];geometry=mesh.wgs(solid);checked_geometry(geometry,ID+' local solid',collision=True)
        contract={'id':ID,'lng':anchor['anchor']['lng'],'lat':anchor['anchor']['lat'],'heading':anchor['runtime_heading_deg'],
                  'scale':1,'altitude':0,'owner':{'macro_id':review['frozen_macro'],'feature_local_id':OWNER},'source_feature_ids':{'building':[],'building_part':[]},'replacement_geometry':None,
                  'collision_geometry':geometry,'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,
                  'navigation':{'listed':False,'status':'从江西中路街面查看464号砖券及上下窗列。'},
                  'placement':{'status':'estimated','note':'新街墙落在原房1588的西面，材质面向街侧前移0.64米、背缘衔接原墙。保留原近远建筑、北楼1766和两栋共用矢量中各自的部件。'},
                  'partial_model':True,'model_scope':meta['model_scope_zh'],'overviewBearing':72,'overviewPitch':36,'overviewZoom':20.7,
                  'maxDistance':670,'lod_switch_in_m':310,'lod_switch_out_m':450}
        output.mkdir(exist_ok=True,parents=True);write(output/'final-placement-contract.json',contract)
        result={'id':ID,'passed':True,'contract_sha256':sha(output/'final-placement-contract.json'),'checker_sha256':sha(Path(__file__)),
                'asset_hashes':assets,'model_bounds_glb':bounds,'original_geometry_cut':False,'replaced_triangles':0,
                'vector_owner':{'id':116293700,'south_component':5,'north_component':6},'original_building_gap_m':footprint.distance(north_footprint),
                'model_projection_m2':projection.area,'collision_m2':solid.area,'existing_party_wall_contact_removed_m2':contact_area,'front_shift_street_m':.64,'wall_back_from_front_m':.89,
                'source_variants':variants,'ground_probes':ground,'frozen_bindings':review['frozen_bindings']}
        write(output/'placement-geometry.json',result)
        return result
if __name__=='__main__':
    args=ArgumentParser(description=__doc__);args.add_argument('--macro',type=Path,required=True);args.add_argument('--manifest',type=Path,required=True)
    args.add_argument('--vector',type=Path,required=True);args.add_argument('--out',default=HERE,type=Path);options=args.parse_args()
    result=inspect(options.macro,options.manifest,options.vector,options.out)
    print(len(result['ground_probes']),[(k,len(v['normal_rays']),v['retained_owner_triangles'])for k,v in result['source_variants'].items()])
