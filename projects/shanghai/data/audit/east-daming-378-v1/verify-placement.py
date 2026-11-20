"""Bind the public red-brick street front and pavilion, leaving the modern COSCO tower separate."""
from pathlib import Path
import argparse,sys,subprocess
import numpy as np,shapely
from shapely.geometry import LineString,MultiLineString,Point,box
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[2];sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
ID='hongkou-east-daming-road-378';OWNER=569;HEADQUARTERS=925
def run():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--work',type=Path,required=True)
    cli.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json');cli.add_argument('--out',type=Path,default=HERE)
    a=cli.parse_args();a.out.mkdir(parents=True,exist_ok=True);refs=PROJECT/'source/precise'/ID/'footprint-review.json'
    record=read(refs);ctx=PlacementMeshes(PROJECT,a.work,record);doc=read(a.manifest)
    assets,bounds,model,feet=ctx.decode_model(a.manifest)
    mask=shapely.union_all([box(-14.48,-.81,14.62,7.51),box(8.42,6.61,14.71,9.42),box(10.60,7.98,17.01,14.46)])
    assert model.difference(mask.buffer(.001)).area<.0001,(model.difference(mask).area,model.bounds)
    geom=shapely.union_all([box(-13.88,.008,13.90,7.24),box(11.42,7.23,13.88,9.05),box(11.59,9.02,16.03,13.46)],grid_size=.001)
    g=next(v for v in record['near_tiles']if OWNER in v['feature_local_ids']);source=ctx.footprints[OWNER]
    native={};far=None
    for k,(orig,others,method)in ctx.decode_group(g,OWNER).items():
        target=ctx.project_faces(orig);neighbors=ctx.project_faces(others)
        if k=='far':far=target
        remaining=target.difference(mask).area
        assert .73<remaining/target.area<.86 and neighbors.distance(mask)>12,(k,remaining/target.area,neighbors.distance(mask))
        native[k]={'source_triangles':len(orig),'peer_triangles':len(others),'assignment':method,'source_m2':target.area,'retained_m2':remaining,
                   'retained_fraction':remaining/target.area,'peer_cut_m2':neighbors.intersection(mask).area,'peer_model_m':neighbors.distance(model),'peer_cut_m':neighbors.distance(mask),'height_m':float(orig[:,:,2].max())}
    hq=next(v for v in record['near_tiles']if HEADQUARTERS in v['feature_local_ids']);protected={}
    # Inspect the modern tower's full near draw as well as its owner-keyed far geometry.
    ctx.link('baseline-near.glb.gz',ctx.files[Path(hq['file']).name]);write(a.work/'context-features.json',[dict(localId=i)for i in hq['feature_local_ids']])
    subprocess.run(['node',ctx.decoders/'map-decode-source.mjs'],check=True,env=ctx.env,stdout=subprocess.DEVNULL)
    for k in ('near','far'):
        tri=np.fromfile(a.work/f'baseline-{k}-triangles.f64',np.float64).reshape(-1,3,3)
        tri[:,:,:2]=tri[:,:,:2]@ctx.axes.T
        if k=='far':tri=tri[np.fromfile(a.work/'baseline-far-owners.u32',np.uint32)==HEADQUARTERS]
        surf=ctx.project_faces(tri);assert surf.distance(model)>22 and surf.distance(mask)>22
        protected[k]={'scope':'whole three-owner streamed tile'if k=='near'else'owner 925 only','triangles':len(tri),'distance_to_model_m':surf.distance(model),'distance_to_cut_m':surf.distance(mask),'intersection_m2':surf.intersection(mask).area}
    seams=[]
    for v,w in zip(mask.exterior.coords,list(mask.exterior.coords)[1:]):
        segment=far.intersection(LineString([v,w]));seams.extend([g for g in shapely.get_parts(segment)if isinstance(g,LineString) and g.length>.001])
    assert len(seams)>=3
    ready=read(ctx.files['READY.json']);caps={'base_m':0,'roof_m':native['far']['height_m'],'height_reference':[ready['origin_longitude'],ready['origin_latitude']],'far_sha256':sha(ctx.files['far.glb']),'geometry':ctx.wgs(MultiLineString(seams))}
    witnesses=[]
    checks=[('public roadway',0,-2,False),('main street wall',0,.4,True),('east street bay',-10,.7,True),('old office body behind street face',-3,5.8,True),
            ('west side ground bay',12.7,8,True),('tower foundation',15.3,11.4,True),('open adjacent courtyard',18,12.3,False),('tower beside the 569 outline',15.7,12.4,True),
            ('old building retained rear',0,26,True),('west garden pavement',17.9,23,False),('modern company headquarters',*ctx.footprints[HEADQUARTERS].representative_point().coords[0],True)]
    for name,x,y,expected in checks:
        pt=Point(x,y);floor=geom.covers(pt);res=source.difference(mask).covers(pt);other=any(t.covers(pt)for i,t in ctx.footprints.items()if i!=OWNER)
        assert bool(floor or res or other)==expected,(name,floor,res,other)
        witnesses.append(dict(name=name,xy=[x,y],point=ctx.to_wgs(np.array([[x,y]]))[0].tolist(),expected='building'if expected else None,modelObstacle=floor,cut=mask.covers(pt),retained=res,nearby_source=other))
    f=record['author_frame'];c={'id':ID,**f['anchor'],'heading':f['runtime_heading_deg'],'scale':1,'altitude':0,'owner':{'macro_id':record['frozen_macro'],'feature_local_id':OWNER},'source_feature_ids':{'building':[record['owner']['source_key'].split(':')[1]],'building_part':[]},'bounds_glb':bounds,'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'replacement_geometry':ctx.wgs(mask),'collision_geometry':ctx.wgs(geom),'source_section_caps':caps,'overviewBearing':130,'overviewPitch':46,'overviewZoom':19.45,'maxDistance':590,'lod_switch_in_m':560,'lod_switch_out_m':720,'navigation':{'listed':False,'status':'东大名路378号历史办公楼外观，供俯瞰。'},'placement':{'status':'estimated','note':'按历史街楼569、东大名路北侧视线、七开间和绿顶塔亭配准；同门牌30层现代总部925与东侧长廊保留。'},'partial_model':True,'model_scope':doc['model_scope_zh']}
    for key in ('replacement_geometry','collision_geometry'):checked_geometry(c[key],key,collision=key=='collision_geometry')
    write(a.out/'final-placement-contract.json',c)
    write(a.out/'placement-geometry.json',{'id':ID,'source_sha256':sha(refs),'script_sha256':sha(Path(__file__)),'manifest_sha256':sha(a.manifest),'assets':assets,'native':native,'same_address_modern_tower_and_tile':protected,'old_569_to_modern_925_source_m':source.distance(ctx.footprints[HEADQUARTERS]),'projected_model_m2':model.area,'tower_and_eaves_outside_569_m2':model.difference(source).area,'collision_m2':geom.area,'retained_owner_m2':source.difference(mask).area,'seams_m':[v.length for v in seams],'ground_probes':witnesses,'contract_sha256':sha(a.out/'final-placement-contract.json')})
    print(native,protected)
if __name__=='__main__':run()
