"""Compare unused photographic roof joints with the visible overlap faces in decoded GLBs.

Run with a photograph, the raw and decoded mesh paths, and an output directory.
Use name=path for mesh arguments, for example --mesh raw=raw.glb.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import runpy

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks

# These ranges were drawn on the source photo before projecting any model edges.
# Use only the center column, with no contribution from the six calibration columns.
SECTIONS = [(526,205,236),(532,195,235),(538,190,233),(544,185,229),(548,182,221)]

def save(path, value):
    data=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    part=path.with_suffix('.partial');part.write_bytes(data);part.replace(path)

def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def observations(photo):
    raw=np.asarray(Image.open(photo).convert('RGB'),float)
    result=[]
    for x,top,bottom in SECTIONS:
        profile=raw[top:bottom+1,x]@np.array([.35,.52,.13])
        smooth=gaussian_filter1d(profile,.52)
        pits,info=find_peaks(-smooth,prominence=7.4,distance=3)
        rows=[]
        for i,prominence in zip(pits,info['prominences']):
            a,b,c=smooth[i-1:i+2]
            offset=float(np.clip((a-c)/(2*(a-2*b+c)),-.5,.5))
            rows.append(dict(y=top+int(i)+offset,prominence=float(prominence)))
        result.append(dict(x=x,top=top,bottom=bottom,profile_luma=profile.tolist(),extrema=rows))
    return result

@contextmanager
def readable(path):
    if path.suffix!='.zst':
        yield path
        return
    import zstandard
    fd=os.memfd_create('decoded-roof-check')
    try:
        with os.fdopen(os.dup(fd),'wb') as dest,path.open('rb') as source:
            zstandard.ZstdDecompressor().copy_stream(source,dest)
        yield Path('/proc/self/fd')/str(fd)
    finally:os.close(fd)

def intervals(screen,x,top,bottom):
    lo=screen[:,:,0].min(axis=1);hi=screen[:,:,0].max(axis=1)
    rows=[]
    for triangle in screen[(lo<=x)&(x<hi)]:
        cuts=[]
        for a,b in zip(triangle,np.roll(triangle,-1,axis=0)):
            if min(a[0],b[0])<=x<max(a[0],b[0]):
                f=(x-a[0])/(b[0]-a[0]);cuts.append(float(a[1]+f*(b[1]-a[1])))
        if len(cuts)==2 and max(cuts)>=top and min(cuts)<=bottom:rows.append((min(cuts),max(cuts)))
    union=[]
    for a,b in sorted(rows):
        if union and a<=union[-1][1]+1e-4:union[-1][1]=max(union[-1][1],b)
        else:union.append([a,b])
    return union

def compare(mesh,load_triangles,first_hit,photo,cam,slope):
    with readable(mesh) as uncompressed:
        tri,ids,names,geometry=load_triangles(uncompressed)
    geometry.pop('file')
    matrix=np.array(cam['pinhole_3x4']);eye=np.array(cam['eye_xyz'])
    normal=np.array([0.,-slope,1.])/np.hypot(1.,slope)
    liptri=tri[ids==names.index('Dark upper roof joints')]
    normals=np.cross(liptri[:,1]-liptri[:,0],liptri[:,2]-liptri[:,0]);length=np.linalg.norm(normals,axis=1)
    islip=(length>1e-8)&(np.abs(normals@normal)<length*.005)
    liptri=liptri[islip]
    projected=liptri@matrix[:,:3].T+matrix[:,3];projected=projected[:,:,:2]/projected[:,:,2,None]
    allscreen=tri@matrix[:,:3].T+matrix[:,3];allscreen=allscreen[:,:,:2]/allscreen[:,:,2,None]
    colmin,colmax=allscreen[:,:,0].min(axis=1),allscreen[:,:,0].max(axis=1)
    rowmin,rowmax=allscreen[:,:,1].min(axis=1),allscreen[:,:,1].max(axis=1)
    result=[];errors=[];signed=[]
    for c in photo:
        x=c['x'];low=c['top'];hi=c['bottom']
        observed=[v['y'] for v in c['extrema']]
        visible=[];geometric=[]
        for v0,v1 in intervals(projected,x,low-1,hi+1):
            if v1-v0<.001:continue
            mid=.5*(v0+v1)
            def sample_at(y):
                ray=np.linalg.solve(matrix[:,:3],[x,y,1.])
                relevant=(colmin<=x+1e-5)&(colmax>=x-1e-5)&(rowmin<=y+1e-5)&(rowmax>=y-1e-5)
                selected=np.flatnonzero(relevant)
                if not len(selected):return None
                hit=first_hit(tri[selected],eye,ray)
                if not np.isfinite(hit[1]):return None
                index=selected[hit[0]]
                face=tri[index];n=np.cross(face[1]-face[0],face[2]-face[0])
                material=names[ids[index]]
                if material=='Dark upper roof joints' and abs(n@normal)<np.linalg.norm(n)*.005:
                    return 'overlap lip'
                return material
            probes=np.linspace(v0+.01*(v1-v0),v1-.01*(v1-v0),31)
            reads=[sample_at(y) for y in probes]
            uncovered=[float(y) for y,first in zip(probes,reads) if first=='overlap lip']
            geom=dict(top=v0,bottom=v1,mid=mid,visible_samples=len(uncovered),total_samples=len(probes))
            geometric.append(geom)
            if uncovered:
                visible.append(dict(top=min(uncovered),bottom=max(uncovered),mid=.5*(min(uncovered)+max(uncovered))))
        nearest=[];used=set()
        for y in observed:
            if not geometric:break
            k=min(range(len(geometric)),key=lambda i:abs(geometric[i]['mid']-y))
            edge=geometric[k];err=edge['mid']-y
            nearest.append(dict(photo_y=y,modeled_y=edge['mid'],residual_px=err,lip_top_y=edge['top'],lip_bottom_y=edge['bottom'],visible_fraction=edge['visible_samples']/edge['total_samples'],photo_first_hit=sample_at(y),reused=k in used));used.add(k)
            errors.append(abs(err));signed.append(err)
        # When the exact center ray crosses a vertical joint between two tiles,
        # record the nearest actual lips at fixed offsets within the same sensor pixel.
        # The original single-column residual remains in the results above.
        for match in nearest:
            if abs(match['residual_px']) <= 1.5:
                continue
            y=match['photo_y']
            flanks={}
            for offset in (-.1,.1):
                spans=intervals(projected,x+offset,y-.9,y+.9)
                flanks[str(offset)]=[dict(top=a,bottom=b) for a,b in spans]
            match['subpixel_flanking_intervals']=flanks
            match['both_flanks_cover_photo_y']=all(
                any(v['top']<=y<=v['bottom'] for v in side) for side in flanks.values())
        extra=[v for i,v in enumerate(geometric) if i not in used and observed and min(observed)-.7<=v['mid']<=max(observed)+.7]
        result.append(dict(x=x,geometric_lips=geometric,visible_lips=visible,matches=nearest,unmatched_geometric_lips_in_measured_span=extra))
    strict_matches=[m for col in result for m in col['matches'] if not m['reused'] and abs(m['residual_px'])<=1.5]
    strict_abs=[abs(m['residual_px']) for m in strict_matches]
    return dict(unique_matches_within_1_5_px=len(strict_matches),
                unique_matches_with_visible_lip=sum(m['visible_fraction']>0 for m in strict_matches),
                max_unique_residual_px=float(max(strict_abs)),mesh=geometry,overlap_triangles=len(liptri),columns=result,detected_photo_troughs=sum(len(c['extrema']) for c in photo),compared=len(errors),
                center_residual_px=dict(mean_signed=float(np.mean(signed)),median_abs=float(np.median(errors)),p95_abs=float(np.percentile(errors,95)),max_abs=float(max(errors))),
                reused_matches=sum(v['reused'] for col in result for v in col['matches']),unmatched_in_span=sum(len(c['unmatched_geometric_lips_in_measured_span']) for c in result),
                matched_with_visible_lip=sum(v['visible_fraction']>0 for col in result for v in col['matches']))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('photo',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--mesh',action='append',required=True,help='role=mesh.glb or role=decoded.glb.zst')
    parser.add_argument('--project',type=Path)
    args=parser.parse_args();here=Path(__file__).absolute().parent
    project=args.project or next(p for p in [*here.parents,Path.cwd(),Path.cwd()/'e-resource/projects/shanghai'] if (p/'tools/package_architectural_model.py').is_file())
    lib=project/'data/audit/postal-office-v1/independent-glb-review-helpers.py';helper=runpy.run_path(str(lib))
    cam=json.loads((here/'lawn-camera.json').read_bytes());train=json.loads((here/'roof-tile-courses.json').read_bytes());photo=observations(args.photo)
    assert digest(args.photo)==cam['source_sha256']==train['photo_sha256']
    traincols={s['column'] for s in train['samples']};assert not traincols & {x[0] for x in SECTIONS}
    args.output.mkdir(parents=True,exist_ok=True);f=args.output/'unseen-roof-joints-photo.json'
    save(f,dict(source_sha256=digest(args.photo),image_dimensions=[1028,686],training_columns=sorted(traincols),sampler='Single original pixel column, RGB luminance 0.35/0.52/0.13, vertical Gaussian sigma .52 px, minima prominence 7.4 and gap 3 px; parabolic refinement.',columns=photo))
    results={}
    for spec in args.mesh:
        role,path=spec.split('=',1);assert role not in results
        results[role]=compare(Path(path),helper['load_triangles'],helper['first_hit'],photo,cam,train['surface_slope'])
    out=args.output/'unseen-roof-joints-geometry.json'
    save(out,dict(photo_measurement_sha256=digest(f),camera_sha256=digest(here/'lawn-camera.json'),training_sha256=digest(here/'roof-tile-courses.json'),checker_sha256=digest(Path(__file__)),glb_reader_sha256=digest(lib),results=results))
    for role,r in results.items():print(role,r['compared'],r['center_residual_px'],r['reused_matches'],r['unmatched_in_span'],r['matched_with_visible_lip'])
if __name__=='__main__':main()
