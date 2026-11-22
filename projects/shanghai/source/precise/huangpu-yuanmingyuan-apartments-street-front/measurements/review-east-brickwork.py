"""First-hit review of the photographed mortar joints, sashes and both gable edges in a delivered mesh."""
import argparse,hashlib,json,runpy,sys
from pathlib import Path

import numpy as np


def check(project,source,mesh):
    sys.path.insert(0,str(source))
    from east_photo_plane import CAMERAS
    from central_brickwork import JOINT,TILES,TIMBER,SHADOW,GLASS,STONE,PLASTER
    helpers=runpy.run_path(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py')
    tri,material,names,identity=helpers['load_triangles'](mesh)
    measured=source.parent/'measurements';features=json.loads((measured/'east-brickwork-features.json').read_bytes());reg=json.loads((measured/'central-arch-close-registration.json').read_bytes());to_front=np.linalg.inv(reg['front_to_detail_matrix'])
    materials=helpers['material_appearance'](mesh)['materials'];double=np.array([materials[n]['doubleSided']for n in names])[material]
    n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);xyz=tri.reshape(-1,3)
    def raycast(cam):
        eye=-np.linalg.solve(cam[:,:3],cam[:,3]);inv=np.linalg.inv(cam[:,:3]);q=xyz@cam[:,:3].T+cam[:,3];px=(q[:,:2]/q[:,2,None]).reshape(-1,3,2);mn=px.min(axis=1)-.002;mx=px.max(axis=1)+.002;cache={}
        def hit(pt):
            pt=np.asarray(pt);key=tuple(np.floor(pt/24.).astype(int))
            if key not in cache:
                lo=np.array(key)*24.;cache[key]=np.flatnonzero((mx>=lo).all(1)&(mn<=lo+24.).all(1))
            ii=cache[key];ray=inv@np.r_[pt,1.];ray/=np.linalg.norm(ray)
            ii=ii[(mn[ii]<=pt).all(1)&(mx[ii]>=pt).all(1)&(double[ii]|(n[ii]@ray<-1.e-12))]
            if not len(ii):return None,None
            i,t,p=helpers['first_hit'](tri[ii],eye,ray)
            if not np.isfinite(t):return None,None
            return names[material[ii[i]]],p
        return hit
    front=raycast(CAMERAS['2016_front']);street=raycast(CAMERAS['2014_oblique'])
    def detail(point):
        v=to_front@np.r_[point,1.];return front(v[:2]/v[2])
    rings={}
    for kind in ['upper_radial_joints','lower_wedge_joints']:
        samples=np.array([v['detail_px']for v in features[kind]])
        out=[]
        for j,point in enumerate(samples):
            m,d=detail(point);other=[samples[k]for k in (j-1,j+1)if 0<=k<len(samples)]
            sides=[detail((point+p)/2.) for p in other];heights=[q[1]for m2,q in sides if m2 in TILES and q is not None]
            recess=float(d[1]-min(heights)) if d is not None and heights else None
            out.append({'detail_px':point.tolist(),'first_surface':m,'flanking_surfaces':[m2 for m2,q in sides],
                        'visible_depth_m':None if recess is None else round(recess,6),
                        'passed':m in [JOINT,*TILES] and recess is not None and recess>.003})
        rings[kind]=out
    glazing=[]
    for tag,px,expected in [('upper fanlight left',(193,90),GLASS),('upper fanlight centre',(228,93),GLASS),('upper transom centre',(235,142),GLASS),('upper south lower pane',(157,182),GLASS),('upper north lower pane',(274,184),GLASS),('upper lower side light',(116,185),GLASS),('upper meeting stile',(216,187),TIMBER),('upper main rail',(158,162),TIMBER),('lower transom south',(140,439),GLASS),('lower transom north',(282,439),GLASS),('lower glass south',(127,517),GLASS),('lower glass north',(292,517),GLASS),('lower vertical pair joint',(213,515),TIMBER),('lower top frame',(155,484),TIMBER)]:
        u,v=px;mat,p=front([480+u/1.75,v/1.75]);glazing.append(dict(feature=tag,front_native_px=[480+u/1.75,v/1.75],expected=expected,first=mat,passed=mat==expected))
    gables=[]
    for key,row in features['gable_edges'].items():
        xy=np.array(row['native_edge_points']);sel=xy[np.round(np.linspace(0,len(xy)-1,7)[1:-1]).astype(int)];positions=[]
        for u,v in sel:
            delta=np.arange(-18.,18.5,.5);found=next((e for e in delta if street([u,v+e])[0] in [STONE,PLASTER]),None)
            positions.append(dict(photo_px=[u,v],error_native_px=found))
        gables.append(dict(slope=key,positions=positions))
    return dict(mesh=identity,arch_joints=rings,window_witnesses=glazing,gable_skyline=gables)


def release(project,source,folder):
    record={}
    for key,delivery,decoded in [('raw','raw.glb','raw.glb'),('web','full.glb','decoded-full.glb'),('lod','lod.glb','decoded-lod.glb')]:
        file=folder/delivery
        result=check(project,source,folder/decoded);rings=result['arch_joints']
        for label,expected in [('upper_radial_joints',116),('lower_wedge_joints',35)]:
            assert len(rings[label])==expected and all(r['passed'] for r in rings[label])
        witnesses=result['window_witnesses'];assert len(witnesses)==14 and all(r['passed']for r in witnesses)
        outline=[p['error_native_px']for seg in result['gable_skyline']for p in seg['positions']]
        assert len(outline)==20 and all(v is not None and abs(v)<=4.5 for v in outline)
        result['delivered']={'file':file.name,'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
        result['summary']={'round_arch_joint_first_hits':116,'segmental_arch_joint_first_hits':35,
                           'glazing_and_frame_witnesses':14,'gable_witnesses':20,'maximum_gable_error_native_px':max(map(abs,outline)),
                           'minimum_round_joint_depth_m':min(r['visible_depth_m']for r in rings['upper_radial_joints']),
                           'minimum_segmental_joint_depth_m':min(r['visible_depth_m']for r in rings['lower_wedge_joints'])}
        record[key]=result
    return {'subject':'圆明园公寓东立面中央砖券、窗扇及成对山墙',
            'method':'Compare the first visible triangle in both original cameras. For both arches the actual observed dark mortar and each neighbouring raised brick are sampled in the 2016 close-up and transferred through its 551 masonry tie points. Gable errors are vertical differences in native 4912 by 3264 street-image pixels. Relief values describe the estimated model geometry.',
            'camera':'east-front-cameras.json','feature_measurements':'east-brickwork-features.json',
            'close_registration':'central-arch-close-registration.json','variants':record}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for k in ['project','source','output']:ap.add_argument('--'+k,type=Path,required=True)
    inputs=ap.add_mutually_exclusive_group(required=True)
    inputs.add_argument('--mesh',type=Path);inputs.add_argument('--package',type=Path)
    a=ap.parse_args();d=release(a.project,a.source,a.package) if a.package else check(a.project,a.source,a.mesh)
    a.output.write_text(json.dumps(d,ensure_ascii=False,indent=1)+'\n')
