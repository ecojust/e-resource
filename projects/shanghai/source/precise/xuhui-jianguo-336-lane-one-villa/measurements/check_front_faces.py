"""Trace manually observed shutters, lit windows, stone fields and the entrance and haunch apertures."""
from pathlib import Path
import argparse,hashlib,json,runpy,sys
import numpy as np
HERE=Path(__file__).absolute().parent
sys.path.insert(0,str(HERE))
from register_court import Camera
PREFIX='Fudefang | '
GLASS='subdued glazing';FRAME='painted frame';SHUT={'charcoal shutter','recessed shutter louvre'}
PANEL={'warm carved stone edges','recessed carving field','pale pink dressed masonry'}
def make_planes(facets):
    planes={}
    for side,order in [('west',('outer','broad','inner')),('east',('inner','broad','outer'))]:
        pts=np.array(facets[side+'_facets_local_xy'])
        for name,a,b in zip(order,pts,pts[1:]):
            t=(b-a)/np.linalg.norm(b-a);planes[side+' '+name]=(a,b,t,np.array([-t[1],t[0]]))
    return planes
def judge(row,hit,planes):
    if hit is None:return False
    x,y,z=hit['point_enu_m'];q=np.array([x,y]);surface=hit['material'].removeprefix(PREFIX)
    target=row['expected_visible_surface'];face=row['visible_plane']
    if target=='door glass':return surface==GLASS and y>1.60 and z<3.38
    if target=='door wood':return surface=='dark entrance wood' and y>1.55 and z<3.46
    if target=='door passage':return surface=='shaded recess' and y>2.05
    if target=='head stone':return surface in PANEL and 1.49<y<1.90 and 3.31<z<3.88
    if target=='haunch':return surface=='warm carved stone edges' and .78<y<1.21 and z>10.0
    if target=='upper opening':return y>1.02 and z>8.8
    if target=='gallery glass':return surface==GLASS and y>1.55 and z>7.7
    if target=='gallery shutter':return surface in SHUT and y>1.60 and z>7.7
    if target=='gallery pier':return surface=='pale pink dressed masonry' and 1.56<y<1.61 and .20<x<.57 and z>8.0
    if target=='glass' and surface!=GLASS:return False
    if target=='shutter' and surface not in SHUT:return False
    if target=='historic aperture' and surface not in SHUT|{GLASS,FRAME}:return False
    if target=='carved field' and surface not in PANEL:return False
    acceptable=[face]if face in planes else [n for n in planes if n.startswith(face.split()[0])]
    for n in acceptable:
        a,b,t,norm=planes[n];axis=(q-a)@t;depth=(q-a)@norm
        if not -.042<axis<np.linalg.norm(b-a)+.042:continue
        if target=='carved field' and -.092<depth<-.011:return True
        if target!='carved field' and .10<depth<.32:return True
    return False
def inspect(path):
    project=next(p for p in HERE.parents if (p/'data/audit/postal-office-v1/independent-glb-review-helpers.py').is_file())
    scene=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene'](path)
    data=json.loads((HERE/'front-face-controls.json').read_bytes());planes=make_planes(json.loads((HERE/'front-facet-geometry.json').read_bytes()))
    offsets=sorted((round(np.hypot(x,y),4),x,y)for x in range(-4,5)for y in range(-4,5)if np.hypot(x,y)<=4)
    rows=[];cams={v:Camera(v)for v in data['photos']}
    for obs in data['points']:
        cam=cams[obs['view']];d=data['photos'][obs['view']];factor=np.array(d['native'])/d['working'];uv=obs['native_pixel'];match=None
        for radius,dx,dy in offsets:
            ray=cam.ray(np.array(uv)+factor*[dx,dy]);hit=scene.ray(cam.c,ray,45)
            if radius==0:exact=hit
            if judge(obs,hit,planes):
                match=dict(offset_working_px=[dx,dy],offset_native_px=(factor*[dx,dy]).tolist(),working_radius_px=radius,hit=hit);break
        rows.append({**obs,'first_surface':exact,'exact':judge(obs,exact,planes),'nearest':match})
    return {'mesh':path.name,'mesh_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'controls_sha256':hashlib.sha256((HERE/'front-face-controls.json').read_bytes()).hexdigest(),'registered_cameras_sha256':hashlib.sha256((HERE/'court-cameras.json').read_bytes()).hexdigest(),'total':len(rows),'exact':sum(r['exact']for r in rows),'within_four_working_pixels':sum(r['nearest']is not None for r in rows),'observations':rows}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('output',type=Path);a=p.parse_args();d=inspect(a.mesh);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+'\n');print(d['exact'],d['within_four_working_pixels'],d['total'])
    for row in d['observations']:
        if not row['nearest']:print(row['view'],row['visible_plane'],row['expected_visible_surface'],row['working_pixel'],str(row['first_surface'])[:170])
