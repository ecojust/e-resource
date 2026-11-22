"""Check exposed steel and glass glTF surfaces on the three west gable openings."""
import argparse
import json
from pathlib import Path

import numpy as np
from check_warehouse_windows import BLUE, FIXED, SASH, first_hit, load_triangles

HERE = Path(__file__).resolve().parent


def frame(layout):
    street, back = np.asarray(layout['west_return'])
    dx,dy = (street-back)/np.linalg.norm(street-back)
    return back,np.array([[dx,dy],[-dy,dx]])


def gable_coordinates(tri, layout):
    back,basis=frame(layout)
    local=tri.copy()
    local[:,:,:2]=(tri[:,:,:2]-back)@basis.T
    return local


def probe(opening,length,far):
    left,right=length-opening['d1'],length-opening['d0']
    base,top=opening['z0'],opening['z1']
    w,h=right-left,top-base
    fixed=min(.051,w*.055,h*.035)
    yield 'jamb',left+fixed*.45,base+.45*h,0,FIXED
    yield 'head',left+.32*w,top-fixed*.45,0,FIXED
    margin = fixed+.0015
    xmin,xmax,zmin,zmax=left+margin,right-margin,base+margin,top-margin
    levels,lights=([0,.26,.76,1],[0,1]) if opening['family']=='west-narrow' else ([0,1],[0,.16,.57,1])
    for a,b in zip(levels,levels[1:]):
        z=zmin+(a+b)/2*(zmax-zmin)
        for c,d in zip(lights,lights[1:]):
            yield 'independent glass light',xmin+(c+d)/2*(xmax-xmin),z,.061 if far else .036,BLUE
        for c in lights[1:-1]:
            yield 'stile',xmin+c*(xmax-xmin),z,.010,SASH
    for a in levels[1:-1]:
        yield 'transom',xmin+.55*(xmax-xmin),zmin+a*(zmax-zmin),.010,SASH


def photo_comparisons(survey):
    result=[]
    for source in survey['sources']:
        plane=np.array(source['estimated_gable_homography'])
        aperture_residuals=[]
        for opening in survey['openings']:
            corners=[[opening[d],opening[z],1] for d,z in
                     [('d1','z1'),('d0','z1'),('d1','z0'),('d0','z0')]]
            mapped=np.array(corners)@plane.T
            pixels=mapped[:,:2]/mapped[:,2:]
            observed=np.array(source['west_aperture_pixels'][opening['key']])
            delta=pixels-observed
            aperture_residuals.append(dict(opening=opening['key'], observed_pixels=observed.tolist(),
                projected_pixels=pixels.round(3).tolist(),residual_px=np.linalg.norm(delta,axis=1).round(3).tolist()))
        result.append(dict(source=source['id'],homography_controls_median_p90_px=source['front_control_residual_median_p90_px'],
                           gable_windows=aperture_residuals))
    return result


def read_mesh(path,layout,survey):
    triangles,materials,names,asset=load_triangles(path)
    tri=gable_coordinates(triangles,layout)
    low,high=tri.min(1),tri.max(1)
    street,back=np.asarray(layout['west_return'])
    length=np.linalg.norm(street-back)
    records=[]
    for opening in survey['openings']:
        for role,s,z,offset,expected in probe(opening,length,'lod' in path.name):
            keep=np.where((low[:,0]<=s)&(high[:,0]>=s)&(low[:,2]<=z)&(high[:,2]>=z))[0]
            idx,dist,hit=first_hit(tri[keep],[s,-1,z],[0,1,0])
            if not np.isfinite(dist):
                raise ValueError((path.name,opening['key'],role,'missed all physical materials'))
            tid=keep[idx]
            n=np.cross(tri[tid,1]-tri[tid,0],tri[tid,2]-tri[tid,0])
            direction=float(n[1]/np.linalg.norm(n))
            error=float(hit[1]-(opening['recess']+offset))
            material=names[materials[tid]]
            records.append(dict(opening=opening['key'],target=role,d_m=round(length-s,4),z_m=round(z,4),
                material=material,expected_material=expected,inward_normal_component=round(direction,5),
                depth_error_m=round(error,6),passed=bool(material==expected and abs(error)<.006 and direction<-.99)))
    return dict(asset=asset,rays=len(records),passed=sum(r['passed'] for r in records),records=records)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('output',type=Path)
    parser.add_argument('models',type=Path,nargs='+')
    args=parser.parse_args()
    layout=json.loads((HERE/'riverfront-layout.json').read_text())
    survey=json.loads((HERE/'west-return-windows.json').read_text())
    checks=[read_mesh(model,layout,survey) for model in args.models]
    args.output.mkdir(exist_ok=True,parents=True)
    report={'openings':survey['openings'],'source_comparisons':photo_comparisons(survey),
        'meshes':checks}
    (args.output/'west-return-window-check.json').write_text(json.dumps(report,indent=2)+'\n')
    print([(c['asset']['file'],c['rays'],c['passed'])for c in checks])
    assert all(c['rays']==c['passed'] for c in checks)
