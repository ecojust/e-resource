"""Resolve nine display frames against the three original camera matrices and actual first-hit surfaces."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import numpy as np
from register_house import Camera

HERE=Path(__file__).resolve().parent
HELPER=HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
def projection(view):
    eye=np.array(view['eye']);forward=np.array(view['target'])-eye
    dist=np.linalg.norm(forward);forward/=dist
    side=np.cross(forward,view.get('world_up',[0.,0.,1.]));side/=np.linalg.norm(side)
    up=np.cross(side,forward);R=np.array([side,-up,forward]);w,h=view['width'],view['height']
    fx=w*dist/view['width_m'];cx,cy=view.get('principal_point_edge_px',[w/2,h/2])
    K=np.array([[fx,view.get('skew_px',0.),cx-.5],[0.,fx/view.get('pixel_aspect_y',1.),cy-.5],[0.,0.,1.]])
    return K@np.column_stack([R,-R@eye])

def project(p,points):
    h=np.asarray(points)@p[:,:3].T+p[:,3]
    return h[:,:2]/h[:,2,None]

def check(mesh):
    scene=runpy.run_path(str(HELPER))['SerialScene'](mesh);points=scene.tri.reshape(-1,3)
    config=HERE.parent/'source/cameras.json'
    survey=json.loads((HERE/'house-cameras.json').read_bytes())
    views=json.loads(config.read_bytes());result={}
    subjects={
      'paired-door':('84',[(460,672),(480,685),(510,680),(521,746),(485,799)]),
      'number-two':('84',[(457,671),(463,674)]),
      'corner-sashes':('84',[]),'street-windows':('86',[]),'lane-windows':('84',[])}
    for k,cam,keys,level in [('corner-sashes','84',['j3_0_0','j3_1_1','j3_2_0','j3_3_0'],3),
                             ('street-windows','86',['A3TR','B3TL','C4TL','E3TR'],3)]:
        for name in keys:
            if name in survey['points']:subjects[k][1].append(Camera(cam).pixel(survey['points'][name]).tolist())
    # Interior samples on the left-hand wing in native photo 84.
    subjects['lane-windows'][1].extend([(176,363),(233,377),(296,416),(375,414)])
    for v in views:
        P=projection(v);key=v['name'];w,h=v['width'],v['height'];eye=np.array(v['eye']);row={}
        if 'reference' in v:
            c=Camera(v['reference']);pad=project(c.P,points)
            row['reference']=v['reference']
            row['photo_reprojection_max_px']=float(np.max(np.abs(project(P,points)-pad)))
        elif key=='overview':
            uv=project(P,points);row['margin_px']=[float(uv[:,0].min()),float(uv[:,1].min()),float(w-uv[:,0].max()),float(h-uv[:,1].max())]
        elif key in subjects:
            cam_key,pixels=subjects[key];c=Camera(cam_key);row['samples']=[]
            for uv in pixels:
                first=scene.ray(c.c,c.ray(uv),100.)
                if first is None:row['samples'].append({'source':uv,'first':None});continue
                point=np.array(first['point_enu_m']);pos=project(P,[point])[0]
                hit=scene.ray(eye,point-eye,100.);offset=None if not hit else float(np.linalg.norm(point-hit['point_enu_m']))
                row['samples'].append({'source':uv,'material':first['material'],'view_px':pos.tolist(),
                                       'first':hit and hit['material'],'obstruction_distance_m':offset,
                                       'in_frame':bool(0<=pos[0]<w and 0<=pos[1]<h),'same_surface':bool(hit and offset<.085)})
        result[key]=row
    return {'mesh_sha256':scene.asset['sha256'],'cameras_sha256':hashlib.sha256(config.read_bytes()).hexdigest(),'views':result}

if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('mesh',type=Path);cli.add_argument('report',type=Path);args=cli.parse_args()
    data=check(args.mesh);args.report.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    for k,r in data['views'].items():print(k,r.get('margin_px'),r.get('photo_reprojection_max_px'),[(s.get('in_frame'),s.get('same_surface')) for s in r.get('samples',[])])
