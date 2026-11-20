"""Bind the named crescent and check both real local meshes against the neighbouring blocks."""
from argparse import ArgumentParser
from pathlib import Path
import sys,subprocess
import numpy as np
import shapely as geo
from shapely.geometry import Polygon
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[2];sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
ID='jingan-yates-apartments';OWNER=1964

def main():
    cli=ArgumentParser(description=__doc__);cli.add_argument('--manifest',required=True,type=Path);cli.add_argument('--work',required=True,type=Path);cli.add_argument('--out',type=Path,default=HERE);args=cli.parse_args();args.out.mkdir(exist_ok=True,parents=True)
    ref=read(PROJECT/'source/precise'/ID/'footprint-review.json');s=PlacementMeshes(PROJECT,args.work,ref);assets,bounds,model,ground=s.decode_model(args.manifest);source=s.footprints[OWNER];cut=source.buffer(.17,join_style='mitre')
    mask=[];probes=[]
    for door in ref['author_frame']['entry_frames']:
        origin,t,n=[np.array(door[k])for k in ('center_wall_xy_m','tangent_xy','outward_xy')]
        def xy(u,v):return (origin+t*u+n*v).tolist()
        half=door['clear_width_m']/2-.13;mask.append(Polygon([xy(-half,.65),xy(half,.65),xy(half,-.64),xy(-half,-.64)]))
        for name,u,v,solid in [('street',.20,1.5,False),('recess',.26,-.32,False),('closed door',.26,-.80,True),('jamb',half+.26,-.04,True)]:probes.append((door['name']+' '+name,xy(u,v),solid))
    # Entrance floors at 9 cm above the datum are walkable; the two deeper closed doors stop the route.
    collision=ground.difference(geo.union_all(mask)).simplify(.010);assert collision.is_valid
    group=next(g for g in ref['near_tiles']if OWNER in g['feature_local_ids']);ids=group['feature_local_ids'];s.link('baseline-near.glb.gz',s.files[Path(group['file']).name]);s.link('baseline-far.glb',s.files['far.glb']);s.link('macro-READY.json',s.files['READY.json']);write(s.work/'context-features.json',[{'localId':i}for i in ids]);subprocess.run(['node',s.decoders/'map-decode-source.mjs'],env=s.env,check=True,stdout=subprocess.DEVNULL)
    variants={}
    for kind in ['near','far']:
        tris=np.fromfile(s.work/f'baseline-{kind}-triangles.f64',np.float64).reshape(-1,3,3);tris[:,:,:2]=tris[:,:,:2]@s.axes.T
        if kind=='far':owners=np.fromfile(s.work/'baseline-far-owners.u32',np.uint32);assignment={'method':'per-vertex _FEATURE_ID_0'}
        else:
            pts=geo.points(tris[:,:,:2].mean(axis=1));dist=np.stack([geo.distance(pts,s.footprints[i])for i in ids],axis=1);owners=np.array(ids)[dist.argmin(1)];d=np.sort(dist[owners==OWNER],axis=1);diff=np.min(d[:,1]-d[:,0]);assert d[:,0].max()<.09 and diff>.90
            assignment={'method':'nearest original owner polygon in the actual near group','maximum_owner_distance_m':float(d[:,0].max()),'minimum_owner_advantage_m':float(diff)}
        target=tris[owners==OWNER];other=tris[owners!=OWNER];old=s.project_faces(target);context=s.project_faces(other);assert cut.covers(old) and cut.distance(context)>.75 and model.distance(context)>.65
        variants[kind]=dict(group=group['id'],target_triangles=len(target),context_triangles=len(other),source_area_m2=old.area,source_outside_clip_m2=old.difference(cut).area,cut_to_nearest_other_real_mesh_m=cut.distance(context),model_to_nearest_other_real_mesh_m=model.distance(context),assignment=assignment)
    neighbors=[]
    for i in (152,1293,1683,2103):
        other=s.footprints[i];assert model.distance(other)>.65 and cut.distance(other)>.70;neighbors.append(dict(local_id=i,estimated_height_m=next(z['height']for z in ref['owners']if z['local_id']==i),model_to_source_m=model.distance(other),cut_to_source_m=cut.distance(other)))
    probes.extend([('apartment upper floors above bank',[1,2],True),('rear ground outside wall',[0,7.64],False),('curved frontage apron',[0,-10.43],False),('Wujiang street end',[-18.9,4.50],False)])
    outcomes=[]
    for title,coords,solid in probes:
        result=collision.covers(geo.Point(coords));assert result==solid,(title,coords,result);outcomes.append(dict(name=title,xy=coords,model_obstacle=result,source_cut=cut.covers(geo.Point(coords))))
    owner=next(r for r in ref['owners']if r['local_id']==OWNER);contract=dict(id=ID,owner=dict(macro_id=ref['frozen_macro'],feature_local_id=OWNER),source_feature_ids=dict(building=[owner['key'][9:]],building_part=[]),replacement_geometry=s.wgs(cut),collision_geometry=s.wgs(collision),lng=s.lon,lat=s.lat,heading=ref['author_frame']['runtime_heading_deg'],scale=1,altitude=0,bounds_glb=bounds,model_geometry_sha256={k:v['sha256']for k,v in assets.items()},overviewBearing=240,overviewPitch=46,overviewZoom=18.55,maxDistance=680,lod_switch_in_m=650,lod_switch_out_m=800,navigation=dict(listed=False,status='从石门一路路口观察弧形公寓和801、803号入口。'),placement=dict(status='map-aligned',note='实名源1964同孚大楼，南京西路801号曾为中国银行西区分行。公寓803号、现状银行及三面道路相合。西邻152、北侧小构筑物1293和路口对面的德义大楼独立。'),partial_model=True,model_scope=read(args.manifest)['scope'])
    for name in ['replacement','collision']:checked_geometry(contract[name+'_geometry'],name,collision=(name=='collision'))
    write(args.out/'final-placement-contract.json',contract);write(args.out/'placement-geometry.json',dict(id=ID,assets=assets,manifest_sha256=sha(args.manifest),source_m2=source.area,model_m2=model.area,ground_m2=collision.area,mask_m2=cut.area,variants=variants,neighbors=neighbors,ground_probes=outcomes,checker_sha256=sha(Path(__file__)),decoder_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))

if __name__=='__main__':main()
