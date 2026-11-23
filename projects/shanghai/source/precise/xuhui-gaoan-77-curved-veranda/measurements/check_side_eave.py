"""Cast the independently marked side-photo pixels against the delivered GLB."""
from pathlib import Path
import argparse,hashlib,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene

def read(p):return json.loads(p.read_bytes())
def check(mesh,layout,component=False):
    info=read(HERE/'west-eave-photo-control.json');samples=read(HERE/'west-eave-visible-pixels.json')
    geo=SerialScene(mesh);reports={}
    frame=layout['side_frame'];along=np.asarray(frame['along'],float)
    along/=np.linalg.norm(along);out=np.array([along[1],-along[0]])
    cfg=layout['side_eave']
    transform=np.asarray(layout.get('component_to_model',np.eye(4)),float)
    assert transform.shape==(4,4) and np.allclose(transform[3],[0,0,0,1])
    def world(q):
        s,depth,z=q
        xy=np.asarray(frame['origin'])+along*(cfg['first_s']+s*(cfg['last_s']-cfg['first_s'])/6.882341274275515)+out*depth
        return (transform@np.r_[xy,cfg['seat_z']+z,1.])[:3]
    for name,spec in samples['stations'].items():
        cam=info['cameras'][name];width,height=cam['native_size'];h=np.asarray(cam['plane_to_pixel'])
        focal=spec['assumed_focal_px']
        K=np.array([[focal,0,width/2],[0,focal,height/2],[0,0,1.]])
        inv=np.linalg.inv(K);u=inv@h[:,0];z=inv@h[:,1];normal=np.cross(u,z)
        normal*=np.sqrt(np.linalg.norm(u)*np.linalg.norm(z))/np.linalg.norm(normal)
        P=np.column_stack([h[:,0],K@normal,h[:,1],h[:,2]])
        eye=-np.linalg.solve(P[:,:3],P[:,3])
        if eye[1]<0:
            P[:,1]*=-1
            eye=-np.linalg.solve(P[:,:3],P[:,3])
        origin=world(eye)
        hits=[]
        for label,mat,px,py in spec['marks']:
            ray=np.linalg.solve(P[:,:3],np.array([px,py,1.]))
            direction=world(eye+ray)-origin
            hit=geo.ray(origin,direction/np.linalg.norm(direction),180.)
            got=hit['material']if hit else None
            hits.append(dict(name=label,pixel=[px,py],expected='Gaoan 77 | '+mat,hit=got,match=got=='Gaoan 77 | '+mat,xyz=hit['point_enu_m']if hit else None))
        reports[name]={'tests':len(hits),'matches':sum(r['match']for r in hits),'hits':hits}
    return {'mesh_sha256':hashlib.sha256(mesh.read_bytes()).hexdigest(),'side_frame':frame,'placement':cfg,'component_to_model':transform.tolist(),'photos':reports}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mesh',type=Path);parser.add_argument('layout',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();report=check(args.mesh,read(args.layout));args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:(v['matches'],v['tests'])for k,v in report['photos'].items()})
