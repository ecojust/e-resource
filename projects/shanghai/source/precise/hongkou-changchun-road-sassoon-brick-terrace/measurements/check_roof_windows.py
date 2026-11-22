"""Inspect the first visible material on seven dormers, without discarding the main roof."""
import argparse,json,sys
from pathlib import Path
from math import cos,sin,radians
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from sassoon_roof_windows import metric_rows,CREAM,GLASS,WOOD,SOFFIT,TINT,LIGHT,TILE,TILE_RIM
from glb_triangles import SerialScene

def inspect(path):
    scene=SerialScene(path); results=[]; photo=[]
    def probe(label,start,dir,expected):
        hit=scene.ray(start,dir,15)
        mat=hit['material'] if hit else None
        results.append(dict(feature=label,origin=list(start),direction=list(dir),expected=expected,actual=mat,
                            first_hit=hit['point_enu_m']if hit else None,passed=mat in expected))
    for r in metric_rows():
        x0,x1=r['xl'],r['xr'];f=r['face'];z0,z1=r['sill'],r['head']
        tag=r['key'];metal=tag in ('G4','D1','D2')
        outer=LIGHT if metal else WOOD;glass=TINT if metal else GLASS
        if r['kind']=='gable':
            left,right=x0+.066,x1-.066
            ap=r['soffit'][1]
            for a in [.25,.5,.75]:
                x=ap[0]+(x0-ap[0])*(a*.17)
                z=z1+(ap[1]-z1)*a
                probe(tag+' cream tympanum', [x,f-1.4,z],[0,1,0],[CREAM])
            for x in (x0,x1):
                probe(tag+' lower timber post',[x,f-1.2,(r['base']+z0)*.5],[0,1,0],[WOOD])
            if tag in ('G2','G3'):
                sign=1 if tag=='G2' else -1
                side_x=x1 if sign==1 else x0
                width=min(r['depth']-.16,.69*(x1-x0))-.066
                for col in range(4):
                    y=f+.066+(col+.56)*width/4
                    z=z0+(z1-z0)*.40
                    probe(tag+' cheek light '+str(col+1),[side_x+sign*.55,y,z],[-sign,0,0],[GLASS])
        else:left,right=r['jamb']
        surround=.038 if metal else .05; n=r['columns'];count=r['rows']
        low,high=z0+surround+.004,z1-surround-.004
        size=(right-left-2*surround)/n
        for i in range(n):
            a=left+surround+i*size+.004;c=left+surround+(i+1)*size-.004
            angle=r['open_leaves'].get(i,0);t=radians(angle);hinge=a if angle<=0 else c
            rail=min(.031 if metal else .039,(c-a)*.16)
            def face_x(x,y):return hinge+(x-hinge)*cos(t)-y*sin(t)
            pl,pr=low+rail,high-rail
            for j in range(count):
                z=pl+(j+.47)*(pr-pl)/count
                x=face_x((a+c)*.5,.067)
                probe(f'{tag} leaf {i+1} pane {j+1}',[x,f-1.2,z],[0,1,0],[glass])
            for j in range(1,count):
                z=pl+j*(pr-pl)/count
                x=face_x((a+c)*.5,.032)
                probe(f'{tag} leaf {i+1} crossbar {j}',[x,f-1.2,z],[0,1,0],[outer])
        top=r['sky']
        for i in range(2):
            x,z=top[i];u,v=top[i+1]
            x,z=.43*x+.57*u,.43*z+.57*v
            probe(f'{tag} roof slope {i+1}',[x,f+.19,z+.75],[0,0,-1],[TILE,TILE_RIM])
    camera=np.asarray(json.loads((HERE/'north-frontage-cameras.json').read_bytes())['front'])
    eye=np.linalg.solve(camera[:,:3],-camera[:,3])
    r=next(q for q in metric_rows() if q['key']=='G4')
    z=(r['base']+r['sill'])*.5
    for note,x in [('western post',r['xl']),('eastern post',r['xr'])]:
        point=np.array([x,r['face']-.068,z])
        direction=point-eye; direction/=np.linalg.norm(direction)
        start=point-2.5*direction
        hit=scene.ray(start,direction,3.0)
        uv=camera@np.r_[point,1.]
        photo.append(dict(feature='G4 '+note,method='camera ray toward the lower timber post, with the entire facade present',
                          original_image_xy=(uv[:2]/uv[2]).tolist(),expected=WOOD,
                          first_material=hit['material'] if hit else None,
                          first_hit=hit['point_enu_m'] if hit else None,matched=bool(hit and hit['material']==WOOD)))
    return {**scene.asset,'photo_camera_checks':photo,'rays':len(results),'passed':all(q['passed'] for q in results),
            'matched':sum(q['passed'] for q in results),'results':results}
if __name__=='__main__':
    arg=argparse.ArgumentParser(description=__doc__);arg.add_argument('output',type=Path);arg.add_argument('models',nargs='+',type=Path);q=arg.parse_args()
    rows=[inspect(p)for p in q.models];q.output.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    for r in rows:
        print(r['file'],r['matched'],r['rays'],[(p['feature'],p['actual'])for p in r['results']if not p['passed']][:16])
    raise SystemExit(0 if all(r['passed']for r in rows)else 1)
