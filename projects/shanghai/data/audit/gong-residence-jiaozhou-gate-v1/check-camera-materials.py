"""Test the public selection camera at the actual 522 gate and the two source city mesh detail levels."""
from pathlib import Path
from argparse import ArgumentParser
from contextlib import ExitStack
import gzip,math,os,runpy,sys
import numpy as np
import shapely as geo
from shapely.geometry import Point,shape
from trimesh.triangles import closest_point
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
model_ray=runpy.run_path(str(HERE.parent/'postal-office-v1/independent-glb-review-helpers.py'))
original_ray=runpy.run_path(str(HERE.parent/'daxin-tobacco-northeast-tower-v1/check-physical-city-rays.py'))['crossings']
cam=runpy.run_path(str(HERE.parent/'pure-heart-church-v1/check-overview-sightlines.py'))
ID='jingan-gong-residence-jiaozhou-gate'
IRON='Graphite wrought iron';GOLD='Ochre gilt iron tips';TRIM='Stone nosing'
MARKS=[
 ('outer arch raised coping',[0,-.063,6.44],[.2,.02,.10],[TRIM]),
 ('left inner arch rim',[-1.54,-.056,4.89],[.2,.040,.26],[TRIM,'Limestone coloured render']),
 ('fan central wrought semicircle',[.15,.235,4.10],[.15,.050,.135],[IRON]),
 ('left fan paired scroll',[-.88,.244,4.51],[.30,.065,.24],[IRON]),
 ('light right springer',[2.24,-.050,3.53],[.16,.04,.14],['Limestone coloured render','Recessed rendered panel']),
 ('left brick pier',[-2.26,-.007,1.58],[.22,.04,.15],['Umber brick','Russet brick','Smoked brick']),
 ('right near-closed gilt vine',[.48,.67,2.03],[.34,.16,.60],[GOLD]),
 ('right near-closed meeting stile',[.042,.717,1.83],[.085,.11,.26],[IRON]),
 ('left open leaf meeting stile',[-1.52,2.21,1.56],[.15,.16,.84],[IRON]),
 ('activity centre tablet',[-2.24,-.046,2.92],[.16,.025,.11],['Bronze activity centre plaque']),
 ('street address tablet',[-2.24,-.043,2.56],[.13,.02,.08],['Bronze 522 address plaque']),
 ('municipal heritage tablet',[2.24,-.047,2.65],[.20,.023,.15],['Pale heritage plaque'])]
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
    a=p.parse_args();ref=read(PROJECT/'source/precise'/ID/'footprint-review.json');m=PlacementMeshes(PROJECT,a.work,ref);c=read(a.contract)
    fb=read(a.fallback);assert fb['contract_sha256']==sha(a.contract)
    cut=geo.transform(shape(c['replacement_geometry']),m.to_xy)
    tab=read_gz=m.files['feature-table.json.gz'];import json
    heights={s['localId']:s['height']for s in json.loads(gzip.decompress(tab.read_bytes()))['features']}
    def local_to_enu(g):return geo.transform(g,lambda xy:xy@m.axes)
    volumes=[(i,local_to_enu(g.difference(cut) if i==2100 else g),heights[i]) for i,g in m.footprints.items()if g.distance(Point(0,0))<145]
    fbvol=[(str(v['id'])+'#'+str(v['component']),local_to_enu(geo.transform(shape(v['outline']),m.to_xy).difference(cut)),float(v['height']))for v in fb['nearby']]
    marks=list(MARKS);manifest=read(a.manifest)
    mats=model_ray['material_appearance'](a.manifest.parent/'raw.glb')['materials']
    enamel='Ochre yellow sign enamel'
    assert enamel in mats
    marks.extend([('left inner yellow caution disc',[-1.786,.54,2.22],[.018,.12,.18],[enamel]),
                  ('caution sign photographed 慢 strokes',[-1.7835,.403,2.223],[.009,.12,.14],[IRON])])
    street_mark=('walkable lane through the open leaf',[-.90,2.20,1.35],[0,0,0],[])
    pts=[(name,*map(float,np.array(pos[:2])@m.axes),pos[2])for name,pos,_,_ in marks+[street_mark]]
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
            # Independent ray to a physical point inside the photographed doorway.
            _,target,_,_=street_mark;direction=np.array(target)-eye;length=np.linalg.norm(direction)
            ix,dist,_=first_front(t,eye,direction/length)
            aperture=bool(not np.isfinite(dist)or dist>=length-.005)
            hinge=np.array([1.762,.506,1.80]);hingedir=hinge-eye
            ix,dist,_=first_front(t,eye,hingedir/np.linalg.norm(hingedir))
            hinge_observation=dict(feature='right hinge viewed from public selection',first_material=names[mi[ix]] if np.isfinite(dist) else None,
                                  target_m=hinge.tolist(),shortfall_m=float(np.linalg.norm(hingedir)-dist) if np.isfinite(dist) else None)
            visible.append(dict(view=v0['view'],local_camera_eye=eye.tolist(),targets=rows,clear=sum(q['visible']for q in rows),aperture_unobstructed=aperture,aperture_target=target,right_hinge_separate_observation=hinge_observation))
        model_rows.append(dict(role=role,delivery_sha256=manifest['assets'][role]['sha256'],decoded_sha256=doc['sha256'],triangles=len(t),views=visible))
    write(a.out/'model-sightlines.json',dict(contract_sha256=sha(a.contract),geometry=model_rows))
    print('model',[(r['role'],[(v['clear'],v['aperture_unobstructed'],[t['feature']for t in v['targets'] if not t['visible']])for v in r['views']])for r in model_rows],flush=True)
    assert all(v['clear']==len(marks) and v['aperture_unobstructed']for r in model_rows for v in r['views'])
    physical=[]
    for grp,owner in zip(ref['near_tiles']+ref['preserved_near_tiles'],[2100,1778]):
        with ExitStack()as hold:
            for lod in ('near','far'):
                for ext in ('owners.u32','triangles.f64'):
                    path=a.work/f'baseline-{lod}-{ext}';assert not path.is_symlink();fd=os.memfd_create('gong318-physical-rays');hold.callback(os.close,fd);path.symlink_to(f'/proc/{os.getpid()}/fd/{fd}');hold.callback(path.unlink)
            native=m.decode_group(grp,owner)
        for lod,(own,other,assign)in native.items():
            rows=[]
            for r in model_rows:
                for v0 in r['views']:
                    eye=np.array(v0['local_camera_eye']);indices=[(h['feature'],h['hit']['physical_endpoint_m'])for h in v0['targets']]+[(street_mark[0],street_mark[1])]
                    for label,pt in indices:
                        _,oldhits=original_ray(eye,np.array(pt),own);_,otherhits=original_ray(eye,np.array(pt),other)
                        dropped=sum(1 for hit in oldhits if owner==2100 and cut.buffer(.0003).covers(Point(hit[:2])))
                        retained=len(oldhits)-dropped+len(otherhits);assert retained==0,(lod,owner,label,len(oldhits),len(otherhits),retained)
                        rows.append(dict(delivery=r['role'],view=v0['view'],feature=label,source_intersections=len(oldhits),removed=dropped,neighbor_hits=len(otherhits),retained_blockers=int(retained)))
            physical.append(dict(owner=owner,group=grp['id'],lod=lod,source_triangles=len(own),neighbor_triangles=len(other),checks=rows))
    write(a.out/'original-city-sightlines.json',dict(contract_sha256=sha(a.contract),original_groups=physical))
    print('physical',sum(len(g['checks'])for g in physical),flush=True)
if __name__=='__main__':main()
