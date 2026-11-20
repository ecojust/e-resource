"""Measure the original two-storey office against its independent city volume and nearby residence."""
from pathlib import Path
import argparse,runpy,sys
import shapely as geo
from shapely.geometry import Point,box
import numpy as np
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
ID='huangpu-former-british-consulate'
OFFICE=3111
RESIDENCE=1074

def run():
    arg=argparse.ArgumentParser(description=__doc__)
    arg.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    arg.add_argument('--work',type=Path,required=True)
    arg.add_argument('--out',type=Path,default=HERE)
    a=arg.parse_args();a.out.mkdir(exist_ok=True,parents=True)
    ref=PROJECT/'source/precise'/ID/'footprint-review.json';record=read(ref)
    ctx=PlacementMeshes(PROJECT,a.work,record);doc=read(a.manifest)
    assets,bounds,model,feet=ctx.decode_model(a.manifest)
    group=next(g for g in record['near_tiles']if OFFICE in g['feature_local_ids'])
    ground=ctx.footprints[OFFICE];res=ctx.footprints[RESIDENCE]
    mask=ground.buffer(.18,join_style=2)
    native={}
    for lod,(target,neighbors,method)in ctx.decode_group(group,OFFICE).items():
        former=ctx.project_faces(target);others=ctx.project_faces(neighbors)
        uncut=former.difference(mask).area
        assert uncut<.0005 and others.distance(mask)>2.00 and others.distance(model)>1.00,(lod,uncut,others.distance(mask),others.distance(model))
        native[lod]={'owner_triangles':len(target),'other_triangles':len(neighbors),'assignment':method,'owner_height_m':float(target[:,:,2].max()),'owner_projection_m2':former.area,'uncut_area_m2':uncut,'other_cut_m2':others.intersection(mask).area,'nearest_mesh_to_cut_m':others.distance(mask),'nearest_mesh_to_model_m':others.distance(model)}
    assert ground.distance(res)>25 and res.distance(mask)>25
    clear={i:p.distance(mask)for i,p in ctx.footprints.items()if i!=OFFICE and p.distance(mask)<39}
    assert min(clear.values())>2.3
    main=box(-8.4,.78,20.63,41.94)
    court=box(-21.88,5.9,-8.395,40.6)
    floor=geo.union_all([main,court]);gaps=[]
    for x in [(20.63-8.4)/2+i*(20.63+8.4)/9 for i in range(-2,3)]:
        gaps.append(box(x-1.105,.65,x+1.105,3.19))
    for y in [(41.55+1.25)/2+i*(41.55-1.25)/13 for i in range(-2,3)]:
        gaps.append(box(18.23,y-1.105,20.85,y+1.105))
    occupancy=floor.difference(geo.union_all(gaps))
    # The raised open garden terrace stays permeable except at the stone guard rails.
    rails=[box(25.11,11.52,25.40,17.99),box(25.11,24.73,25.40,30.84),
           box(20.50,11.51,25.36,11.79),box(20.50,30.58,25.36,30.86)]
    occupancy=geo.union_all([occupancy,*rails],grid_size=.001)
    assert model.distance(res)>25
    witnesses=[]
    for name,x,y,expected in [
        ('southern garden',6,-1.2,False),('south central arched recess',6,1.44,False),
        ('back of south arcade',6,3.40,True),('southern ashlar pier',7.70,1.22,True),
        ('east central terrace',23,21.36,False),('east central arcade',19.8,21.36,False),
        ('east arcade back wall',17.8,21.36,True),('east plinth behind end window',19.9,5,True),
        ('east stone guardrail',25.23,14,True),('west court',-17,26,True),
        ('north lawn',4,47,False),('independent residence',*res.representative_point().coords[0],True)]:
        test=Point(x,y);m=occupancy.covers(test);other=any(p.covers(test)for i,p in ctx.footprints.items()if i!=OFFICE)
        assert m or other if expected else not(m or other),(name,m,other)
        witnesses.append(dict(name=name,xy=[x,y],point=ctx.to_wgs(np.array([[x,y]]))[0].tolist(),expected='building'if expected else None,model=m,other=other))
    frame=record['author_frame'];c={'id':ID,**frame['anchor'],'heading':frame['runtime_heading_deg'],'scale':1,'altitude':0,'source_feature_ids':{'building':[record['owner']['source_key'].split(':')[1]],'building_part':[]},'owner':{'macro_id':record['frozen_macro'],'feature_local_id':OFFICE},'bounds_glb':bounds,'model_geometry_sha256':{key:v['sha256']for key,v in assets.items()},'replacement_geometry':ctx.wgs(mask),'collision_geometry':ctx.wgs(occupancy),'overviewBearing':-47,'overviewPitch':48,'overviewZoom':18.95,'maxDistance':620,'lod_switch_in_m':600,'lod_switch_out_m':760,'navigation':{'listed':False,'status':'原英国驻沪领事馆办公主楼，供俯瞰。'},'placement':{'status':'estimated','note':'将南边1873年办公主楼和历史法院外立面匹配到3111；1882年宅邸1074继续单独保留。檐高来自档案影像估算。'},'partial_model':True,'model_scope':doc['model_scope_zh']}
    for key in ('replacement_geometry','collision_geometry'):checked_geometry(c[key],key,collision=key=='collision_geometry')
    write(a.out/'final-placement-contract.json',c)
    out={'id':ID,'source_sha256':sha(ref),'script_sha256':sha(Path(__file__)),'manifest_sha256':sha(a.manifest),'model':assets,'native':native,'native_office_m2':ground.area,'model_projected_m2':model.area,'detail_outside_vector_m2':model.difference(ground).area,'model_floor_projections_m2':feet.area,'ground_occupancy_m2':occupancy.area,'separate_residence_m':ground.distance(res),'residence_to_model_m':model.distance(res),'other_vector_clearance_m':clear,'ground_probes':witnesses,'contract_sha256':sha(a.out/'final-placement-contract.json')}
    write(a.out/'placement-geometry.json',out);print(native,flush=True)
if __name__=='__main__':run()
