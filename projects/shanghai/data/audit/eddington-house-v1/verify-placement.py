"""Check the street apartment against the real full-resolution and distant city meshes."""
import argparse
from pathlib import Path
import sys
import numpy as np
import shapely
from shapely.geometry import box,Point,shape

AUDIT=Path(__file__).resolve().parent
PROJECT=AUDIT.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
from source_meshes import house_meshes
ID='jingan-eddington-house'
OWNER=1912
PEERS=[964, 1947, 2189, 3139, 2927, 1256, 2596, 484]


def run():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',type=Path,required=True)
    p.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    p.add_argument('--out',type=Path,default=AUDIT)
    a=p.parse_args();a.out.mkdir(exist_ok=True,parents=True)
    data=PROJECT/'source/precise'/ID/'footprint-review.json';review=read(data)
    ctx=PlacementMeshes(PROJECT,a.work,review)
    for f in review['owners']:
        if f['local_id'] not in ctx.footprints:ctx.footprints[f['local_id']]=shapely.transform(shape(f['geometry']),ctx.to_xy)
    assets,bounds,model,ground=ctx.decode_model(a.manifest)
    baseline=house_meshes(ctx,review['near_tiles'][0])
    roof={k:ctx.project_faces(t) for k,(t,peer,method) in baseline.items()}
    peers={k:ctx.project_faces(peer) for k,(t,peer,method)in baseline.items()}
    src=ctx.footprints[OWNER]
    # Start at the verified owner polygon. Expand only enough to remove projecting native sill bands.
    mask=src.buffer(.40,join_style='mitre')
    assert all(g.difference(mask).area<.00005 for g in roof.values()),[(k,g.difference(mask).area)for k,g in roof.items()]
    report={}
    for k,(tri,other,method) in baseline.items():
        report[k]=dict(triangles=len(tri),height_m=float(tri[:,:,2].max()),retained_m2=roof[k].difference(mask).area,
                       actual_model_overlap_m2=roof[k].intersection(model).area,old_m2=roof[k].area,cut_m2=roof[k].intersection(mask).area,
                       peer_cut_gap_m=peers[k].distance(mask),peer_cut_m2=peers[k].intersection(mask).area,
                       peer_model_gap_m=peers[k].distance(model),other_triangles=len(other),assignment=method)
        assert report[k]['peer_cut_m2']<.00004 and peers[k].distance(model)>.15,report[k]
    # The upper balconies overhang the public pavement. The entrance has a deep, accessible threshold.
    core=box(-7.91,.10,7.91,9.89).difference(box(-2.12,-.72,2.12,1.17))
    wing=box(7.91,.77,20.14,9.88)
    rear=box(8.2,9.78,19.7,13.04)
    pillar=box(2.03,-.68,2.53,1.24)
    from shapely.affinity import scale
    right=shapely.union_all([wing,rear,pillar])
    walk=shapely.union_all([core,right,scale(right,xfact=-1,origin=(0,0))],grid_size=.002)
    spec=[('pavement before entrance',0,-2.2,False),('under projecting name',0,-1.13,False),
          ('between striped jambs',0,-.37,False),('above threshold',0,.74,False),
          ('south striped jamb',-2.28,-.35,True),('north striped jamb',2.28,-.35,True),
          ('closed glass door',0,1.24,True),('south hall windows',-5.41,.33,True),
          ('north hall windows',5.41,.33,True),('under south balconies',-17,.22,False),
          ('under north balconies',17,.22,False),('south shop enclosure',-17,.98,True),
          ('north shop enclosure',17,.98,True),('north side lane',21.55,6,False),
          ('south side lane',-21.55,6,False),('rear courtyard centre',0,11.25,False),
          ('north rear wing',15.2,11.25,True),('south rear wing',-15.2,11.25,True)]
    for i in PEERS:spec.append((f'preserved neighboring building {i}',*ctx.footprints[i].representative_point().coords[0],True))
    probes=[]
    for name,x,y,want in spec:
        pt=Point(x,y);ow=walk.covers(pt);keep=src.difference(mask).covers(pt)
        adjacent=[i for i,g in ctx.footprints.items() if i!=OWNER and g.covers(pt)]
        assert bool(ow or keep or adjacent)==want,(name,x,y,ow,adjacent,want)
        q=dict(name=name,xy=[x,y],point=ctx.to_wgs(np.array([[x,y]]))[0].tolist(),expected='building' if want else None,modelObstacle=ow,cut=mask.covers(pt))
        if adjacent:q['ownerLocalId']=adjacent[0]
        probes.append(q)
    others={i:dict(footprint_gap_to_cut_m=ctx.footprints[i].distance(mask),footprint_gap_to_model_m=ctx.footprints[i].distance(model))for i in PEERS}
    assert all(q['footprint_gap_to_cut_m']>.05 for q in others.values()),others
    _,bearing,pitch=read(data.parent/'camera-preflight.json')['recommendation']
    frame=review['author_frame'];contract=dict(id=ID,**frame['anchor'],heading=frame['runtime_heading_deg'],scale=1,altitude=0,
         owner=review['owner'],source_feature_ids={'building':[review['owner']['source_key'].split(':')[1]],'building_part':[]},
         bounds_glb=bounds,model_geometry_sha256={k:v['sha256']for k,v in assets.items()},replacement_geometry=ctx.wgs(mask),collision_geometry=ctx.wgs(walk),
         overviewBearing=bearing,overviewPitch=pitch,overviewZoom=18.9,maxDistance=690,lod_switch_in_m=510,lod_switch_out_m=665,
         navigation={'listed':False,'status':'常德路沿街可走至三层雨篷下、横纹门柱之间的玻璃门前，两翼阳台下保留人行道。'},
         placement={'status':'estimated','note':'常德路195号铭牌和地址点对应源楼1912，实名OSM建筑与底图交并比98.42%。建筑沿常德路东向，街面宽约41.46米。楼层高度、门廊深度、后翼与屋面细部按照片和轮廓估计。'},
         partial_model=False,model_scope=read(a.manifest)['model_scope_zh'])
    contract['overview_focus_bounds_glb']={'min':[-20.6,.1,-3.0],'max':[20.6,28.71,1.45]}
    contract['owner']={k:contract['owner'][k]for k in ['macro_id','feature_local_id']}
    for k in ['replacement_geometry','collision_geometry']:checked_geometry(contract[k],k,collision=k=='collision_geometry')
    write(a.out/'final-placement-contract.json',contract)
    write(a.out/'placement-geometry.json',dict(id=ID,source_sha256=sha(data),manifest_sha256=sha(a.manifest),contract_sha256=sha(a.out/'final-placement-contract.json'),
         script_sha256=sha(Path(__file__)),assets=assets,near_and_far=report,neighbors=others,
         ground_probes=probes,model_projection_m2=model.area,collision_m2=walk.area,old_vector_m2=src.area,mask_m2=mask.area))
    print('Checked',[(k,v['triangles'],v['peer_model_gap_m'])for k,v in report.items()],len(probes))
if __name__=='__main__':run()
