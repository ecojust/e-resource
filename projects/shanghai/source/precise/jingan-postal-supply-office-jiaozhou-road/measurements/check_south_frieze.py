"""Export the isolated relief or cast directly into an assembled street wall."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

D=Path(__file__).resolve().parent
sys.path[:0]=[str(D.parent/'source'),str(D.parents[1]/'hongkou-general-post-office/source/common'),
             str(D.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from south_bay_frieze import PALETTE,PLAN,BRICK,RIDGE,LIGHT,SHADE,GROOVE,READING,add_south_bay_frieze
from photo_architecture import Builder
from glb_triangles import SerialScene


def export(mesh,lod):
    b=Builder(PALETTE);add_south_bay_frieze(b,lod)
    for part in b.parts:
        v=np.array(part['vertices']);f=np.array(part['triangles'])
        e=Counter((i,j) for face in f for i,j in zip(face,np.roll(face,-1)))
        if any(k!=1 or e[j,i]!=1 for (i,j),k in e.items()):
            raise ValueError('Unpaired edge '+part['label'])
        t=(v-v.mean(0))[f]
        if np.sum(t[:,0]*np.cross(t[:,1],t[:,2]))<=0:
            raise ValueError('Non-positive volume '+part['label'])
    b.save(mesh,{'name':'Southern window frieze and pier ornaments','photos_embedded':False})
    return dict(objects=len(b.parts),triangles=sum(len(x['triangles'])for x in b.parts),
                oriented_closed_solids=True)


def check(mesh,head):
    scene=SerialScene(mesh);trials=[]
    def ray(name,x,z,match):
        hit=scene.ray([x,-1,z+head],[0,1,0],1.07)
        mat=hit and hit['material']
        trials.append(dict(point=name,relative_xz=[round(x,4),round(z,4)],
                     first_material=mat,first_y=hit and round(hit['distance_m']-1,6),
                     acceptable=match,passed=mat in match))
    low,top=PLAN['lower_z']
    for i,(a,b) in enumerate(PLAN['lower_red_x']):
        for t in [.09,.26,.34,.51,.66,.82,.97]:
            for p in [.26,.78]:
                ray('Separate spandrel panel',a+t*(b-a),low+p*(top-low),[BRICK,GROOVE])
        for t in PLAN['lower_lines'][i]:
            ray('Visible facing joint',a+t*(b-a),(low+top)/2,[GROOVE])
    for a,b in PLAN['lower_end_stones_x']:
        for t in [.25,.75]:ray('Pale terminal or stop',a+t*(b-a),(low+top)/2,[LIGHT])
    low,top=PLAN['upper_band_z']
    for i,(a,b) in enumerate(PLAN['upper_red_x']):
        for t,q in [[.35,.24],[.83,.5],[.55,.86],[.24,.64],[.54,.42],[.43,.66]]:
            ray('Returned relief on upper facing',a+t*(b-a),top-q*(top-low),[RIDGE])
        for t,q in [[.055,.36],[.94,.53] if i==0 else [.884,.52],[.55,.60]]:
            ray('Dark red field inside bends',a+t*(b-a),top-q*(top-low),[BRICK])
    a,b=PLAN['pale_frame_x'];c=(a+b)/2;z=(low+top)/2
    ray('Light frame north edge',a+.026,z,[LIGHT]);ray('Light frame south edge',b-.025,z,[LIGHT])
    ray('Inset square at the end of upper facing',c,z,[SHADE])
    for name,(a,b,c,d) in PLAN['pilaster_faces'].items():
        ray(name,(a+b)/2,(c+d)/2,[LIGHT if name.endswith('course')else SHADE])
        if not name.endswith('course'):ray(name+' edge',a+.007,(c+d)/2,[LIGHT])
    xa,xb=PLAN['bracket_x'];za,zb=PLAN['bracket_z']
    for t in [.2,.4,.65,.85]:
        ray('End pier support below the eaves',xa+t*(xb-xa),zb-.07,[LIGHT])
    material_for_photo={
        'red_west':[BRICK,GROOVE], 'red_east':[BRICK,GROOVE], 'middle_stop':[LIGHT],
        'upper_red_middle':[BRICK,RIDGE],'upper_red_south':[BRICK,RIDGE],
        'upper_end_square_frame':[SHADE],'upper_end_square_dark':[SHADE],
        'pier_lower_panel':[SHADE],'pier_small_west':[SHADE],'pier_small_east':[SHADE],
        'pier_cap_west_return':[LIGHT],
    }
    number_orthographic=len(trials)
    for view,camera in READING['cameras'].items():
        P=np.asarray(camera['matrix_reference_window_head']).copy()
        P[:,3]-=P[:,2]*head
        eye=np.linalg.solve(-P[:,:3],P[:,3])
        for label,allowed in material_for_photo.items():
            mark=camera['observations'].get(label)
            if not mark:
                continue
            uv=np.mean(mark['native_px'],axis=0)
            direction=np.linalg.solve(P[:,:3],[*uv,1.])
            hit=scene.ray(eye,direction,60)
            mat=hit and hit['material']
            trials.append(dict(point=label,view=view,pixel=uv.round(2).tolist(),acceptable=allowed,
                         first_material=mat,passed=mat in allowed))
    return dict(asset=scene.asset,head_z_m=head,count=len(trials),orthographic=number_orthographic,
                native_photo_first_hits=len(trials)-number_orthographic,unfiltered_first_hits=True,
                passed=all(t['passed']for t in trials),tests=trials)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mesh',type=Path);ap.add_argument('report',type=Path)
    ap.add_argument('--export',choices=['full','lod']);ap.add_argument('--head',type=float,default=PLAN['window_head_z_m'])
    args=ap.parse_args();extra=export(args.mesh,args.export=='lod') if args.export else {}
    result={**extra,**check(args.mesh,args.head)}
    args.report.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
    print(result.get('objects'),result['count'],[(r['point'],r.get('relative_xz',r.get('pixel')),r['first_material']) for r in result['tests'] if not r['passed']])
    raise SystemExit(int(not result['passed']))
