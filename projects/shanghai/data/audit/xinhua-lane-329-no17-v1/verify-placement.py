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
ID='changning-xinhua-lane-329-no17'
OWNER=1248
PEERS=[1839,4113,672,3413,4091,4002]


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
    # Recess the south wall behind the arcade and preserve the lane outside the shut doors.
    # Above-head terrace rails, entrance hood and porch step are traversable at ground level.
    inner=shapely.Polygon([(-5.80,.00),(4.24,.00),(4.24,13.57),(-6.08,13.57)])
    arcade=box(5.27,.04,5.56,13.51)
    for u in (-4.73,-1.66,1.59,4.70):
        center=(.04+13.51)/2+u
        arcade=arcade.difference(box(5.02,center-1.275,5.81,center+1.275))
    porch=shapely.union_all([box(1.51,-.88,2.02,.00),box(3.76,-.88,4.27,.00)])
    east_return=box(4.18,13.32,5.52,13.55)
    walk=shapely.union_all([inner,arcade,porch,east_return],grid_size=.002)
    spec=[('closed pointed garage',-.73,.15,True),('lane before four wooden leaves',-.73,-.48,False),
          ('lane before porch',2.89,-1.42,False),('porch threshold',2.89,-.68,False),
          ('ground below shallow brick barrel',2.89,-.32,False),('closed inner grille',2.89,.12,True),
          ('porch right springing',4.03,-.47,True),('small lane door',-4.15,.12,True),
          ('south garden',6.25,8.35,False),('western arcade opening',5.45,2.04,False),
          ('second arcade opening',5.46,5.12,False),('third arcade opening',5.43,8.37,False),
          ('east arcade opening',5.43,11.48,False),('arcade pier',5.43,6.78,True),
          ('terrace above passage',4.93,10.74,False),('rear glazed wall at garden',4.18,10.74,True),
          ('east return beside passage',4.89,13.46,True),('north return',-5.7,3.36,True)]
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
         overviewBearing=48,overviewPitch=51,overviewZoom=18.9,maxDistance=630,lod_switch_in_m=510,lod_switch_out_m=665,
         navigation={'listed':False,'status':'沿西弄可接近西侧尖券车库与砖券门廊，南侧花园可走入底层券廊。'},
         placement={'status':'estimated','note':'新华路329弄17号地址点位于1248地块内，地块与OSM w864493245重合95.84%。西弄的两种砖券与绿色17号牌、南花园塔楼和地块图共同定位。深度、建筑高度、屋面和隐面仍含估计。'},
         partial_model=False,model_scope=read(a.manifest)['model_scope_zh'])
    contract['overview_focus_bounds_glb']={'min':[-5.50,.12,-11.9],'max':[5.55,9.65,.85]}
    contract['owner']={k:contract['owner'][k]for k in ['macro_id','feature_local_id']}
    for k in ['replacement_geometry','collision_geometry']:checked_geometry(contract[k],k,collision=k=='collision_geometry')
    write(a.out/'final-placement-contract.json',contract)
    write(a.out/'placement-geometry.json',dict(id=ID,source_sha256=sha(data),manifest_sha256=sha(a.manifest),contract_sha256=sha(a.out/'final-placement-contract.json'),
         script_sha256=sha(Path(__file__)),assets=assets,near_and_far=report,neighbors=others,
         ground_probes=probes,model_projection_m2=model.area,collision_m2=walk.area,old_vector_m2=src.area,mask_m2=mask.area))
    print('Checked',[(k,v['triangles'],v['peer_model_gap_m'])for k,v in report.items()],len(probes))
if __name__=='__main__':run()
