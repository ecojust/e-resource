"""Test the nine camera frames against the delivered triangles and the two measured projections."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
from register_court import Camera
from check_porch_doors import Scene

HERE=Path(__file__).resolve().parent
def project(P,pts):
    hom=np.atleast_2d(pts)@P[:,:3].T+P[:,3]
    return hom[:,:2]/hom[:,2,None]
def projection(v):
    eye=np.array(v['eye']);forward=np.array(v['target'])-eye
    dist=np.linalg.norm(forward);forward/=dist
    right=np.cross(forward,v.get('world_up',[0.,0.,1.]));right/=np.linalg.norm(right)
    up=np.cross(right,forward);R=np.array([right,-up,forward])
    w,h=v['width'],v['height'];fx=dist*w/v['width_m']
    cx,cy=v.get('principal_point_edge_px',[w/2,h/2])
    K=np.array([[fx,v.get('skew_px',0.),cx-.5],[0.,fx/v.get('pixel_aspect_y',1),cy-.5],[0.,0.,1.]])
    return K@np.column_stack([R,-R@eye])
CONTROLS={
 'stone-flight':[(615,1072),(640,1047),(664,1011),(666,987),(703,951),(731,927),(698,913)],
 'glass-entrance':[(607,768),(681,737),(742,711),(729,792),(754,801),(735,816),(656,904),(747,904)],
 'tile-canopy':[(588,491),(621,519),(609,560),(665,562),(721,589),(598,619)],
 'stone-newels':[(379,856),(382,866),(389,925),(448,820),(468,775),(476,838)],
 'curved-windows':[(925,635),(926,850),(1010,803),(1123,853),(1018,701),(1058,763)],
 'wing-eaves':[(930,630),(1100,649),(1487,625),(1660,650),(1508,794),(925,865)]}
def check(mesh):
    scene=Scene(mesh);points=scene.tri.reshape(-1,3)
    poses=json.loads((HERE.parent/'source/cameras.json').read_bytes());rows={}
    main=Camera('fayhoo')
    for v in poses:
        w,h=v['width'],v['height'];eye=np.array(v['eye']);P=projection(v);k=v['name'];entry={}
        if k=='overview':
            uv=project(P,points)
            entry['all_vertex_margin_px']=[float(uv[:,0].min()),float(uv[:,1].min()),float(w-uv[:,0].max()),float(h-uv[:,1].max())]
        if 'reference' in v:
            camera=Camera(v['reference']);entry['max_photo_projection_difference_px']=float(np.max(abs(project(camera.P,points)-project(P,points))))
        if k in CONTROLS:
            subjects=[]
            for pixel in CONTROLS[k]:
                source=scene.ray(main.c,main.ray(pixel),70)
                if not source:
                    subjects.append({'source_pixel':pixel,'source_first_hit':None});continue
                p=np.array(source['point_enu_m']);d=p-eye;ray=scene.ray(eye,d/np.linalg.norm(d),70)
                uv=project(P,p)[0];within=bool(0<=uv[0]<w and 0<=uv[1]<h)
                offset=None if ray is None else float(np.linalg.norm(p-np.array(ray['point_enu_m'])))
                subjects.append({'source_pixel':pixel,'source_material':source['material'],'view_pixel':uv.tolist(),'inside':within,'first_hit':ray,'obstruction_offset_m':offset,'visible':bool(within and ray and ray['material']==source['material'] and offset<.065)})
            entry['subjects']=subjects
        rows[k]=entry
    return {'mesh_sha256':hashlib.sha256(mesh.read_bytes()).hexdigest(),'cameras_sha256':hashlib.sha256((HERE.parent/'source/cameras.json').read_bytes()).hexdigest(),'cameras':rows}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mesh',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args()
    d=check(a.mesh);a.out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    for k,row in d['cameras'].items():
        print(k,row.get('all_vertex_margin_px'),row.get('max_photo_projection_difference_px'),sum(v.get('visible',False)for v in row.get('subjects',[])),len(row.get('subjects',[])))
