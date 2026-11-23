"""Test the edge planes of the C and E window banks against the two eastern views.

The original eight cameras stay frozen. For each bank, ground and upper windows get
independent left and right survey positions. The east camera poses have acquisition
priors. Leave-one-station tests can omit all window points from any registered frame.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

from read_eastern_end import frame
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent


def solve(main, source, east, omitted=None, parallel=False):
    initial = []
    scales = []
    variables = {}
    def add(key, values, uncertainty):
        variables[key] = slice(len(initial), len(initial)+len(values))
        initial.extend(values)
        scales.extend(np.broadcast_to(uncertainty, len(values)))

    groups = {}
    for bank in "CE":
        i = 0 if bank=="C" else 2
        for high in [False,True]:
            prm = main["parameters"]
            level = 2 if high else 1
            bounds = main["points"]
            xmin = bounds[bank+str(level)+"TL"][0]
            xmax = bounds[bank+str(level)+"TR"][0]
            y = prm["depth"][i+high]
            add((bank,high),[xmin,y,xmax,y],[.42,.64,.42,.64])
        for level in range(1,6):
            z = prm["z"+str(level)]
            oz = prm[bank.lower()+"z"][2*(level-1):2*level]
            add((bank,level,"z"),[z[0]+oz[0],z[1]+oz[1]],.42)

    az = np.radians(90-main["x_azimuth_deg"])
    enu = Rotation.from_rotvec([0,0,az]).as_matrix()
    origin = main["origin_wgs"]
    metres = np.array([111320*np.cos(np.radians(origin[1])),110860])
    cameras = {}
    known = {}
    for key,record in main["cameras"].items():
        cameras[key]=(np.asarray(record["C"]),np.asarray(record["R"]),np.asarray(record["K"]))
        known[key]={n:[v["pixel"],v["sigma"]]for n,v in source["observations"][key].items()if n[0] in "CE"}
    for key,rec in east["stations"].items():
        name="east-"+key
        s=rec["station"]
        c0=enu.T@np.r_[(np.array(s["wgs"])-origin)*metres,s["z"]]
        add(name,[*c0,s["yaw"],s["pitch"],0.],[.45,.45,.23,3.7,2.,.9])
        w,h=rec["size"];f=.5*w/np.tan(np.radians(s["hfov"]/2))
        cameras[name]=(None,None,np.array([[f,0,w/2],[0,f,h/2],[0,0,1]]))
        known[name]={n:[v,3.5]for n,v in (rec['window_points']|rec.get('independent_upper_apertures',{})).items()}
    start=np.array(initial);sigma=np.array(scales)
    def positions(p):
        for name in sorted(set(n for vals in known.values()for n in vals)):
            b=name[0];lev=int(name[1]);upper=name[-2]=='T';right=name[-1]=='R'
            xl,yl,xr,yr=p[variables[(b,lev>1)]];z=p[variables[(b,lev,'z')]][int(upper)]
            yield name,(xr if right else xl,yr if right else yl,z)
    def errors(p):
        xyz=dict(positions(p));rows={}
        for k,marks in known.items():
            if not marks:continue
            c,R,K=cameras[k]
            if c is None:
                cp=p[variables[k]];c=cp[:3];R=frame(cp[3:])@enu
            pts=np.asarray([xyz[n]for n in marks])
            q=(pts-c)@R.T@K.T
            rows[k]=q[:,:2]/q[:,2,None]-np.array([v[0]for v in marks.values()])
        return rows
    def loss(p):
        err=errors(p)
        v=[x/np.array([a[1]for a in known[k].values()])[:,None]for k,x in err.items()if k!=omitted]
        extra=[]
        if parallel:
            for b in 'CE':
                for hi in [0,1]:
                    q=p[variables[(b,hi)]];extra.append((q[1]-q[3])/.008)
        return np.concatenate([m.ravel()for m in v]+[(p-start)/sigma,np.array(extra)])
    fit=least_squares(loss,start,loss='soft_l1',max_nfev=120)
    p=fit.x
    banks={}
    for b in "CE":
        for hi in [False,True]:
            q=p[variables[(b,hi)]]
            banks[b+('2-5' if hi else '1')]={'left_xy':q[:2].tolist(),'right_xy':q[2:4].tolist(),'azimuth_to_photo_right_local_degrees':float(np.degrees(np.arctan2(q[3]-q[1],q[2]-q[0])))}
    return {'banks':banks,'stats':{k:{'median':float(np.median(np.linalg.norm(v,axis=1))),'mean':float(np.mean(np.linalg.norm(v,axis=1)))} for k,v in errors(p).items()},
            'xyz':dict(positions(p)),'east_poses':{k:p[variables[k]].tolist()for k in ['east-1512','east-2002']}}

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('output',type=Path)
    cli.add_argument('--folder',type=Path,default=HERE)
    args=cli.parse_args()
    def read(n):return json.loads((args.folder/n).read_bytes())
    data=(read('house-cameras.json'),read('house-camera-observations.json'),read('eastern-end-readings.json'))
    summary={}
    for omitted in [None,'6-1512','6-2002','86','east-1512','east-2002']:
        summary[omitted or 'all']={}
        for parallel in [True,False]:
            row=solve(*data,omitted=omitted,parallel=parallel)
            if omitted:row.pop('xyz');row.pop('east_poses')
            summary[omitted or 'all']['parallel' if parallel else 'independent_jambs']=row
    combined=summary['all']['independent_jambs']
    full=data[0];east=data[2]
    enu=Rotation.from_rotvec([0,0,np.radians(90.-full['x_azimuth_deg'])]).as_matrix()
    front=combined['banks']['E2-5']
    left=np.array(front['left_xy']);right=np.array(front['right_xy'])
    tangent=right-left;normal=np.array([tangent[1],-tangent[0],0])
    P0=np.r_[left,0.]
    out={};cast={}
    for key,rec in east['stations'].items():
        pose=np.array(combined['east_poses']['east-'+key]);w,h=rec['size']
        f=.5*w/np.tan(np.radians(rec['station']['hfov']/2.))
        K=np.array([[f,0,w/2],[0,f,h/2],[0,0,1.]])
        R=frame(pose[3:])@enu
        out[key]={'C':pose[:3].tolist(),'R':R.tolist(),'K':K.tolist(),'size':[w,h]}
        cast[key]={}
        for name,uv in rec['holdout'].items():
            ray=R.T@np.linalg.solve(K,[*uv,1]);ray/=np.linalg.norm(ray)
            cast[key][name]=(pose[:3],ray)
    roofs={}
    for name in cast['1512']:
        a,u=cast['1512'][name];b,v=cast['2002'][name]
        t=np.linalg.lstsq(np.column_stack((u,-v)),b-a,rcond=None)[0]
        p,q=a+t[0]*u,b+t[1]*v
        roofs[name]={'free_xyz':((p+q)/2).tolist(),'skew_m':float(np.linalg.norm(p-q)),'on_extended_E_face':{}}
        for key,(c,r) in [(k,z[name])for k,z in cast.items()]:
            roofs[name]['on_extended_E_face'][key]=(c+r*np.dot(P0-c,normal)/np.dot(r,normal)).tolist()
    summary['eastern_roof_and_windows']={'east_cameras':out,'geometry_on_retained_eight_station_system':combined['xyz'],'two_station_roof':roofs,
        'interpretation':'Two direct intersecting rays plus separate ray-to-extended-E-wall intersections bound the turn. E wall is estimated from windows; parapet may stand back. Tree cover obscures the lower and rear boundary. Three small window openings in the otherwise pale side wall are separately visible in the 2015 eastern view.'}
    args.output.write_text(json.dumps(summary,indent=2)+'\n')
