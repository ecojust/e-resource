"""Intersect the actual metal strips at the independently observed solid-and-open point pairs."""
from pathlib import Path
import argparse,json,runpy
import numpy as np
HERE=Path(__file__).absolute().parent;SRC=HERE.parents[2]/'source/precise/jingan-liang-residence-arched-iron-window/measurements'
read=runpy.run_path(HERE.parent/'postal-office-v1/independent-glb-review-helpers.py')['load_triangles']
D=json.loads((SRC/'independent-window-apertures.json').read_bytes());C=json.loads((SRC/'window-camera.json').read_bytes())
P=np.array(C['pinhole_3x4']);E=np.array(C['eye_xyz']);W=C['nominal_outer_frame_width_m'];H=C['derived_outer_frame_height_m']
def check(path):
    tri,ids,materials,_=read(path);m=materials.index('Oxide on the window grille');t=tri[ids==m]
    # Central projection back onto the photographed front plane. Barycentric
    # point-in-triangle testing then corresponds to a sightline hitting actual metal
    # before the recessed glazing. The other model materials are purposely excluded.
    fac=(-E[1])/(t[:,:,1]-E[1]);x=E[0]+(t[:,:,0]-E[0])*fac;z=E[2]+(t[:,:,2]-E[2])*fac
    xy=np.stack([480*(x/W+.5),875*(1-z/H)],axis=-1);lo=xy.min(1);hi=xy.max(1)
    def solid(p):
        q=np.asarray(p);mask=((lo<=q).all(1))&((hi>=q).all(1));pts=xy[mask]
        if not len(pts):return False
        v=np.roll(pts,-1,axis=1)-pts;k=q-pts;cross=v[:,:,0]*k[:,:,1]-v[:,:,1]*k[:,:,0]
        return bool(((cross>=-1.e-6).all(1)|(cross<=1.e-6).all(1)).any())
    report=[]
    for sample in D['samples']:
        for role,expect in [('opening',False),('iron',True)]:
            p=np.array(sample[role+'_xy_px'],float);center=solid(p);distance=0. if center==expect else None
            radius=sample[role+'_pick_tolerance_px']
            if distance is None:
                for d in np.linspace(radius/5.,radius,5):
                    if any(solid(p+d*np.array([np.cos(ang),np.sin(ang)]))==expect for ang in np.arange(16)*np.pi/8):
                        distance=float(d);break
            report.append(dict(pair=sample['sample'],feature=sample['feature'],kind=role,rectified_xy=p.tolist(),center_is_iron=center,exact=center==expect,tolerance_px=radius,closest_matched_radius_px=distance,within_tolerance=distance is not None))
    return dict(metal_triangles=len(t),probes=report,total=len(report),exact_centres=sum(q['exact']for q in report),within_stated_tolerance=sum(q['within_tolerance']for q in report))
if __name__=='__main__':
    import sys
    f=list(map(Path,sys.argv[1:]));roles=['raw','full','lod'] if len(f)==4 else['model']
    assert len(f)==len(roles)+1
    r={k:check(f)for k,f in zip(roles,f[:-1])};f[-1].write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print({k:(v['total'],v['exact_centres'],v['within_stated_tolerance'],[(u['pair'],u['kind'])for u in v['probes']if not u['within_tolerance']])for k,v in r.items()})
