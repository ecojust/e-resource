"""Fit three court photographs to the six repeated window axes in the main plane."""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

HERE=Path(__file__).absolute().parent

def rotation(yaw,pitch,roll):
    cy,sy=np.cos(yaw),np.sin(yaw);cp,sp=np.cos(pitch),np.sin(pitch);cr,sr=np.cos(roll),np.sin(roll)
    right=np.array([cy,-sy,0]);down=np.array([sy*sp,cy*sp,-cp]);forward=np.array([sy*cp,cy*cp,sp])
    return np.array([cr*right+sr*down,-sr*right+cr*down,forward])

def make_k(data, f):
    w,h=data['size']
    return np.array([[f,0,w/2],[0,f,h/2],[0,0,1.]])

def line_errors(camera,d):
    k,r,c=camera
    result=[]
    for axis,dim in [('vp_x',0),('vp_z',2)]:
        vp=k@r[:,dim]
        for s,e in d[axis]:
            line=np.cross([*s,1],[*e,1]);det=np.linalg.norm(line[:2])
            result.append((np.dot(line,vp)/det)/(np.linalg.norm(vp[:2]-np.array(s)*vp[2])/np.linalg.norm(np.subtract(s,e))))
    return result

def proj(cam,xyz):
    k,r,c=cam
    p=k@r@(xyz-c);return p[:2]/p[2]

def plane(cam,uv):
    k,r,c=cam
    v=r.T@np.linalg.solve(k,[*uv,1]);return c+v*(-c[1]/v[1])

