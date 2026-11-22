"""Test the public selection camera at the Xinen west church facade and the two source city mesh detail levels."""
from pathlib import Path
from argparse import ArgumentParser
from contextlib import ExitStack
import gzip,math,os,runpy,sys
import numpy as np
import shapely as geo
from shapely.geometry import Point,shape
from trimesh.triangles import closest_point
HERE=Path(__file__).resolve().parent;PROJECT=Path(__import__('os').environ['SHANGHAI_PROJECT_ROOT']) if 'SHANGHAI_PROJECT_ROOT' in __import__('os').environ else HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
model_ray=runpy.run_path(str(PROJECT/'data/audit'/'postal-office-v1/independent-glb-review-helpers.py'))
original_ray=runpy.run_path(str(PROJECT/'data/audit'/'daxin-tobacco-northeast-tower-v1/check-physical-city-rays.py'))['crossings']
cam=runpy.run_path(str(PROJECT/'data/audit'/'pure-heart-church-v1/check-overview-sightlines.py'))
ID='jingan-xinen-church-west-porch'
MARKS=[('screen north crimson character', [-1.68, 0.287, 2.99], [0.33, 0.05, 0.32], ['crimson characters']), ('screen middle crimson character', [0, 0.287, 3], [0.33, 0.05, 0.32], ['crimson characters']), ('screen south crimson character', [1.7, 0.287, 3], [0.33, 0.05, 0.32], ['crimson characters']), ('porch masonry screen', [0.84, 0, 1.32], [0.22, 0.035, 0.2], ['granite porch']), ('porch letter screen recessed plane', [1.98, 0.307, 2.64], [0.15, 0.014, 0.22], ['dark letter screen']), ('English upper inscription', [0.02, -0.032, 4.86], [0.29, 0.035, 0.15], ['incised lettering']), ('English lower inscription', [0, -0.032, 4.49], [0.24, 0.025, 0.15], ['incised lettering']), ('porch upper drip', [1.91, -0.18, 5.24], [0.26, 0.062, 0.07], ['granite dressing']), ('southern arch outer rim', [3.69, 3.17, 3.86], [0.06, 0.31, 0.14], ['granite dressing']), ('southern arch front pier', [3.66, 0.53, 2.1], [0.04, 0.15, 0.26], ['granite porch']), ('stone lancet southern mullion', [1.11, 6.22, 8.59], [0.12, 0.055, 0.34], ['granite dressing']), ('lancet dark glazing', [-0.15, 6.484, 8.04], [0.17, 0.023, 0.2], ['grey glazing', 'green grey glazing']), ('iron glazing bars', [0.37, 6.393, 9.02], [0.029, 0.05, 0.17], ['iron frame']), ('pointed hood', [-0.35, 6.23, 10.91], [0.24, 0.09, 0.16], ['granite dressing', 'weathered fascia']), ('south upper brick reveal', [3.73, 6.36, 8.08], [0.18, 0.03, 0.21], ['blue grey brick', 'brick shading']), ('upper brick field', [-1.54, 6.36, 12.27], [0.32, 0.038, 0.32], ['blue grey brick', 'brick shading']), ('gable pitched coping northern edge', [-1.48, 6.196, 14.05], [0.21, 0.06, 0.26], ['granite dressing']), ('red ridge and arms', [0.36, 6.245, 17.44], [0.13, 0.04, 0.12], ['cross red'])]
def first_front(tri,eye,direction):
    normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);cs=np.flatnonzero(normal@direction< -1.e-10)
    if not len(cs):return -1,math.inf,np.full(3,np.nan)
    i,d,x=model_ray['first_hit'](tri[cs],eye,direction);return cs[i],d,x

def material_ray(eye,trial,expected,data):
    t,mi,names,lows,highs=data;unit=trial-eye;distance=np.linalg.norm(unit);unit/=distance
    ok=np.all(highs>=np.minimum(eye,trial)-.04,axis=1)&np.all(lows<=np.maximum(eye,trial)+.04,axis=1)
    ids=np.flatnonzero(ok);ix,dist,end=first_front(t[ids],eye,unit)
    if not np.isfinite(dist) or abs(dist-distance)>.011 or names[mi[ids[ix]]]not in expected:return
    return dict(triangle=int(ids[ix]),first_material=names[mi[ids[ix]]],physical_endpoint_m=end.round(6).tolist(),first_hit_error_m=float(abs(dist-distance)))
