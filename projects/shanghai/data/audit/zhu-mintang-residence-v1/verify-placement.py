"""Check the 151 gate against decoded native facades and retain every city owner."""
import argparse
import gzip
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import shapely
from shapely.geometry import Point, box
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from build_candidate_city_integrations import checked_geometry
from candidate_placement_meshes import PlacementMeshes, read, sha, write


def native_clearance(ctx, review, projected):
    table=json.loads(gzip.decompress(ctx.files['feature-table.json.gz'].read_bytes()))['features']
    write(ctx.work/'context-features.json',[{'localId':r['localId']}for r in table])
    ctx.link('baseline-far.glb',ctx.files['far.glb'])
    ctx.link('macro-READY.json',ctx.files['READY.json'])
    result={}
    for group in review['near_tiles']:
        ctx.link('baseline-near.glb.gz',ctx.files[Path(group['file']).name])
        subprocess.run(['node',ctx.decoders/'map-decode-source.mjs'],env=ctx.env,check=True,stdout=subprocess.DEVNULL)
        for variant,label in [('near',group['id']),('far','macro_far')]:
            if label in result:continue
            triangles=np.fromfile(ctx.work/f'baseline-{variant}-triangles.f64').reshape(-1,3,3)
            planar=triangles[:,:,:2]@ctx.axes.T
            search=(planar.min(1)<55).all(axis=1)&(planar.max(1)>-55).all(axis=1)
            region=planar[search]
            polygons=shapely.polygons(region)
            solid=shapely.area(polygons)>1e-9
            gap=min(shapely.distance(polygons[solid],projected).min(initial=1e6),
                    shapely.distance(shapely.linestrings(region[~solid]),projected).min(initial=1e6))
            assert gap>.10 and search.any(),(group['id'],variant,gap)
            result[label]={'triangles':len(triangles),'within_55m':int(search.sum()),'minimum_distance_m':float(gap),
                           'overlap_m2':0,'source_sha256':sha(ctx.files['far.glb'if variant=='far'else Path(group['file']).name])}
    return result


def run():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',required=True,type=Path)
    parser.add_argument('--out',default=HERE,type=Path)
    args=parser.parse_args()
    ident='xuhui-zhu-mintang-residence'
    source=PROJECT/'source/precise'/ident
    review=read(source/'footprint-review.json')
    ctx=PlacementMeshes(PROJECT,args.work,review)
    manifest=PROJECT/'assets/models/candidates'/ident/'manifest.json'
    assets,bounds,projected,feet=ctx.decode_model(manifest)
    assert box(-4.451,-.93,4.451,.385).covers(projected),projected.bounds
    neighbors=sorted((poly.distance(projected),i)for i,poly in ctx.footprints.items())
    assert neighbors[0][0]>.25
    clearances=native_clearance(ctx,review,projected)
    # The 0.44m pedestrian barrier accounts for a 0.425m sprint step through a closed gate.
    # The rear face of the narrow rendered wall is within the same envelope.
    solid=unary_union([box(-4.45,-.207,4.45,.233),
                       *[box(x-.355,-.367,x+.355,.367)for x in (-1.92,1.92)],
                       *[box(x-.390,-.92,x+.390,-.12)for x in (-3.48,3.48)]])
    cases=[('pavement at entrance',0,-1.2,False),('north approach',-1,-.40,False),('closed north leaf',-.76,.08,True),
           ('closed south leaf',.83,.08,True),('closed center seam',0,.08,True),('north pier',-1.92,0,True),
           ('south pier',1.92,0,True),('north stone pedestal',-3.48,-.5,True),('south stone pedestal',3.48,-.5,True),
           ('north plaque wall',-2.64,0,True),('south wall return',4.15,0,True),
           ('before north lion',-3.48,-1.11,False),('before south lion',3.48,-1.11,False),
           ('beside southern lion',4.02,-.58,False),('pavement beside northern lion',-4.02,-.58,False),
           ('inside gate line',0,.46,False),('outside northern wall cut',-4.8,0,False),('outside southern wall cut',4.8,0,False)]
    probes=[]
    for name,x,y,expected in cases:
        pt=Point(x,y)
        assert expected==solid.covers(pt) and not any(v.covers(pt)for v in ctx.footprints.values()),name
        probes.append(dict(name=name,xy=[x,y],wgs84=ctx.to_wgs(np.array([[x,y]]))[0].tolist(),cut=False,
                           modelObstacle=expected,expected='building' if expected else None))
    for i in review['context_owner_ids']:
        at=ctx.footprints[i].representative_point()
        assert not solid.covers(at)
        probes.append(dict(name=f'retained native building {i}',ownerLocalId=i,xy=[at.x,at.y],
                           wgs84=ctx.to_wgs(np.array(at.coords))[0].tolist(),cut=False,modelObstacle=False,expected='building'))
    frame=review['author_frame']
    contract=dict(id=ident,**frame['anchor'],heading=frame['runtime_heading_deg'],altitude=0,scale=1,
                  replacement_geometry=None,source_feature_ids={'building':[],'building_part':[]},
                  collision_geometry=ctx.wgs(solid),bounds_glb=bounds,
                  model_geometry_sha256={k:v['sha256']for k,v in assets.items()},
                  overviewBearing=78,overviewPitch=37,overviewZoom=20.18,maxDistance=510,
                  lod_switch_in_m=445,lod_switch_out_m=585,
                  navigation={'listed':False,'status':'门扇依2019年街照关闭，门外人行道可通行。'},
                  placement={'status':'estimated','note':'由2013、2019和2021年街道影像中两柱球顶及两扇上角交会落位。街门独立，院内与街对面原有房屋全部保留。'},
                  partial_model=True,model_scope=read(manifest)['model_scope_zh'])
    checked_geometry(contract['collision_geometry'],'151 entrance',collision=True)
    out=args.out;out.mkdir(exist_ok=True,parents=True)
    write(out/'final-placement-contract.json',contract)
    write(out/'placement-geometry.json',dict(id=ident,script_sha256=sha(Path(__file__)),manifest_sha256=sha(manifest),
          reference_sha256=sha(source/'street-registration.json'),decoded_model_assets=assets,
          model_projection_m2=projected.area,near_ground_mesh_m2=feet.area,collision_m2=solid.area,
          native_clearances=clearances,nearest_vector_geometry_m=neighbors[:7],ground_probes=probes,
          retained_buildings=review['context_owner_ids'],contract_sha256=sha(out/'final-placement-contract.json')))


if __name__=='__main__':
    run()