def measure(width,facade_width):
    src=json.loads((HERE/'court-photograph-observations.json').read_bytes())
    labels=list(src)
    starts=[]
    samples=[]
    camera_starts=[]
    for i,(name,d) in enumerate(src.items()):
        f0=d['f35']*d['size'][0]/36
        angles=least_squares(lambda v:line_errors((make_k(d,f0),rotation(*v),np.zeros(3)),d),
                             np.radians([45,10,0]),loss='huber',f_scale=2).x
        k=make_k(d,f0);r=rotation(*angles)
        origin_ray=r.T@np.linalg.solve(k,[*d['origin_uv'],1])
        c=-origin_ray*14/origin_ray[1]
        cam=k,r,c
        left=d['middle'][0][:2];right=d['middle'][-1][:2]
        span=plane(cam,right)[0]-plane(cam,left)[0]
        c*=width/span
        starts.extend([*angles,*c,0.]);camera_starts.append((k,r,c))
        for row in ('upper','middle'):
            for j,marks in enumerate(d[row]):
                for side,key in enumerate(('L','R')):
                    u,v=marks[2*side:2*side+2]
                    if u is not None:
                        samples.append((i,j,side,0 if row=='upper' else 2,np.array([u,v])))
                    if row=='upper' and u is not None:
                        samples.append((i,j,side,1,np.array([u,marks[4+side]])))
    first=src[labels[0]]
    x0=[plane(camera_starts[0],mark[:2])[0]for mark in first['middle']]
    # Fix the X origin to the third (door) axis below its middle sash; temporary width between outer left jambs before the cadastral end-to-end scaling.
    loc=np.asarray(x0)
    loc-=loc[2]+.47
    span=loc[-1]-loc[0];loc*=width/span
    base=21;starts.extend(loc[1:-1]);starts.extend([.95]*6);starts.extend([9.7,7.9,6.3,0.])
    # Shared front edges and independent projections of the two balustrades.
    # Only the far/front face is used in these constraints. The window wall has Y=0.
    rail_start=base+14
    for side in ('left','right'):
        projected=[]
        for j,uv in enumerate(first['balcony'][side]):
            k,r,c=camera_starts[0];v=r.T@np.linalg.solve(k,[*uv,1])
            projected.append(c+v*((-1.1-c[1])/v[1]))
        starts.extend([np.mean([projected[j][0] for j in (0,3)]),np.mean([projected[j][0]for j in(1,2)]),-1.1,
                       np.mean([projected[j][2]for j in(0,1)]),np.mean([projected[j][2]for j in(2,3)])])
    def unpack(t):
        cams=[]
        for i,(name,d)in enumerate(src.items()):
            v=t[7*i:7*(i+1)];k=make_k(d,d['f35']*d['size'][0]/36*np.exp(v[-1]))
            cams.append((k,rotation(*v[:3]),v[3:6]))
        # Bounds are anchored at the first left jamb; the third sash center and the datum use two independent constraints.
        x=np.r_[loc[0],t[base:base+4],loc[0]+width];w=t[base+4:base+10];heights=t[base+10:base+13]
        shift=x[2]+w[2]/2
        return cams,x-shift,w,heights
    def loss(t,report=False):
        cams,x,widths,z=unpack(t);per={n:[] for n in labels};out=[]
        for i,j,side,level,target in samples:
            p=np.array([x[j]+widths[j]*side,0,z[level]])
            delta=proj(cams[i],p)-target
            per[labels[i]].append(np.linalg.norm(delta))
            out.extend(delta/2)
        for i,(name,d) in enumerate(src.items()):
            out.extend(np.asarray(line_errors(cams[i],d))/1.5)
            out.append(t[7*i+6]/.035)
        for side_id,side in enumerate(('left','right')):
            a,b,y,h,l=t[rail_start+5*side_id:rail_start+5*(side_id+1)]
            corners=[[a,y,h],[b,y,h],[b,y,l],[a,y,l]]
            for i,(name,d)in enumerate(src.items()):
                for v,uv in zip(corners,d['balcony'][side]):
                    out.extend((proj(cams[i],v)-uv)/2.5)
        # Only the first distant view marks the raised porch landing at street-facing wall plane.
        # Select a Z datum at the court pavement by the measured lower riser in that view.
        datum=proj(cams[0],np.zeros(3))-first['origin_uv']
        out.append(datum[1]/1.2)
        out.append((cams[0][2][2]-1.56)/1.0)
        return per if report else out
    opt=least_squares(loss,starts,loss='soft_l1',max_nfev=85,xtol=1e-8)
    cams,x,widths,z=unpack(opt.x)
    spans={}
    outline={}
    for (name,d),cam in zip(src.items(),cams):
        ends=[plane(cam,uv)[0] for uv in d['wall_ends']]
        outline[name]=ends
        spans[name]=ends[1]-ends[0]
    scale=facade_width/float(np.median(list(spans.values())))
    cams=[(k,r,c*scale) for k,r,c in cams]
    x=x*scale;widths=widths*scale;z=z*scale
    rails={}
    for i,key in enumerate(('left','right')):
        vals=opt.x[rail_start+5*i:rail_start+5*i+5]*scale
        rails[key]=dict(zip(['x0','x1','y','top_z','base_z'],map(float,vals)))
    return dict(views={name:dict(K=k.tolist(),R=r.tolist(),C=c.tolist(),size=src[name]['size'])
                       for name,(k,r,c)in zip(labels,cams)},station_errors_px=loss(opt.x,True),
                scale='Scaled to the median end-to-end span on the 22.94 m cadastral garden-facing edge. The six front windows determine the plane; its third sash is above the entrance axis.',
                jamb_span_m=width*scale,gis_main_court_edge_m=facade_width,balustrades=rails,
                outline_by_view_m={n:[float(v*scale)for v in xs]for n,xs in outline.items()},
                edge_span_by_view_m={n:v*scale for n,v in spans.items()},
                axis_left_jambs_m=x.tolist(),opening_widths_m=widths.tolist(),window_heights_m=z.tolist(),
                approximate_camera_heights_m={n:float(c[2]) for n,(_,_,c)in zip(labels,cams)})

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--span',type=float,default=14.0)
    cli.add_argument('--out',type=Path,default=HERE/'court-cameras.json');args=cli.parse_args()
    result=measure(args.span,22.94);args.out.write_text(json.dumps(result,indent=2)+'\n')
    print([(n,np.median(v),max(v)) for n,v in result['station_errors_px'].items()],result['axis_left_jambs_m'],result['approximate_camera_heights_m'])
