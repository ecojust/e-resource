"""Measure unused mortar profiles against the front edges of actual 3D voussoirs."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import runpy
import sys

import numpy as np
from PIL import Image

def crossings(screen,y):
    ranges=[]
    for tri in screen[(screen[:,:,1].min(1)<=y)&(screen[:,:,1].max(1)>y)]:
        hits=[]
        for a,b in zip(tri,np.roll(tri,-1,axis=0)):
            if min(a[1],b[1])<=y<max(a[1],b[1]):
                hits.append(a[0]+(b[0]-a[0])*(y-a[1])/(b[1]-a[1]))
        if len(hits)==2:ranges.append((min(hits),max(hits)))
    union=[]
    for a,b in sorted(ranges):
        if union and a<=union[-1][1]+.0005:union[-1][1]=max(union[-1][1],b)
        else:union.append([a,b])
    return [(lo[1],hi[0]) for lo,hi in zip(union,union[1:]) if .20<hi[0]-lo[1]<2.5]

def observations(photo,info):
    img=Image.open(photo)
    factor=img.width/510
    # Read only a narrow strip at original resolution; rows are held out from all
    # calibration samples (normal offsets ±1.6, -7, -5, +5, +7).
    img=img.crop((0,int(47*factor),img.width,int(106*factor))).convert('RGB')
    rows=[]
    gx,gy=info['radial_guide_point']
    for hand in info['radial_lines_x_at_strip']:
        for x in hand[1:-1]:
            y0=69+.00157*(x-251.5)**2
            if y0>98:continue
            for dy in (-3.2,3.2):
                y=y0+dy
                predicted=x+(gx-x)*dy/(gy-y0)
                xx=np.arange(predicted-2.45,predicted+2.5,.15)
                gray=np.array([img.getpixel((round(u*factor),round(y*factor)-int(47*factor)))[1] for u in xx])
                baseline=(gray[:4].mean()+gray[-4:].mean())/2
                weights=np.maximum(0,gray-baseline-12)
                if weights.max()<25 or not weights.sum():continue
                peak=float(np.average(xx,weights=weights))
                rows.append(dict(photo_center_x=peak,y=y,contrast=float(gray.max()-baseline)))
    return rows

def stats(values):
    v=np.abs(values)
    return dict(n=len(values),median_abs_px=float(np.median(v)),p95_abs_px=float(np.percentile(v,95)),max_abs_px=float(np.max(v)))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('photo',type=Path);p.add_argument('report',type=Path)
    p.add_argument('--project',type=Path);p.add_argument('--mesh',action='append',default=[],help='role=uncompressed raw or decoded GLB')
    args=p.parse_args()
    folder=Path(__file__).absolute().parents[1]
    project=args.project or next(d for d in Path(__file__).absolute().parents if (d/'tools/package_architectural_model.py').is_file())
    sys.path[:0]=[str(folder/'source'),str(project/'tools')]
    import package_architectural_model
    from brick_surround import add_brick_surround, PALETTE, OUTER, INNER, KEY, STONE, STONE_TOP, APRON, BED
    from window_photo import P,EYE,project as pixel
    lib=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))
    info=json.loads((folder/'measurements/brick-surround.json').read_bytes())
    assert sha256(args.photo.read_bytes()).hexdigest()==info['photo_sha256']
    observations_=observations(args.photo,info)
    def examine(tri,materials,geometry):
        # An outward brick surface is on its own Y plane, independently of faces at
        # the same material and the same x,z that make the side return.
        brick=tri[np.isin(materials,OUTER)&(np.max(abs(tri[:,:,1]+.066),axis=1)<1e-5)]
        screen=pixel(brick.reshape(-1,3)).reshape(-1,3,2)
        values=[]
        for v in observations_:
            x,y=v['photo_center_x'],v['y']
            gaps=crossings(screen,y)
            if not gaps:continue
            gap=min(gaps,key=lambda s:abs(sum(s)/2-x))
            values.append(dict(**v,actual_left_x=gap[0],actual_right_x=gap[1],residual_px=float(sum(gap)/2-x)))
        allscreen=pixel(tri.reshape(-1,3)).reshape(-1,3,2)
        lo,hi=allscreen.min(1),allscreen.max(1)
        controls=[]
        for name,x,y,options in [
            ('left archivolt',148,79,OUTER),('right archivolt',368,92,OUTER),
            ('left lower fan',161,119,INNER),('right lower fan',346,120,INNER),
            ('central ribbed key',254.0,91,(KEY,)),('triangular crest',252.5,24,INNER),
            ('upper shelf',252,577,(STONE_TOP,STONE)),('stone face',331,590,(STONE,'Liang subdued ochre on sill','Liang olive-gray on sill','Liang reddish sill wear')),
            ('lower masonry',173,634,APRON),('next brick course',266,648,APRON)]:
            subset=np.flatnonzero(np.all(lo<=[x,y],axis=1)&np.all(hi>=[x,y],axis=1))
            ray=np.linalg.solve(P[:,:3],[x,y,1.]);hit=lib['first_hit'](tri[subset],EYE,ray)
            actual=str(materials[subset[hit[0]]]) if np.isfinite(hit[1]) else None
            controls.append(dict(name=name,pixel=[x,y],expected=list(options),actual=actual,matched=actual in options))
        return dict(geometry=geometry,front_brick_triangles=len(brick),matches=values,residual=stats([r['residual_px'] for r in values]),surface_checks=controls)
    results={}
    if not args.mesh:
        sys.path.insert(0,str(project/'source/precise/huangpu-somekh-building-street-corner/source'))
        from aggregate_mesh import AggregateBuilder
        for lod in (False,True):
            builder=AggregateBuilder(PALETTE);add_brick_surround(builder,lod)
            tri=[];m=[]
            for group in builder.parts:
                t=np.asarray(group['vertices'])[np.asarray(group['triangles'])]
                tri.extend(t);m.extend([group['material']]*len(t))
            role='helper_lod' if lod else 'helper_full'
            results[role]=examine(np.asarray(tri),np.asarray(m),dict(groups=len(builder.parts),triangles=len(tri)))
    for arg in args.mesh:
        role,filename=arg.split('=',1)
        tri,ids,names,g=lib['load_triangles'](Path(filename))
        g.pop('file',None);results[role]=examine(tri,np.asarray(names)[ids],g)
    data=dict(photo_sha256=info['photo_sha256'],checker_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),camera_sha256=sha256((folder/'measurements/window-camera.json').read_bytes()).hexdigest(),measurements_sha256=sha256((folder/'measurements/brick-surround.json').read_bytes()).hexdigest(),helper_sha256=sha256((folder/'source/brick_surround.py').read_bytes()).hexdigest(),sample_rows=len(observations_),results=results)
    args.report.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    for role,r in results.items():print(role,r['residual'],[(v['name'],v['actual']) for v in r['surface_checks'] if not v['matched']])
if __name__=='__main__':main()
