"""First triangle struck at the three roof windows, eaves and collectors."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from daren_photo_plane import camera_matrix
from glb_triangles import SerialScene
from triple_roof_gables import FACE,RETURN,SEAM,EDGE,FLASH,ROOF,FRAME,GLASS,DARK,PIPE

def check(asset):
    scene=SerialScene(asset)
    registration=json.loads((HERE/'three-gables.json').read_text())
    y=registration['front_y_m'];checks=[]
    def observe(label,org,ray,limit,expected,**details):
        hit=scene.ray(org,ray,limit);name=hit['material'] if hit else None
        checks.append(dict(label=label,expected=list(expected),first_material=name,passed=name in expected,**details))
    def front(label,x,z,expected):
        observe(label,[x,y-.55,z],[0,1,0],1.,expected,world_xz=[x,z])
    for i,w in enumerate(registration['window_controls']):
        l,r=w['x_interval_m'];b,t=w['z_interval_m'];cx=w['central_stile_x_m']
        for frac in [.17,.36,.58,.80]:
            z=b+(t-b)*frac
            for x,materials,title in [(l+.025,[FRAME],'left jamb'),(r-.023,[FRAME],'right jamb'),
                    (cx,[FRAME],'meeting stile'),((l+cx)/2,[DARK if i==0 else GLASS],'left light'),
                    ((r+cx)/2,[GLASS],'right light')]:
                front(f'Window {i+1} / {title}',x,z,materials)
        for x in np.linspace(l+.1,r-.1,4):
            front(f'Window {i+1} / upper rail',x,t-.030,[FRAME])
            front(f'Window {i+1} / lower rail',x,b+.035,[FRAME])
        xs=registration['crest_profile'];left,peak,right=[p['xz_m'] for p in xs[2*i:2*i+3]]
        for start,end in [(left,peak),(peak,right)]:
            for a in [.17,.43,.72,.87]:
                x=start[0]+a*(end[0]-start[0]);z=start[1]+a*(end[1]-start[1])
                front(f'Gable {i+1} / verge',x,z-.067,[EDGE])
                front(f'Gable {i+1} / grey facing behind verge',x,z-.18,[FACE,SEAM])
        for shelf in registration['course_edges_z_m']:
            for x in [l-.23,r+.22]:
                cap=left[1]+(peak[1]-left[1])*(x-left[0])/(peak[0]-left[0]) if x<peak[0] else right[1]+(peak[1]-right[1])*(right[0]-x)/(right[0]-peak[0])
                if shelf+.08<cap-.15:
                    front(f'Gable {i+1} / course lip',x,shelf+.012,[SEAM])
                    front(f'Gable {i+1} / course face',x,shelf+.075,[FACE])
        for x in [l-.19,r+.22]:front(f'Gable {i+1} / bottom flashing',x,registration['lower_z_m']-.019,[FLASH])
    for i,x in enumerate(registration['collector_mid_x_m']):
        top=registration['crest_profile'][2+2*i]['xz_m'][1]
        for z in np.linspace(14.23,top-.19,8):front(f'Valley {i+1} / pipe',x,z,[PIPE])
        for xx in [x-.11,x+.11]:front(f'Valley {i+1} / collecting mouth',xx,top-.01,[PIPE])
    # Rectified samples are traced in the original cover. They are converted back to original image
    # pixels before taking the first hit across all visible and occluding parts of the exported house.
    samples=[(78,163,[FACE,SEAM]),(194,167,[FACE,SEAM]),(273,168,[FACE,SEAM]),(371,167,[FACE,SEAM]),
             (453,169,[FACE,SEAM]),(564,168,[FACE,SEAM]),(123,205,[DARK]),(159,220,[GLASS]),
             (305,221,[GLASS]),(343,215,[GLASS]),(486,226,[GLASS]),(524,224,[GLASS]),
             (233,163,[PIPE]),(416,166,[PIPE]),(99,70,[EDGE]),(296,55,[None]),(296,65,[EDGE]),
             (541,60,[EDGE]),(60,257,[FLASH]),(449,257,[FLASH])]
    P=camera_matrix('video-cover');org=-np.linalg.solve(P[:,:3],P[:,3])
    for idx,(u,v,expected) in enumerate(samples,1):
        H=np.asarray(registration['rectification']['xz_from_rectified_pixel'])
        ax,az,ak=H@[u,v,1.]
        a=P@[ax/ak,y,az/ak,1];xy=a[:2]/a[2]
        observe(f'Original photograph / control {idx}',org,np.linalg.solve(P[:,:3],[*xy,1]),150.,expected,original_px=xy.round(3).tolist(),rectified_px=[u,v])
    for camera,coordinates in {'centre20-peaks':[(236,333,RETURN),(715,408,FACE)],
                               'east20-peaks':[(760,349,RETURN),(505,273,FACE),(680,291,FACE)],
                               'east15-peaks':[(768,332,RETURN),(535,295,FACE)]}.items():
        P=camera_matrix(camera);org=-np.linalg.solve(P[:,:3],P[:,3])
        for u,v,mat in coordinates:
            observe(camera+f' / {u},{v}',org,np.linalg.solve(P[:,:3],[u,v,1.]),150,[mat,SEAM] if mat==FACE else [mat],original_px=[u,v])
    return {**scene.asset,'method':'First physical triangle in the complete supplied GLB. Each photographed sample retains its original camera and pixel.', 'count':len(checks),'passed':all(c['passed'] for c in checks),'checks':checks}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('asset',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();result=check(a.asset);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
    bad=[(x['label'],x['first_material'])for x in result['checks'] if not x['passed']]
    print(result['count']-len(bad),'/',result['count'],bad)
    raise SystemExit(int(bool(bad)))
