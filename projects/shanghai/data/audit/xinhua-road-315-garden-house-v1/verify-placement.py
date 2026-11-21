"""Check the garden house against the real full-resolution and distant city meshes."""
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
ID='changning-xinhua-road-315-garden-house'
OWNER=4029
PEERS=[237,4002,1552,1401,4091,672]


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
    # The broad eastern arcade is open at ground level. The door is at its rear wall.
    walk=shapely.union_all([box(-14.97,.90,-6.57,12.03),box(-6.57,-1.52,.25,12.03),
            box(.25,1.35,8.95,12.03),box(8.95,3.09,14.95,12.03),box(8.95,.21,9.17,3.10),
            box(14.73,.21,14.95,3.10),box(8.95,.21,9.49,.445),box(14.41,.21,14.95,.445),
            box(-12.50,12.02,-4.90,19.64),box(-.77,12.02,5.60,13.64)])
    spec=[('three garden windows',-3.18,-1.40,True),('grass before projecting gable',-3.18,-2.14,False),
          ('garden door setback',4.59,.70,False),('garden room glazing',4.59,1.39,True),
          ('arcade west springing pier',9.18,.30,True),('arcade east springing pier',14.69,.30,True),
          ('open passage through broad arch',11.95,.35,False),('open bay before rear door',11.95,2.66,False),
          ('closed veranda glazed doors',11.95,3.20,True),('northwest wing',-8.4,18.68,True),
          ('recess between two northern gables',-2.49,14.58,False),('north stair bay',2.08,13.55,True),
          ('north entry court',2.08,16.50,False),('lawn',3,-4.2,False)]
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
    frame=review['author_frame'];contract=dict(id=ID,**frame['anchor'],heading=frame['runtime_heading_deg'],scale=1,altitude=0,
         owner=review['owner'],source_feature_ids={'building':[review['owner']['source_key'].split(':')[1]],'building_part':[]},
         bounds_glb=bounds,model_geometry_sha256={k:v['sha256']for k,v in assets.items()},replacement_geometry=ctx.wgs(mask),collision_geometry=ctx.wgs(walk),
         overviewBearing=2,overviewPitch=35,overviewZoom=18.9,maxDistance=630,lod_switch_in_m=510,lod_switch_out_m=665,
         navigation={'listed':False,'status':'可绕主屋和北翼观看，花园东侧大券以内留有走近门扇的空间。'},
         placement={'status':'estimated','note':'核对新华路315号实名地址、地块4029、OSM w864485667、带北针总平面、上下两层平面和两期屋面。仅重建主屋及相连北翼，独立门房、围墙和其他建筑保留。'},
         partial_model=False,model_scope=read(a.manifest)['model_scope_zh'])
    contract['owner']={k:contract['owner'][k]for k in ['macro_id','feature_local_id']}
    for k in ['replacement_geometry','collision_geometry']:checked_geometry(contract[k],k,collision=k=='collision_geometry')
    write(a.out/'final-placement-contract.json',contract)
    write(a.out/'placement-geometry.json',dict(id=ID,source_sha256=sha(data),manifest_sha256=sha(a.manifest),contract_sha256=sha(a.out/'final-placement-contract.json'),
         script_sha256=sha(Path(__file__)),assets=assets,near_and_far=report,neighbors=others,
         ground_probes=probes,model_projection_m2=model.area,collision_m2=walk.area,old_vector_m2=src.area,mask_m2=mask.area))
    print('Checked',[(k,v['triangles'],v['peer_model_gap_m'])for k,v in report.items()],len(probes))
if __name__=='__main__':run()