def main():
    p=ArgumentParser(description=__doc__)
    for k in ('manifest','work','contract','fallback','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();ref=read(Path(os.environ.get('XINEN_FOOTPRINT',PROJECT/'source/precise'/ID/'footprint-review.json')));m=PlacementMeshes(PROJECT,a.work,ref);c=read(a.contract)
    fb=read(a.fallback);assert fb['contract_sha256']==sha(a.contract)
    cut=geo.transform(shape(c['replacement_geometry']),m.to_xy)
    tab=read_gz=m.files['feature-table.json.gz'];import json
    heights={s['localId']:s['height']for s in json.loads(gzip.decompress(tab.read_bytes()))['features']}
    def local_to_enu(g):return geo.transform(g,lambda xy:xy@m.axes)
    volumes=[(i,local_to_enu(g.difference(cut) if i==3149 else g),heights[i]) for i,g in m.footprints.items()if g.distance(Point(0,0))<145]
    fbvol=[(str(v['id'])+'#'+str(v['component']),local_to_enu(geo.transform(shape(v['outline']),m.to_xy).difference(cut)),float(v['height']))for v in fb['nearby']]
    marks=list(MARKS);manifest=read(a.manifest)
    pts=[(name,*map(float,np.array(pos[:2])@m.axes),pos[2])for name,pos,_,_ in marks]
    rad=math.pi/180*6371008.8
    def views(v):
        return [cam['evaluate'](c,dict(width=w,height=h,insets=dict(zip(['left','right','top','bottom'],pads))),label,v,m.lon,m.lat,rad*math.cos(math.radians(m.lat)),rad,pts) for label,w,h,pads in cam['VIEWS']]
    v=views(volumes);vf=views(fbvol)
    write(a.out/'overview-sightlines.json',dict(views=v,fallback_views=vf,contract_sha256=sha(a.contract),original_footprints=len(volumes),actual_camera_sha=sha(PROJECT/'src/candidate-overview-camera.js')))
    assert all(x['clear_count']==len(pts) for x in v+vf),[(x['view'],[q for q in x['probes']if not q['clear']])for x in v+vf]
    model_rows=[]
    for role,name in [('raw','raw.glb'),('full','decoded-full.glb'),('lod','decoded-lod.glb')]:
        t,mi,names,doc=model_ray['load_triangles'](a.manifest.parent/name);assert len(t)==manifest['assets'][role]['triangles']
        lows,highs=t.min(1),t.max(1);cent=t.mean(1);mesh=(t,mi,names,lows,highs)
        visible=[]
        for v0 in v:
            e,n,z=v0['camera_enu'];eye=np.r_[np.array([e,n])@m.axes.T,z];rows=[]
            for label,pos,r,materials in marks:
                pos=np.asarray(pos);r=np.asarray(r);alloc=np.isin(mi,[i for i,x in enumerate(names)if x in materials]);alloc&=np.all(highs>=pos-r,axis=1)&np.all(lows<=pos+r,axis=1)
                ids=np.flatnonzero(alloc);assert len(ids),(label,materials)
                surf=closest_point(t[ids],np.repeat(pos[None,:],len(ids),axis=0));options=.94*surf+.06*cent[ids];hit=None
                for i in np.argsort(np.linalg.norm((pos-options)/r,axis=1))[:75]:
                    for point in (options[i],cent[ids[i]]):
                        if np.any(np.abs(pos-point)>1.04*r):continue
                        hit=material_ray(eye,point,materials,mesh)
                        if hit:break
                    if hit:break
                rows.append(dict(feature=label,visible=hit is not None,hit=hit))
            visible.append(dict(view=v0['view'],local_camera_eye=eye.tolist(),targets=rows,clear=sum(q['visible']for q in rows)))
        model_rows.append(dict(role=role,delivery_sha256=manifest['assets'][role]['sha256'],decoded_sha256=doc['sha256'],triangles=len(t),views=visible))
    write(a.out/'model-sightlines.json',dict(contract_sha256=sha(a.contract),geometry=model_rows))
    print('model',[(r['role'],[(v['clear'],[t['feature']for t in v['targets']if not t['visible']]) for v in r['views']])for r in model_rows],flush=True)
    assert all(v['clear']==len(marks)for r in model_rows for v in r['views'])
    physical=[]
    for grp,owner in zip(ref['near_tiles'],[3149]):
        with ExitStack()as hold:
            for lod in ('near','far'):
                for ext in ('owners.u32','triangles.f64'):
                    path=a.work/f'baseline-{lod}-{ext}';assert not path.is_symlink();fd=os.memfd_create('xinen323-city-rays');hold.callback(os.close,fd);path.symlink_to(f'/proc/{os.getpid()}/fd/{fd}');hold.callback(path.unlink)
            native=runpy.run_path(str(HERE/'verify-placement.py'))['decode_corner_group'](m,grp,cut)
        for lod,(own,other,assign)in native.items():
            rows=[]
            for r in model_rows:
                for v0 in r['views']:
                    eye=np.array(v0['local_camera_eye']);indices=[(h['feature'],h['hit']['physical_endpoint_m'])for h in v0['targets']]
                    for label,pt in indices:
                        _,oldhits=original_ray(eye,np.array(pt),own);_,otherhits=original_ray(eye,np.array(pt),other)
                        dropped=sum(1 for hit in oldhits if owner==3149 and cut.buffer(.0003).covers(Point(hit[:2])))
                        retained=len(oldhits)-dropped+len(otherhits);assert retained==0,(lod,owner,label,len(oldhits),len(otherhits),retained)
                        rows.append(dict(delivery=r['role'],view=v0['view'],feature=label,source_intersections=len(oldhits),removed=dropped,neighbor_hits=len(otherhits),retained_blockers=int(retained)))
            physical.append(dict(owner=owner,group=grp['id'],lod=lod,source_triangles=len(own),neighbor_triangles=len(other),checks=rows))
    write(a.out/'original-city-sightlines.json',dict(contract_sha256=sha(a.contract),original_groups=physical))
    print('physical',sum(len(g['checks'])for g in physical),flush=True)
if __name__=='__main__':main()
